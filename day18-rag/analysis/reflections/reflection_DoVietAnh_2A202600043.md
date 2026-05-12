# Individual Reflection — Lab 18

**Tên:** Đỗ Việt Anh 
**Module phụ trách:** M2: Hybrid Search

---

## 1. Đóng góp kỹ thuật

- **Module đã implement:** `src/m2_search.py`- Module 2: Hybrid Search.
- **Các hàm/class chính đã viết:** 
    - `segment_vietnamese()`: Sử dụng `underthesea` để tách từ tiếng Việt.
    - `BM25Search`: Lập chỉ mục và tìm kiếm bằng thuật toán BM25 (Rank-BM25).
    - `DenseSearch`: Tích hợp Qdrant và SentenceTransformers (model BGE-M3) để tìm kiếm vector.
    - `reciprocal_rank_fusion()`: Kết hợp kết quả từ BM25 và Dense Search bằng thuật toán RRF.
    - `HybridSearch`: Lớp bao bọc (wrapper) để chạy luồng tìm kiếm hỗn hợp.
- **Số tests pass:** 5/5 (Tất cả các test case cho Module 2 đã vượt qua thành công).

## 2. Kiến thức học được

- **Khái niệm mới nhất:** Reciprocal Rank Fusion (RRF) - một cách cực kỳ hiệu quả để kết hợp kết quả từ nhiều nguồn tìm kiếm khác nhau mà không cần chuẩn hóa điểm số (normalization). Hiểu rõ hơn về cách Qdrant lưu trữ và truy vấn vector.
- **Điều bất ngờ nhất:** Thư viện `underthesea` có sự khác biệt về kết quả tách từ giữa cụm từ ngắn và cụm từ dài (ví dụ: "nghỉ phép" vs "nghỉ phép năm"), điều này gây ảnh hưởng trực tiếp đến độ chính xác của BM25.
- **Kết nối với bài giảng (slide nào):** Chương 5: Fix ONLINE — Retrieval & Augment (Slide về Hybrid Search, Metadata Filtering & Reranking — fix R và A).

## 3. Khó khăn & Cách giải quyết

- **Khó khăn lớn nhất:**
    - BM25 không trả về kết quả do tokenization tiếng Việt không nhất quán (ví dụ: “nghỉ phép” bị tách khác nhau giữa query và dữ liệu như “nghỉ_phép” vs “nghỉ phép”), dẫn đến toàn bộ điểm số bằng 0 và hệ thống không truy hồi được dữ liệu.
- **Cách giải quyết:**
    - Chuẩn hóa pipeline tokenization cho cả query và corpus (lowercase, xử lý lại định dạng token), đồng thời loại bỏ điều kiện lọc score > 0 để luôn lấy top-k kết
- **Thời gian debug:** Khoảng 10 phút, chủ yếu để trace tokenization và kiểm tra phân phối score của BM25.

## 4. Nếu làm lại

- **Sẽ làm khác điều gì:**
    - Sẽ thiết kế pipeline xử lý văn bản ngay từ đầu theo hướng chuẩn hóa thống nhất (tokenization, lowercase, xử lý dấu câu) thay vì debug sau khi gặp lỗi. Đồng thời, sẽ kết hợp BM25 với embedding ngay từ đầu để tránh phụ thuộc hoàn toàn vào keyword matching.
- **Module nào muốn thử tiếp:**
    - Module 3 (Reranking) để cải thiện chất lượng kết quả sau Hybrid Search, đặc biệt trong các trường hợp query dài hoặc mang tính ngữ nghĩa cao.

## 5. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) |
|----------|---------------|
| Hiểu bài giảng | 5 |
| Code quality | 5 |
| Teamwork | 5 |
| Problem solving | 5 |
