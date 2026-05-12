import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

load_dotenv(PROJECT_DIR / ".env")


JUDGE_PROMPT = PromptTemplate.from_template(
    """
You are an impartial evaluator. Compare two answers to the same question.

Question: {question}
Answer A: {answer_a}
Answer B: {answer_b}

Rate based on:
- Factual accuracy
- Relevance to question
- Conciseness

Important: judge content quality, not answer length or position.

Output JSON ONLY:
{{"winner": "A" or "B" or "tie", "reason": "..."}}
"""
)


def parse_judge_output(text: str) -> dict:
    try:
        cleaned = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
        if parsed.get("winner") not in {"A", "B", "tie"}:
            parsed["winner"] = "tie"
        return parsed
    except json.JSONDecodeError:
        return {"winner": "tie", "reason": "Parse error"}


def _judge_once(question: str, answer_a: str, answer_b: str, judge_llm) -> dict:
    prompt = JUDGE_PROMPT.format(question=question, answer_a=answer_a, answer_b=answer_b)
    out = judge_llm.invoke(prompt)
    return parse_judge_output(out.content)


def pairwise_judge_with_swap(question: str, baseline: str, production: str, judge_llm) -> dict:
    """Run pairwise judge twice and map both answers back to original labels.

    Original labels:
    A = baseline
    B = production
    """
    first = _judge_once(question, baseline, production, judge_llm)
    run1_winner = first.get("winner", "tie")

    second = _judge_once(question, production, baseline, judge_llm)
    raw_second = second.get("winner", "tie")
    if raw_second == "A":
        run2_winner = "B"
    elif raw_second == "B":
        run2_winner = "A"
    else:
        run2_winner = "tie"

    winner_after_swap = run1_winner if run1_winner == run2_winner else "tie"
    reason = first.get("reason", "")
    if winner_after_swap == "tie" and run1_winner != run2_winner:
        reason = f"Disagreement after swap: run1={run1_winner}, run2={run2_winner}"

    return {
        "run1_winner": run1_winner,
        "run2_raw_position_winner": raw_second,
        "run2_winner": run2_winner,
        "winner_after_swap": winner_after_swap,
        "reason": reason,
    }


def _load_eval_rows() -> pd.DataFrame:
    path = PROJECT_DIR / "phase-a" / "ragas_results.csv"
    if not path.exists():
        raise FileNotFoundError("Không tìm thấy phase-a/ragas_results.csv. Hãy chạy Phase A trước.")
    df = pd.read_csv(path)
    required = {"question", "answer", "baseline_answer"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "ragas_results.csv thiếu cột cần cho pairwise judge: "
            + ", ".join(sorted(missing))
            + ". Không dùng placeholder baseline vì sẽ làm sai calibration."
        )
    return df.head(30)


def _write_summary(results_df: pd.DataFrame) -> None:
    counts = results_df["winner_after_swap"].value_counts().to_dict()
    total = int(len(results_df))
    summary = {
        "total": total,
        "winner_counts": {
            "A": int(counts.get("A", 0)),
            "B": int(counts.get("B", 0)),
            "tie": int(counts.get("tie", 0)),
        },
        "production_win_rate": float(counts.get("B", 0) / total) if total else 0.0,
        "baseline_win_rate": float(counts.get("A", 0) / total) if total else 0.0,
        "tie_rate": float(counts.get("tie", 0) / total) if total else 0.0,
    }
    with (SCRIPT_DIR / "pairwise_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def main() -> None:
    df = _load_eval_rows()
    judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    rows = []
    print("Running pairwise judge...")
    for i, row in df.iterrows():
        print(f"  Evaluating [{i + 1}/{len(df)}]")
        judged = pairwise_judge_with_swap(
            question=row["question"],
            baseline=row["baseline_answer"],
            production=row["answer"],
            judge_llm=judge_llm,
        )
        rows.append(
            {
                "question": row["question"],
                "answer_a": row["baseline_answer"],
                "answer_b": row["answer"],
                **judged,
            }
        )

    results_df = pd.DataFrame(rows)
    results_df.to_csv(SCRIPT_DIR / "pairwise_results.csv", index=False)
    _write_summary(results_df)
    print("Saved pairwise_results.csv and pairwise_summary.json")


if __name__ == "__main__":
    main()
