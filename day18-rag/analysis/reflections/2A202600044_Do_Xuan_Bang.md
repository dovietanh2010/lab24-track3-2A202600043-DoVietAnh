# Individual Reflection - Lab 18

**Tên:** Đỗ Xuân Bằng  
**Mã sinh viên:** 2A202600044  
**Module phụ trách:** M1 - Advanced Chunking Strategies

---

## 1. Đóng góp kỹ thuật

- Module đã implement: `src/m1_chunking.py` - Module 1: Advanced Chunking Strategies.
- Các hàm/class chính đã viết:
  - `Chunk`: dataclass lưu nội dung chunk, metadata và `parent_id`.
  - `chunk_semantic()`: tách văn bản thành các câu, tính cosine similarity bằng token vector và gom các câu gần cùng chủ đề vào một chunk.
  - `chunk_hierarchical()`: tạo parent chunks và child chunks, mỗi child có `parent_id` liên kết về parent tương ứng.
  - `chunk_structure_aware()`: parse markdown headers để chia theo section logic, giữ nguyên bảng, list và code block trong cùng section.
  - `compare_strategies()`: chạy basic, semantic, hierarchical và structure-aware chunking để so sánh số chunk, độ dài trung bình, min và max.
- Số tests pass: 13/13 với lệnh `pytest tests\test_m1.py`.

## 2. Kiến thức học được

- Khái niệm mới nhất: hierarchical parent-child chunking. Theo slide 8/42, chiến lược này nên là default vì retrieve trên child chunk nhỏ giúp tăng precision, sau đó return parent chunk lớn để LLM có full context.
- Điều bất ngờ nhất: fixed-size chunking có thể cắt giữa câu hoặc giữa ý, còn semantic chunking nhóm theo similarity nên giữ ý tốt hơn. Vì vậy chunking không chỉ là chia nhỏ văn bản, mà quyết định trực tiếp chất lượng retrieval phía sau.
- Kết nối với bài giảng:
  - Slide 8/42 - Chunking Strategies: phần code đã hiện thực đúng 3 hướng so sánh trong slide: semantic dùng cosine threshold, hierarchical dùng parent/child, và basic/fixed-size làm baseline để đối chiếu.
  - Slide 9/42 - Structure-Aware & Late Chunking: `chunk_structure_aware()` bám theo ý tưởng parse markdown headers rồi chunk theo logical structure, đồng thời giữ nguyên tables, code blocks và lists để không cắt giữa chừng.
  - Slide 10/42 - Embedding Model Selection: M1 chưa trực tiếp embed, nhưng thiết kế chunk cần phù hợp với bước embedding sau đó. Với tiếng Việt, slide gợi ý các model như `bge-m3` hoặc `multilingual-e5-large`; chunk tốt sẽ giúp các model này biểu diễn ngữ nghĩa chính xác hơn.
  - Slide 11/42 - Contextual Retrieval: hierarchical chunking có liên quan trực tiếp đến ý tưởng bổ sung context trước khi embed. Child chunk dùng để search chính xác, còn parent/context giúp tránh chunk bị "orphan", không biết xung quanh nói gì.
  - Slide 12/42 - Multimodal Embeddings: module hiện tại tập trung text chunking; nếu corpus có nhiều nội dung ảnh, bảng scan hoặc PDF nhiều layout, có thể cân nhắc hướng document-as-image/multimodal retrieval ở các bước mở rộng.

## 3. Khó khăn & Cách giải quyết

- Khó khăn lớn nhất: thiết kế semantic chunking sao cho vẫn bám theo ý tưởng cosine similarity trong slide, nhưng không phụ thuộc bắt buộc vào việc tải model embedding trong môi trường local.
- Cách giải quyết: dùng fallback nhẹ bằng token-count vector và cosine similarity. Cách này giữ được logic gom câu theo độ tương đồng, chạy ổn định khi test và không cần thêm dependency mới.
- Thời gian debug: khoảng 20-30 phút, tập trung vào metadata của hierarchical chunking và đảm bảo mỗi child có `parent_id` hợp lệ.

## 4. Nếu làm lại

- Sẽ làm khác điều gì: nếu có thêm thời gian và môi trường đầy đủ dependency, tôi sẽ thêm lựa chọn semantic chunking bằng embedding model thật, ví dụ `bge-m3` cho tiếng Việt như slide 10/42 gợi ý.
- Tôi cũng muốn thử thêm contextual prepend như slide 11/42: trước khi embed mỗi child chunk, thêm một câu ngắn giải thích chunk nằm ở đâu trong tài liệu để giảm retrieval failure.
- Module nào muốn thử tiếp: M2 - Hybrid Search, vì đây là bước sử dụng trực tiếp các chunk của M1 để kết hợp BM25, dense vector và RRF fusion.

## 5. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) |
|----------|---------------|
| Hiểu bài giảng | 5 |
| Code quality | 5 |
| Teamwork | 5 |
| Problem solving | 5 |
