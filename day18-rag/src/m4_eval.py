"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    from ragas import evaluate
    from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from datasets import Dataset
    import pandas as pd
    
    dataset = Dataset.from_dict({
        "user_input": questions,
        "response": answers,
        "retrieved_contexts": contexts,
        "reference": ground_truths,
    })
    
    llm = LangchainLLMWrapper(ChatOpenAI(
        model=os.getenv("RAGAS_LLM_MODEL", "gpt-4o-mini"),
        temperature=0
    ))
    embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(
        model=os.getenv("RAGAS_EMBEDDING_MODEL", "text-embedding-3-small")
    ))
    metrics = [
        Faithfulness(),
        AnswerRelevancy(),
        ContextPrecision(),
        ContextRecall(),
    ]
    
    result = evaluate(
        dataset,
        metrics=metrics,
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=False
    )
    df = result.to_pandas()
    
    # Fill missing values (NaN) with 0.0 to prevent processing/JSON saving errors
    df = df.fillna(0.0)
    
    per_question = []
    for idx, (_, row) in enumerate(df.iterrows()):
        per_question.append(
            EvalResult(
                question=questions[idx],
                answer=answers[idx],
                contexts=contexts[idx],
                ground_truth=ground_truths[idx],
                faithfulness=float(row.get("faithfulness", 0.0) or 0.0),
                answer_relevancy=float(row.get("answer_relevancy", 0.0) or 0.0),
                context_precision=float(row.get("context_precision", 0.0) or 0.0),
                context_recall=float(row.get("context_recall", 0.0) or 0.0)
            )
        )

    def mean_metric(name: str) -> float:
        values = [getattr(item, name) for item in per_question]
        return float(sum(values) / len(values)) if values else 0.0
        
    return {
        "faithfulness": mean_metric("faithfulness"),
        "answer_relevancy": mean_metric("answer_relevancy"),
        "context_precision": mean_metric("context_precision"),
        "context_recall": mean_metric("context_recall"),
        "per_question": per_question
    }


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    # 1. Calculate average score across 4 metrics
    scored_results = []
    for res in eval_results:
        avg_score = (res.faithfulness + res.answer_relevancy + res.context_precision + res.context_recall) / 4.0
        scored_results.append((avg_score, res))
        
    # 2. Sort ascending by avg_score and take the bottom_n
    scored_results.sort(key=lambda x: x[0])
    worst_results = scored_results[:bottom_n]
    
    failures = []
    for avg_score, res in worst_results:
        metrics = {
            "faithfulness": res.faithfulness,
            "answer_relevancy": res.answer_relevancy,
            "context_precision": res.context_precision,
            "context_recall": res.context_recall
        }
        
        # Identify the worst metric by absolute lowest score
        worst_metric = min(metrics, key=metrics.get)
        worst_score = metrics[worst_metric]
        
        # 3. Diagnostic mapping based on predefined rules
        diagnosis = "Needs general review (scores are acceptable)"
        suggested_fix = "N/A"
        
        if worst_metric == "faithfulness" and worst_score < 0.85:
            diagnosis = "LLM hallucinating"
            suggested_fix = "Tighten prompt, lower temperature"
        elif worst_metric == "context_recall" and worst_score < 0.75:
            diagnosis = "Missing relevant chunks"
            suggested_fix = "Improve chunking or add BM25"
        elif worst_metric == "context_precision" and worst_score < 0.75:
            diagnosis = "Too many irrelevant chunks"
            suggested_fix = "Add reranking or metadata filter"
        elif worst_metric == "answer_relevancy" and worst_score < 0.80:
            diagnosis = "Answer doesn't match question"
            suggested_fix = "Improve prompt template"
            
        failures.append({
            "question": res.question,
            "worst_metric": worst_metric,
            "score": worst_score,
            "diagnosis": diagnosis,
            "suggested_fix": suggested_fix
        })

    return failures


def save_report(results: dict, failures: list[dict], path: str = "ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
