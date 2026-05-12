# Testset Review Notes

_Đáp ứng yêu cầu A.1.4: Đánh giá thủ công >= 10 câu hỏi, và A.1.5: Ít nhất 1 câu hỏi đã chỉnh sửa._

## Phân bố testset

Nguồn: `testset_v1.csv` gồm 50 câu.

| Loại câu hỏi | Số lượng | Tỷ lệ |
|---|---:|---:|
| simple | 25 | 50% |
| reasoning | 12 | 24% |
| multi_context | 13 | 26% |

Phân bố này gần đúng mục tiêu đề bài: 50% simple, 25% reasoning, 25% multi-context.

## Đánh giá thủ công

| # | Câu hỏi | Ground Truth | Loại | Nhận xét |
|---|---------|-------------|------|----------|
| 1 | Phạm vi điều chỉnh của Nghị định 13/2023/NĐ-CP là gì? | Nghị định quy định về bảo vệ dữ liệu cá nhân và trách nhiệm của các bên liên quan. | simple | OK - Chính xác, trích dẫn đúng Điều 1 |
| 2 | Dữ liệu cá nhân cơ bản bao gồm những thông tin nào? | Bao gồm họ tên, ngày tháng năm sinh, nhóm máu, giới tính. | simple | OK - Đầy đủ, có thể thêm số CMND/CCCD |
| 3 | Dữ liệu cá nhân nhạy cảm là gì? | Là dữ liệu gắn với quyền riêng tư, nếu bị xâm phạm sẽ gây ảnh hưởng nghiêm trọng. | reasoning | OK - Chính xác theo Điều 2 |
| 4 | Sự khác biệt giữa dữ liệu cá nhân cơ bản và nhạy cảm? | Dữ liệu cơ bản là thông tin nhận diện chung, còn dữ liệu nhạy cảm liên quan đến sức khỏe, sinh trắc học, đời tư sâu sắc. | multi_context | OK - So sánh tốt, nhưng có thể thêm ví dụ cụ thể hơn |
| 5 | Chủ thể dữ liệu có những quyền gì? | Chủ thể có 11 quyền cơ bản bao gồm quyền được biết, đồng ý, truy cập, xóa và khiếu nại. | simple | OK - Cần bổ sung thêm các quyền còn lại |
| 6 | Quyền rút lại sự đồng ý được thực hiện thế nào? | Có thể rút lại bất kỳ lúc nào nhưng không làm ảnh hưởng đến dữ liệu đã xử lý trước khi rút. | reasoning | OK - Chính xác |
| 7 | Xử lý dữ liệu cá nhân là gì? | Là các hoạt động như thu thập, lưu trữ, phân tích và xóa dữ liệu cá nhân. | simple | **SỬA** - Cần thêm "ghi, xác nhận, cập nhật" |
| 8 | Bên Kiểm soát dữ liệu cá nhân có trách nhiệm gì? | Chịu trách nhiệm quyết định mục đích và cách thức (phương tiện) xử lý dữ liệu cá nhân. | simple | OK - Rõ ràng |
| 9 | Bên Xử lý dữ liệu cá nhân là ai? | Là bên thực hiện các thao tác xử lý dữ liệu thay mặt và theo yêu cầu của Bên Kiểm soát. | simple | OK - Phân biệt rõ với Bên Kiểm soát |
| 10 | Trong trường hợp nào được xử lý dữ liệu mà không cần sự đồng ý? | Trong tình trạng khẩn cấp đe dọa tính mạng, yêu cầu y tế khẩn cấp hoặc an ninh quốc gia. | reasoning | OK - Nhưng nên bổ sung thêm trường hợp luật định |

## Câu hỏi đã chỉnh sửa (A.1.5)

**Câu hỏi gốc:** "Xử lý dữ liệu cá nhân là gì?"
**Câu hỏi mới:** "Xử lý dữ liệu cá nhân theo Nghị định 13 bao gồm những hoạt động cụ thể nào?"
**Lý do:** Câu hỏi gốc quá chung chung, câu mới yêu cầu liệt kê cụ thể các hoạt động xử lý (thu thập, ghi, phân tích, lưu trữ, chỉnh sửa, công khai, kết hợp, truy cập, lấy, sử dụng, tiết lộ, xóa, hủy) để kiểm tra khả năng retrieve chi tiết của RAG pipeline.
