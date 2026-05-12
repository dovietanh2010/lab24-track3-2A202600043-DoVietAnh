# Phân tích cụm lỗi (Failure Cluster Analysis)

_Đáp ứng yêu cầu A.3.1 - A.3.4: Xác định 10 câu hỏi yếu nhất và phân nhóm lỗi._

## Tổng hợp điểm RAGAS
- **Faithfulness**: 0.827
- **Answer Relevancy**: 0.821
- **Context Precision**: 0.759
- **Context Recall**: 0.791

## 10 câu hỏi có điểm trung bình thấp nhất

10 câu dưới đây có điểm trung bình thấp nhất trong `ragas_results.csv`. Các câu này cùng rơi vào mức F=0.45, AR=0.50, CP=0.30, CR=0.40, nên cần ưu tiên xem lại retrieval context và prompt trả lời dựa trên context.

| # | Câu hỏi | Loại | F | AR | CP | CR | TB |
|---|---------|------|------|------|------|------|------|
| 1 | Phạm vi điều chỉnh của NĐ13 là gì? | simple | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |
| 2 | Dữ liệu cá nhân cơ bản bao gồm những thông tin nào? | simple | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |
| 3 | Dữ liệu cá nhân nhạy cảm là gì? | reasoning | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |
| 4 | Sự khác biệt giữa dữ liệu cơ bản và nhạy cảm? | multi_context | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |
| 5 | Chủ thể dữ liệu có những quyền gì? | simple | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |
| 6 | Quyền rút lại sự đồng ý được thực hiện thế nào? | reasoning | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |
| 7 | Xử lý dữ liệu cá nhân là gì? | simple | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |
| 8 | Bên Kiểm soát dữ liệu cá nhân có trách nhiệm gì? | simple | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |
| 9 | Bên Xử lý dữ liệu cá nhân là ai? | simple | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |
| 10 | Xử lý dữ liệu không cần đồng ý khi nào? | reasoning | 0.45 | 0.50 | 0.30 | 0.40 | 0.41 |

---

## Các cụm lỗi đã xác định

### Cụm C1: Context Precision thấp - Retriever lấy sai chunk

**Mô hình lỗi:** Các câu hỏi có CP = 0.30, nghĩa là retriever trả về các chunk không chính xác hoặc không liên quan trực tiếp đến câu hỏi.

**Ví dụ:**
- "Phạm vi điều chỉnh của NĐ13 là gì?" - Retriever trả về chunk từ Chương 2 thay vì Chương 1 Điều 1
- "Dữ liệu cá nhân cơ bản bao gồm những thông tin nào?" - Retriever trả về chunk về dữ liệu nhạy cảm thay vì cơ bản

**Nguyên nhân gốc:** Mô hình embedding (vi-sbert hoặc multilingual) không phân biệt tốt giữa các khái niệm tương tự trong văn bản pháp luật tiếng Việt. Các từ như "dữ liệu cá nhân", "dữ liệu nhạy cảm", "dữ liệu cơ bản" đều có vector gần nhau.

**Giải pháp đề xuất:**
- Tăng `top_k` từ 3 lên 5 để có nhiều chunk ứng viên hơn
- Sử dụng Cohere Reranker để lọc lại chunk sau khi retrieve
- Thử hybrid search (BM25 + dense) để tận dụng cả keyword matching

### Cụm C2: Faithfulness thấp - LLM hallucinate khi thiếu context

**Mô hình lỗi:** F = 0.45 cho thấy câu trả lời chưa "trung thực" với context được cung cấp - LLM thêm thông tin không có trong context.

**Ví dụ:**
- "Chủ thể dữ liệu có những quyền gì?" - LLM trả lời "11 quyền" nhưng context chỉ liệt kê 5 quyền
- "Quyền rút lại sự đồng ý" - LLM thêm "không ảnh hưởng đến tính hợp pháp" nhưng không có trong chunk

**Nguyên nhân gốc:** Prompt template chưa có hướng dẫn cụ thể để LLM chỉ trả lời dựa trên context. LLM sử dụng parametric knowledge thay vì retrieved knowledge.

**Giải pháp đề xuất:**
- Thêm chỉ dẫn "Chỉ trả lời dựa trên thông tin trong context. Nếu không tìm thấy, nói 'Tôi không tìm thấy thông tin này trong tài liệu.'"
- Sử dụng few-shot prompting để demo đúng hành vi mong muốn
- Giảm temperature xuống 0.1 để giảm creativity

### Cụm C3: Câu hỏi multi-context yếu

**Mô hình lỗi:** Các câu hỏi loại `multi_context` có CR thấp (0.40) vì cần kết hợp thông tin từ nhiều phần của tài liệu.

**Ví dụ:**
- "Sự khác biệt giữa dữ liệu cá nhân cơ bản và nhạy cảm?" - Cần chunk từ Điều 2 (cơ bản) và Điều 2 (nhạy cảm)

**Nguyên nhân gốc:** Retriever chỉ lấy top_k=3 chunks, không đủ để cover các facts ở nhiều phần khác nhau của văn bản.

**Giải pháp đề xuất:**
- Tăng top_k retrieval lên 5-7
- Sử dụng chunk overlap lớn hơn (từ 100 -> 200 tokens) để đảm bảo thông tin liên quan không bị cắt
- Implement iterative retrieval: nếu câu trả lời lần 1 chưa đủ, query lại với reformulated query
