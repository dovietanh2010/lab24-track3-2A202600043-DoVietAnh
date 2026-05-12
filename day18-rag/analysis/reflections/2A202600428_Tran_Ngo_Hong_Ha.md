# Individual Reflection — Lab 18

**Tên:** Trần Ngô Hồng Hà  
**Module phụ trách:** [M3]

---

## 1. Đóng góp kỹ thuật

- Module đã implement: Rerank (M3) — Cross-encoder top-20 → top-3 + latency benchmark
- Các hàm/class chính đã viết:
    + `CrossEncoderReranker()` — Class chính với model loading & multi-fallback strategy
    + `rerank()` — Hàm reranking documents sử dụng FlagEmbedding/sentence-transformers/flashrank
    + `FlashrankReranker` — Lightweight alternative (<5ms) cho reranking
    + `benchmark_reranker()` — Benchmark latency over n_runs với thống kê min/max/avg
- Số tests pass: 5/5

## 2. Kiến thức học được

- **Khái niệm mới nhất:**
  - Cross-encoder reranking: Khác biệt giữa retrieval (dense/sparse) vs reranking (pair-wise scoring)
  - Model fallback strategy: FlagEmbedding → sentence-transformers → flashrank → fallback
  - Latency profiling với `time.perf_counter()` để benchmark inference time
  - RerankResult dataclass để chuẩn hóa output format

- **Điều bất ngờ nhất:**
  - Độ khác biệt lớn giữa mô hình: FlagEmbedding nhanh hơn nhưng sentence-transformers ổn định hơn
  - Flashrank tốc độ siêu nhanh (<5ms) nhưng có trade-off về độ chính xác

- **Kết nối với bài giảng:**
  - Phần `Fix ONLINE - Retrieval & Augment`: slide 22

## 3. Khó khăn & Cách giải quyết

- **Khó khăn lớn nhất:**
  - Xử lý bất tương thích giữa các phiên bản transformers (torchcodec missing, prepare_for_model method)
  - Multiple model fallbacks khiến code phức tạp nhưng cần để production robustness

- **Cách giải quyết:**
  - Thêm sys.modules['torchcodec'] = None để bypass DLL error
  - Patch transformers.PreTrainedTokenizer nếu thiếu prepare_for_model
  - Try-except chain cho 3 fallback options (FlagEmbedding → sentence-transformers → flashrank)
  - Test từng fallback path riêng biệt

- **Thời gian debug:** ~1 giờ (chủ yếu xử lý environment & model loading issues)

## 4. Nếu làm lại

- **Sẽ làm khác điều gì:**
  - Tách model initialization sang separate function để caching tốt hơn
  - Thêm logging để track fallback path được dùng
  - Unit test cho từng fallback scenario riêng
  - Thêm config option cho model_name để flexibility hơn

- **Module nào muốn thử tiếp:**
  - M4_eval (evaluation metrics) — muốn hiểu cách evaluate reranking quality
  - M5_enrichment (enrichment techniques) — muốn tìm hiểu augmentation strategies

## 5. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) |
|----------|---------------|
| Hiểu bài giảng | 4 |
| Code quality | 4 |
| Teamwork | 5 |
| Problem solving | 5 |

**Giải thích:** error handling & fallback strategy khá ổn. Hiểu sâu về reranking nhưng vẫn có thể tối ưu hơn. Team work tốt, tích cực debug & support teammates. Problem solving xử lý được các lỗi environment phức tạp.
