# Individual Reflection - Lab 18

**Tên:** Lê Thành Long  
**Mã sinh viên:** 2A202600105  
**Module phụ trách:** M4 - RAGAS Evaluation, Test Set và Pipeline Evaluation

---

## 1. Đóng góp kỹ thuật

- Module đã implement và hoàn thiện: `src/m4_eval.py` - Module 4: RAGAS Evaluation, kết hợp với phần test set và báo cáo đánh giá pipeline.
- Các hàm/class chính đã làm việc:
  - `load_test_set()`: đọc bộ câu hỏi đánh giá từ `test_set.json`, đảm bảo mỗi phần tử có đủ `question` và `ground_truth`.
  - `evaluate_ragas()`: chạy đánh giá RAGAS cho 4 metrics chính gồm `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`.
  - `EvalResult`: dataclass lưu kết quả theo từng câu hỏi, gồm câu hỏi, câu trả lời, context, ground truth và điểm của từng metric.
  - `failure_analysis()`: phân tích các câu có điểm thấp nhất, xác định metric yếu nhất và gợi ý hướng sửa tương ứng.
  - `save_report()`: lưu kết quả đánh giá ra file JSON để phục vụ phần so sánh và nộp bài.
- Ngoài phần M4, em cũng tham gia hỗ trợ kiểm tra pipeline tổng thể:
  - Rà soát `test_set.json` và thay bằng các câu hỏi có ground truth rõ ràng.
  - Kiểm tra sự khác nhau giữa Basic RAG và Production RAG thông qua báo cáo RAGAS.
  - Phát hiện production pipeline ban đầu có vấn đề ở cách dùng hierarchical chunking: retrieve child chunk nhỏ nhưng chưa lấy lại parent context đầy đủ khi trả lời.
  - Kiểm tra lỗi tương thích thư viện như `qdrant-client`, `ragas`, OpenAI API parameter và parser trong `check_lab.py`.
- Số tests pass: trong lần chạy gần nhất, pytest trực tiếp ghi nhận phần lớn tests đã chạy được, ví dụ `32/37` tests pass.

## 2. Kiến thức học được

- Khái niệm mới nhất em học được là đánh giá RAG không chỉ nhìn vào câu trả lời cuối cùng mà phải tách thành nhiều mặt: câu trả lời có bám context không, câu trả lời có liên quan câu hỏi không, context lấy về có chính xác không và context có đủ thông tin cần thiết không.
- Trước lab này, em thường nghĩ retrieval tốt thì hệ thống RAG sẽ tốt. Sau khi làm, em thấy điều này chưa đủ. Ví dụ production có `context_precision` rất cao, tức là các context được lấy về khá đúng, nhưng nếu context quá ngắn hoặc câu trả lời sinh ra không bám đúng context thì `faithfulness` vẫn có thể thấp.
- Điều bất ngờ nhất là Basic RAG đôi khi có `faithfulness` cao hơn Production RAG. Nguyên nhân là Basic baseline trả gần như trực tiếp đoạn context đầu tiên làm answer, nên RAGAS dễ đánh giá là bám sát context. Trong khi đó Production RAG dùng LLM để sinh câu trả lời, nếu prompt chưa chặt hoặc context chưa đầy đủ thì dễ bị trừ faithfulness.
- Kết nối với bài giảng:
  - Phần RAGAS Evaluation trong slide giúp em hiểu vì sao cần nhiều metric thay vì chỉ dùng một điểm tổng.
  - Phần Error Tree/Failure Analysis giúp em biết cách truy ngược lỗi: output sai là do LLM hallucinate, do thiếu context, do context thừa nhiễu, hay do query/retrieval chưa tốt.
  - Phần Production RAG cho thấy pipeline thực tế là chuỗi nhiều module phụ thuộc nhau. Nếu M1 chunking hoặc M2 retrieval có vấn đề thì M4 evaluation sẽ phản ánh ra bằng điểm context recall/context precision.
  - Phần hierarchical chunking trong bài giảng cũng liên quan trực tiếp tới lỗi em quan sát được: nên retrieve bằng child chunk nhỏ nhưng trả parent chunk lớn hơn cho LLM để có đủ ngữ cảnh.

## 3. Khó khăn & Cách giải quyết

- Khó khăn lớn nhất là sự thay đổi API giữa các phiên bản thư viện. Code mẫu ban đầu phù hợp với API cũ hơn, nhưng môi trường hiện tại dùng các version mới hơn như `qdrant-client 1.17.1`, `ragas 0.4.3` và OpenAI SDK mới. Vì vậy một số lỗi không đến từ thuật toán mà đến từ interface đã thay đổi.
- Các lỗi cụ thể em gặp và cách xử lý:
  - `QdrantClient` không còn method `search()`: nguyên nhân là version mới dùng `query_points()`. Cách xử lý là cập nhật logic search để tương thích API mới.
  - RAGAS báo thiếu cột `question`: nguyên nhân là schema mới dùng `user_input`, `response`, `retrieved_contexts`, `reference`. Cách xử lý là map lại dataset theo schema mới rồi convert kết quả về format nội bộ.
  - RAGAS yêu cầu metric object đã khởi tạo: thay vì truyền metric dạng function/module, cần dùng các class như `Faithfulness()`, `AnswerRelevancy()`, `ContextPrecision()`, `ContextRecall()`.
  - OpenAI model mới không nhận `max_tokens`: cần đổi sang `max_completion_tokens`.
  - `check_lab.py` parse output pytest chưa chắc chắn: khi pytest in dòng tổng kết có dấu `====`, parser cũ cố convert chuỗi `====` thành số. Cách xử lý là dùng regex để lấy đúng số lượng `passed` và `failed`.
- Khó khăn khác là dữ liệu nguồn ban đầu chưa khớp với test set. Một số câu hỏi trong `test_set.json` hỏi về báo cáo tài chính, nhưng file dữ liệu thực tế là tờ khai thuế GTGT. Vì vậy nếu giữ nguyên test set thì RAG không thể trả lời đúng. em đã học được rằng bộ test set phải bám sát corpus thực tế, nếu không metric sẽ đánh giá sai năng lực của pipeline.
- Thời gian debug: khoảng 2-3 giờ, trong đó phần tốn thời gian nhất là chạy pipeline nhiều lần, đọc traceback, phân biệt lỗi môi trường/thư viện với lỗi logic pipeline.

## 4. Nếu làm lại

- Nếu làm lại từ đầu, em sẽ cố định version thư viện trong `requirements.txt` rõ hơn, ví dụ pin `qdrant-client`, `ragas`, `openai`, `sentence-transformers`. Như vậy các bạn trong nhóm và giảng viên khi chạy lại sẽ ít gặp lỗi lệch API hơn.
- em sẽ viết test cho M4 theo hướng mock RAGAS/OpenAI nhiều hơn, để unit test không phụ thuộc API thật, network thật hoặc chi phí gọi LLM. Unit test nên kiểm tra logic mapping dữ liệu và format report, còn việc gọi RAGAS thật nên nằm ở bước integration/evaluation riêng.
- em cũng sẽ chuẩn hóa quy trình tạo test set:
  - Kiểm tra corpus trước.
  - Tạo câu hỏi đúng với từng tài liệu.
  - Viết ground truth ngắn gọn nhưng đủ thông tin.
  - Loại bỏ placeholder trước khi chạy evaluation.
- Nếu có thêm thời gian, em muốn thử tiếp M3 - Reranking. Đây là module ảnh hưởng lớn tới `context_precision`, nhưng cũng dễ gặp vấn đề khi phụ thuộc model tải từ Hugging Face. em muốn thêm fallback reranker local để test vẫn chạy được khi không có network, đồng thời production vẫn dùng cross-encoder thật nếu môi trường hỗ trợ.
- em cũng muốn tối ưu thêm `answer_relevancy`, vì sau khi sửa context, các metric như `faithfulness`, `context_precision`, `context_recall` đã tốt hơn nhưng `answer_relevancy` vẫn thấp hơn kỳ vọng. Hướng cải thiện có thể là prompt trả lời trực tiếp hơn, ngắn hơn và yêu cầu nhắc lại đúng thực thể/số liệu trong câu hỏi.

## 5. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) |
|----------|---------------|
| Hiểu bài giảng | 5 |
| Code quality | 4 |
| Teamwork | 5 |
| Problem solving | 5 |

## 6. Nhận xét cá nhân

Qua Lab 18, em hiểu rõ hơn rằng một hệ thống RAG production không chỉ là ghép embedding model với vector database. Chất lượng cuối cùng phụ thuộc vào rất nhiều quyết định nhỏ: chunk thế nào, search ra sao, rerank bao nhiêu context, prompt có đủ chặt không, và đánh giá bằng metric nào. Điều em thấy hữu ích nhất là quy trình đọc lỗi theo từng tầng. Khi điểm số thấp, không nên kết luận ngay là model kém, mà cần xem retrieval có lấy đúng context không, context có đủ không, answer có bám context không và ground truth có đúng với dữ liệu nguồn không.

em cũng nhận ra việc làm bài lab trong môi trường thực tế khác với đọc slide. Nhiều lỗi phát sinh từ dependency, network, version API và format file. Tuy nhiên chính các lỗi này giúp em hiểu rõ hơn về production engineering: code không chỉ cần đúng về mặt thuật toán, mà còn phải chạy ổn định trong nhiều môi trường khác nhau, có fallback hợp lý và có report rõ ràng để debug.


