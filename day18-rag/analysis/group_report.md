# Group Report — Lab 18: Production RAG

**Nhóm:** B3
**Ngày:** 2026-05-05

## Thành viên & Phân công

| Tên | MSSV | Module | Hoàn thành | Tests pass |
|-----|------|--------|-----------|-----------|
| Đỗ Xuân Bằng | 2A202600044 | M1: Chunking | ☑ | 13/13 |
| Đỗ Việt Anh | 2A202600043 | M2: Hybrid Search | ☑ | 5/5 |
| Trần Ngô Hồng Hà | 2A202600428 | M3: Reranking | ☑ | 5/5 |
| Lê Thành Long | 2A202600105 | M4: RAGAS Evaluation | ☑ | 32/37 (toàn pipeline) |
| Trương Anh Long | 2A202600327 | M5: Enrichment (TODO 1, 2, 3 — summarize / HyQA / contextual prepend) | ☑ | 10/10 |
| Lã Thị Linh | 2A202600089 | M5: Enrichment (TODO 4, 5 — extract_metadata / enrich_chunks pipeline) | ☑ | tích hợp pass cùng M5 |

## Kết quả RAGAS

> Số liệu thực tế từ 3 lần chạy với cùng 1 test set 20 câu hỏi tiếng Việt, RAGAS judge `gpt-4o-mini` + embeddings `text-embedding-3-small`. File output:
> - Naive: [reports/naive_baseline_report.json](../reports/naive_baseline_report.json) (paragraph chunking + dense-only top-3, answer = `contexts[0]` raw không qua LLM)
> - Production (KHÔNG M5): [reports/ragas_report_no_m5.json](../reports/ragas_report_no_m5.json) (M1 hierarchical + M2 hybrid BM25+dense BGE-M3+RRF + M3 cross-encoder rerank top-3, raw chunks)
> - Production (CÓ M5): [reports/ragas_report.json](../reports/ragas_report.json) ≡ [reports/ragas_report_with_m5.json](../reports/ragas_report_with_m5.json) (M1+M2+M3 + M5 full enrichment: contextual prepend + HyQA + auto metadata trên 353 chunks, 962s enrich + 7m50 RAGAS, có 2 TimeoutError ở job 33, 58)

| Metric | Naive | Prod (KHÔNG M5) | Prod (CÓ M5) | Δ vs Naive (CÓ M5) |
|--------|-------|-----------------|---------------|---------------------|
| Faithfulness | 0.8802 | 0.9250 | **0.9000** | +0.0198 |
| Answer Relevancy | 0.3442 | 0.4696 | **0.4708** | +0.1266 |
| Context Precision | 0.7750 | 0.9500 | **0.9000** | +0.1250 |
| Context Recall | 0.7600 | 0.8833 | **0.8833** | +0.1233 |

Production (CÓ M5) đậu ngưỡng 0.75 ở 3/4 metric (chỉ trừ `answer_relevancy`).

### So sánh "có M5" vs "không M5"

| Metric | KHÔNG M5 | CÓ M5 | Δ |
|--------|----------|-------|---|
| Faithfulness | 0.9250 | 0.9000 | **-0.0250** |
| Answer Relevancy | 0.4696 | 0.4708 | +0.0012 |
| Context Precision | 0.9500 | 0.9000 | **-0.0500** |
| Context Recall | 0.8833 | 0.8833 | 0 |

Bất ngờ: **M5 enrichment lần này không cải thiện được điểm số**, thậm chí kéo nhẹ `faithfulness` (-0.025) và `context_precision` (-0.05). Lý do khả nghi:
1. **2 TimeoutError** ở job 33 và 58 trong RAGAS bị set về 0 → kéo trung bình xuống mạnh (1 question 0.0 trên 20 = -0.05 điểm trung bình).
2. Enriched text (contextual prefix + question hypothesis được prepend vào chunk) khiến dense embedding bị "loãng" — chunk index không còn purely là raw policy text mà có thêm câu LLM-generated, khiến reranker đôi khi rerank kém hơn.
3. Auto metadata (topic/category/entities) hiện chưa được dùng làm filter ở M2 search → enrichment metadata hoàn toàn không được tận dụng để boost precision.

## Key Findings

1. **Biggest improvement:** **Context Precision +0.125** (0.7750 → 0.9000 với M5, hoặc +0.175 lên 0.9500 nếu KHÔNG M5). Bộ ba M2 Hybrid (BM25 + dense + RRF) → M3 Cross-encoder rerank top-3 lọc context cực sạch — gần như mọi context đưa cho LLM đều liên quan câu hỏi.
2. **Biggest challenge:** **Answer Relevancy vẫn thấp (0.47)** dù precision/recall đều cao. Phân tích `failures` trong [reports/ragas_report.json](../reports/ragas_report.json): **6/10 failures rớt ở `answer_relevancy`** ở các câu về tờ khai thuế GTGT (BCTC.pdf) — context retrieve đúng nhưng LLM trả lời chưa nhắc lại đúng số liệu/thực thể. Đây đúng là điểm Lê Thành Long (M4) đã cảnh báo: "answer_relevancy vẫn thấp hơn kỳ vọng — cần tighten prompt".
3. **Surprise finding:** **M5 enrichment KHÔNG luôn cải thiện điểm số**. Trong run này, enrichment làm tụt nhẹ Faithfulness và Context Precision so với không enrich. Bài học: enrichment có overhead (~1000 LLM calls cho 353 chunks, mất 16 phút) và chỉ thực sự thắng khi (a) auto_metadata được dùng làm filter, (b) HyQA được index như separate field thay vì prepend vào chunk text. Naive baseline có `faithfulness = 0.88` cao bất ngờ — vì `naive_baseline.py:39` trả thẳng `contexts[0]` làm answer (không qua LLM), RAGAS chấm "bám sát context" gần như tuyệt đối — đánh đổi là `answer_relevancy` chỉ 0.34.

## Presentation Notes (5 phút)

1. **RAGAS scores (naive vs production):** chiếu bảng 3 cột (Naive, Prod KHÔNG M5, Prod CÓ M5) — nhấn mạnh **3/4 metric đều tăng mạnh so với naive** (Context Precision +12.5%, Answer Relevancy +12.66%, Context Recall +12.33%, Faithfulness +1.98%). Thẳng thắn nói luôn M5 enrichment chưa "thắng" — đó là nội dung cho slide "next optimization".
2. **Biggest win — module nào, tại sao:** **M3 Reranking + M2 Hybrid** là cặp đôi đẩy Context Precision lên 0.90-0.95. Hybrid (BM25 nắm exact-match tiếng Việt sau khi `underthesea` segment, Dense BGE-M3 nắm semantic, RRF merge) cho recall tốt ở top-20. Cross-encoder rerank top-3 cuối cùng loại bỏ 17 context noise → LLM chỉ nhìn 3 context cực sạch. M1 hierarchical (parent/child) đóng góp Context Recall vì trả parent text đầy đủ thay vì child nhỏ bị orphan.
3. **Case study — 1 failure, Error Tree walkthrough:**
   - **Question:** *"Kỳ tính thuế của tờ khai thuế giá trị gia tăng trong file BCTC.pdf là kỳ nào?"*
   - **Worst metric:** `faithfulness = 0.0` (cả 2 run đều fail câu này) → LLM hallucinating
   - Error Tree: Output đúng? → ❌ → Context đúng? → ✓ retrieve được tờ khai GTGT nhưng OCR/parse PDF không có trường "kỳ tính thuế" rõ ràng → Query OK? → ✓ → **Root cause:** LLM bịa kỳ tính thuế vì context có chữ "tờ khai" nhưng không có trường kỳ → **Fix:** tighten system prompt thêm rule "Nếu context không có chính xác thông tin được hỏi, trả lời 'Không tìm thấy.'", thêm metadata filter `category=finance`, sửa BCTC.pdf parsing để giữ structure bảng.
4. **Next optimization nếu có thêm 1 giờ:**
   - **Tighten answer prompt** (kỳ vọng đẩy answer_relevancy 0.47 → 0.65+): yêu cầu LLM nhắc lại đúng thực thể + số liệu trong câu hỏi, "câu hỏi hỏi gì trả lời nấy".
   - **Sửa cách dùng M5**: index HyQA và summary là **separate Qdrant payload field** thay vì prepend vào chunk text → embed sẽ purely là raw text, M2 search có thể optionally match qua HyQA. Auto metadata dùng làm `metadata filter` ở M2.
   - **Async/batch M5 enrichment**: gộp 3 LLM call (contextual + hyqa + metadata) thành 1 prompt JSON → giảm 3× thời gian/cost từ 16 phút xuống ~5 phút.
   - **Handle RAGAS timeouts**: tăng timeout LLM judge hoặc retry để tránh 2 câu bị 0 điểm kéo trung bình.
   - **Pin version `requirements.txt`** (`qdrant-client`, `ragas`, `openai`, `sentence-transformers`) để CI/giảng viên reproduce ổn định.
