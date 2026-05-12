import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.run_config import RunConfig


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


def _resolve_day18_path() -> Path:
    configured = os.getenv("DAY18_RAG_PATH")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        [
            PROJECT_DIR.parent / "day18-rag",
            PROJECT_DIR / "day18-rag",
            Path.cwd().parent / "day18-rag",
        ]
    )

    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if (resolved / "src" / "pipeline.py").exists():
            return resolved

    checked = "\n".join(f"- {c}" for c in candidates)
    raise FileNotFoundError(
        "Không tìm thấy Day 18 RAG pipeline. Set DAY18_RAG_PATH hoặc đặt folder day18-rag cạnh repo.\n"
        f"Đã kiểm tra:\n{checked}"
    )


def _parse_threshold(values: list[str]) -> dict[str, float]:
    thresholds: dict[str, float] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"Threshold không hợp lệ: {item}. Dùng dạng metric=value")
        name, value = item.split("=", 1)
        thresholds[name.strip()] = float(value)
    return thresholds


def _load_testset() -> pd.DataFrame:
    path = SCRIPT_DIR / "testset_v1.csv"
    if not path.exists():
        raise FileNotFoundError("phase-a/testset_v1.csv không tồn tại. Hãy chạy generate_testset.py trước.")
    return pd.read_csv(path)


def _write_gate_report(summary: dict[str, float], thresholds: dict[str, float]) -> bool:
    failed = [
        metric
        for metric, target in thresholds.items()
        if float(summary.get(metric, 0.0)) < target
    ]
    report = {
        "scores": summary,
        "thresholds": thresholds,
        "passed": not failed,
        "failed_metrics": failed,
    }
    with (SCRIPT_DIR / "ragas_gate_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return not failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--threshold",
        action="append",
        default=[],
        help="Metric gate dạng metric=value, ví dụ: --threshold faithfulness=0.85",
    )
    args = parser.parse_args(argv)
    thresholds = _parse_threshold(args.threshold)

    day18_path = _resolve_day18_path()
    sys.path.insert(0, str(day18_path))

    from src.pipeline import build_pipeline, run_query
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    print("Loading testset...")
    testset = _load_testset()

    print("Building RAG pipeline...")
    search, reranker = build_pipeline()

    print("Running queries through the pipeline...")
    rows = []
    for i, row in testset.iterrows():
        question = row["question"]
        ground_truth = row["ground_truth"]
        print(f"  [{i + 1}/{len(testset)}] {question[:70]}...")

        answer, contexts = run_query(question, search, reranker)
        rows.append(
            {
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
            }
        )

    dataset = Dataset.from_list(rows)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    run_config = RunConfig(max_workers=1, max_retries=15, max_wait=90)

    print("Evaluating with RAGAS metrics...")
    results = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
        run_config=run_config,
    )

    results_df = results.to_pandas()
    results_df.to_csv(SCRIPT_DIR / "ragas_results.csv", index=False)

    summary = {
        "faithfulness": float(results.get("faithfulness", 0)),
        "answer_relevancy": float(results.get("answer_relevancy", 0)),
        "context_precision": float(results.get("context_precision", 0)),
        "context_recall": float(results.get("context_recall", 0)),
    }
    with (SCRIPT_DIR / "ragas_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    gate_passed = _write_gate_report(summary, thresholds) if thresholds else True

    print("\nEvaluation complete.")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if thresholds:
        print(f"Gate passed: {gate_passed}")
    return 0 if gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
