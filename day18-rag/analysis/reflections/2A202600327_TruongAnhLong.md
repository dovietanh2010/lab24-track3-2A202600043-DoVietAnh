# Individual Reflection - Lab 18

**Tên:** Trương Ánh Long
**Mã sinh viên:** 2A202600327
**Module phụ trách:** M5 - Enrichment Pipeline

---

## 1. Đóng góp kỹ thuật

- Module đã implement: `src/m5_enrichment.py` - Module 5: Enrichment Pipeline (TODO 1, 2, 3).
- Các hàm/class chính đã viết:
  - `summarize_chunk()`: gọi `gpt-4o-mini` tóm tắt chunk trong 2-3 câu tiếng Việt; có fallback extractive (lấy 2 câu đầu) khi máy không có `OPENAI_API_KEY` để pipeline vẫn chạy được offline.
  - `generate_hypothesis_questions()`: prompt LLM sinh `n_questions` câu hỏi tiếng Việt mà chunk có thể trả lời, parse output theo từng dòng và strip prefix số/dấu gạch đầu dòng (`0123456789.-) `) trước khi return.
  - `contextual_prepend()`: gọi LLM viết 1 câu mô tả chunk nằm ở đâu trong tài liệu rồi prepend vào nội dung gốc; fallback dùng template `"Trích từ tài liệu '{document_title}'."` để vẫn giữ nguyên `original_text` (Anthropic-style contextual retrieval).
  - Cả 3 hàm đều có guard `if not text or not text.strip()` ở đầu và bọc lời gọi OpenAI trong `try/except` để không làm crash khi API lỗi.
- Số tests pass: 10/10 với lệnh `python -m pytest tests/test_m5.py -v`.

## 2. Kiến thức học được

- Khái niệm mới nhất: **enrichment pipeline** chạy ở giai đoạn indexing (one-time cost) chứ không phải lúc query. Mỗi chunk được "làm giàu" bằng summary, hypothesis questions, và contextual prefix trước khi đưa vào embedding model, nhờ đó cải thiện chất lượng retrieval cho **mọi query** sau này mà không tăng latency lúc serve.
- Điều bất ngờ nhất: HyQA (Hypothesis Question-Answer) bridge được **vocabulary gap**. User hỏi *"nghỉ phép bao nhiêu ngày?"* nhưng tài liệu chỉ viết *"12 ngày làm việc mỗi năm"* - hai câu này có cosine similarity thấp dù cùng nói về một chuyện. Bằng cách generate trước câu hỏi *"Nhân viên được nghỉ bao nhiêu ngày?"* và index cùng chunk, retrieval match trực tiếp question-to-question thay vì question-to-document.
- Kết nối với bài giảng:
  - Slide 11/42 - Contextual Retrieval: `contextual_prepend()` chính là cách hiện thực ý tưởng Anthropic công bố - thêm 1 câu context "chunk nằm ở đâu, nói về gì" trước khi embed, theo benchmark giảm 49% retrieval failure khi dùng riêng. Prompt tôi viết yêu cầu LLM trả về đúng 1 câu với `max_tokens=80` để giữ overhead nhỏ.
  - Slide 8/42 - Chunking Strategies: enrichment bổ trợ cho chunking. Dù M1 cắt chunk khéo đến đâu, một chunk thiếu context xung quanh vẫn có thể bị "orphan"; M5 vá lỗ hổng đó bằng summary và contextual prefix.
  - Slide 10/42 - Embedding Model Selection: với tiếng Việt + `bge-m3`, summary tiếng Việt và HyQA tiếng Việt giúp embedding biểu diễn đúng ngữ nghĩa miền (HR, IT policy) thay vì để model phải "đoán" qua đoạn raw text dài đầy noise.
  - Slide 12/42 - Auto Metadata & Filtering: TODO 4 (`extract_metadata`) là bước tiếp theo của pipeline - extract `topic/entities/category` ra JSON để enable rich filtering ở M2 (ví dụ filter `category="policy"` trước khi BM25 + dense search).

## 3. Khó khăn & Cách giải quyết

- Khó khăn lớn nhất: cân bằng giữa "dùng API thật để có chất lượng tốt" và "test phải pass kể cả khi máy chấm bài không có `OPENAI_API_KEY`". Test `test_contextual_contains_original` bắt buộc `SAMPLE in result`, còn `test_summarize_returns_string` đòi return string không null.
- Cách giải quyết: thiết kế **dual-path** cho cả 3 hàm. Path chính gọi `gpt-5.4-nano` qua `from openai import OpenAI`, path fallback dùng heuristic không cần API:
  - `summarize_chunk` → split câu theo `". "` rồi lấy 2 câu đầu.
  - `generate_hypothesis_questions` → trả `[]` (test chấp nhận list rỗng vì có guard `if result:`).
  - `contextual_prepend` → ghép template `"Trích từ tài liệu '{document_title}'."` + `\n\n` + text gốc, đảm bảo `SAMPLE in result` luôn đúng.
- Ngoài ra, parse output của LLM cho HyQA cũng cần cẩn thận: model hay trả `"1. Câu hỏi..."` hoặc `"- Câu hỏi..."`, nên tôi `.lstrip("0123456789.-) ")` rồi `[:n_questions]` để tránh trả vượt số câu hỏi user yêu cầu.
- Thời gian debug: khoảng 25-30 phút, tập trung vào prompt engineering tiếng Việt và xử lý edge case khi text rỗng/whitespace.

## 4. Nếu làm lại

- Sẽ làm khác điều gì: thay vì gọi 3 lần API riêng cho summary, HyQA và contextual prefix, tôi sẽ gộp thành **1 prompt duy nhất** trả JSON `{"summary": ..., "questions": [...], "context": ...}` để giảm 3x chi phí và 3x latency lúc indexing. Với corpus lớn vài nghìn chunk thì khoản tiết kiệm này không nhỏ.
- Tôi cũng muốn thêm **caching theo hash của chunk text** để re-index không gọi lại API cho chunks không đổi - đúng tinh thần "enrichment = one-time cost" mà slide nhấn mạnh.
- Module nào muốn thử tiếp: M3 - Reranking, vì sau khi M5 đã làm sạch input ở giai đoạn index, M3 là lớp lọc cuối cùng ở giai đoạn query (cross-encoder bge-reranker-v2-m3) để xem cải thiện precision có cộng dồn được không.

## 5. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) |
|----------|---------------|
| Hiểu bài giảng | 5 |
| Code quality | 5 |
| Teamwork | 5 |
| Problem solving | 5 |