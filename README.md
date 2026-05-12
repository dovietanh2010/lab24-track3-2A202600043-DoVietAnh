# Lab 24 - Full Evaluation & Guardrail System

**Họ tên:** Đỗ Việt Anh  
**MSSV:** 2A202600043  
**Track:** 3

## Overview

Bài lab mở rộng pipeline RAG từ Day 18 bằng 4 phần chính:

1. **Phase A - RAGAS Evaluation:** sinh test set 50 câu, chạy 4 metric, phân tích lỗi.
2. **Phase B - LLM-as-Judge:** pairwise comparison, absolute scoring, human calibration bằng Cohen's Kappa.
3. **Phase C - Guardrails Stack:** input PII redaction, topic scope validator, adversarial defense, output guard, latency benchmark.
4. **Phase D - Blueprint:** SLO, architecture diagram, alert playbook, cost analysis.

## Folder Structure

```text
lab24-eval-guardrails-DoVietAnh/
|-- .github/workflows/eval-gate.yml
|-- .env.example
|-- requirements.txt
|-- prompts.md
|-- README.md
|
|-- phase-a/
|   |-- generate_testset.py
|   |-- testset_v1.csv
|   |-- testset_review_notes.md
|   |-- run_eval.py
|   |-- ragas_results.csv
|   |-- ragas_summary.json
|   |-- ragas_gate_report.json
|   |-- failure_analysis.md
|
|-- phase-b/
|   |-- pairwise_judge.py
|   |-- pairwise_results.csv
|   |-- pairwise_summary.json
|   |-- absolute_judge.py
|   |-- absolute_scores.csv
|   |-- human_labels.csv
|   |-- kappa_analysis.ipynb
|   |-- kappa_summary.json
|   |-- judge_bias_report.md
|
|-- phase-c/
|   |-- input_guard.py
|   |-- output_guard.py
|   |-- full_pipeline.py
|   |-- pii_test_results.csv
|   |-- adversarial_test_results.csv
|   |-- guardrail_report.md
|   |-- latency_benchmark.csv
|
|-- phase-d/
    |-- blueprint.md
```

## Results Summary

### Phase A - RAGAS

| Metric | Score | Target | Status |
|---|---:|---:|---|
| Faithfulness | 0.827 | 0.850 | Chưa đạt |
| Answer Relevancy | 0.821 | 0.800 | Đạt |
| Context Precision | 0.759 | 0.700 | Đạt |
| Context Recall | 0.791 | 0.750 | Đạt |

CI gate hiện tại dùng ngưỡng **Min OK** nên pass; production SLO target `faithfulness >= 0.85` vẫn chưa đạt vì faithfulness hiện tại là `0.827`. Chi tiết nằm ở `phase-a/ragas_gate_report.json` và `phase-a/failure_analysis.md`.

### Phase B - LLM-as-Judge

| Output | Kết quả |
|---|---|
| Pairwise questions | 30 |
| Production/B wins | 22/30 |
| Baseline/A wins | 7/30 |
| Ties | 1/30 |
| Absolute average score | 4.33/5 |
| Cohen's Kappa | 0.615 |

Kappa `0.615` tương ứng mức agreement khá tốt để dùng cho monitoring, nhưng vẫn cần kiểm tra định kỳ vì tập human label chỉ có 10 mẫu.

### Phase C - Guardrails

| Metric | Result |
|---|---:|
| PII test cases | 10 |
| PII detection on positive cases | 8/8 |
| Adversarial detection | 18/20 |
| Latency benchmark requests | 100 |
| Total latency P50 | ~1180ms |
| Total latency P95 | ~1560ms |

`input_guard.py` có fallback regex/local heuristic để vẫn chạy được khi máy chưa có spaCy model cho Presidio. Nếu có spaCy model, Presidio NER sẽ được dùng thêm.

### Phase D - Blueprint

Blueprint gồm SLO, sơ đồ kiến trúc Mermaid, 3 alert playbooks và phân tích chi phí cho 100K queries/tháng.

## How To Run

```bash
pip install -r requirements.txt
```

Cấu hình `.env` từ `.env.example`:

```bash
OPENAI_API_KEY=...
GROQ_API_KEY=...
```

Nếu Day 18 RAG pipeline nằm ngoài repo mặc định, set thêm:

```bash
DAY18_RAG_PATH=../day18-rag
```

Chạy từng phase:

```bash
python phase-a/generate_testset.py
python phase-a/run_eval.py --threshold faithfulness=0.75 --threshold answer_relevancy=0.70 --threshold context_precision=0.60 --threshold context_recall=0.65

python phase-b/pairwise_judge.py
python phase-b/absolute_judge.py

python phase-c/input_guard.py
python phase-c/output_guard.py
python phase-c/full_pipeline.py --sample
python phase-c/full_pipeline.py --benchmark --requests 100
```

## Notes

- Các output CSV/JSON hiện tại đã được giữ trong repo để reviewer có thể kiểm tra mà không cần gọi API lại.
- `ragas_gate_report.json` phản ánh đúng trạng thái CI gate hiện tại: pass theo ngưỡng Min OK; SLO target vẫn được ghi riêng trong blueprint.
- `pairwise_judge.py` đã lưu đủ `run1_winner`, `run2_winner` và `winner_after_swap` cho các lần chạy sau; file cũ đã được tổng hợp lại trong `pairwise_summary.json`.
