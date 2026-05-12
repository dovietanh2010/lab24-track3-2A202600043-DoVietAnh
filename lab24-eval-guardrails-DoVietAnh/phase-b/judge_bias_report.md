# Báo cáo Thiên Kiến của Judge

_Đáp ứng yêu cầu B.4: quan sát ít nhất 2 bias và nêu chiến lược giảm thiểu._

## 1. Tổng kết Pairwise Judge

Nguồn: `pairwise_results.csv` và `pairwise_summary.json`.

| Chỉ số | Giá trị |
|---|---:|
| Tổng số câu hỏi | 30 |
| Production/B thắng | 22/30 = 73.3% |
| Baseline/A thắng | 7/30 = 23.3% |
| Hòa | 1/30 = 3.3% |

Kết luận: Production/B thắng nhiều hơn baseline. Tuy nhiên kết quả cần đọc cùng bias analysis vì baseline trong file hiện tại ngắn hơn rõ rệt.

## 2. Bias 1 - Position Bias

Position bias xảy ra khi judge ưu tiên Answer A hoặc Answer B do vị trí hiển thị.

### Cách giảm thiểu đã implement

`pairwise_judge.py` chạy judge 2 lượt:

1. Lượt 1: A = baseline, B = production.
2. Lượt 2: A = production, B = baseline.
3. Map kết quả lượt 2 về nhãn gốc rồi chỉ giữ winner nếu 2 lượt đồng thuận; nếu không đồng thuận thì gán `tie`.

### Ghi chú về output hiện tại

File `pairwise_results.csv` hiện có các cột `run1_winner`, `run2_winner`, `winner_after_swap`, nhưng dữ liệu cũ không lưu raw positional winner của lượt 2. Script đã được sửa để các lần chạy sau lưu thêm `run2_raw_position_winner`, giúp kiểm tra position bias đầy đủ hơn.

Rủi ro còn lại: nếu judge bị bias theo vị trí nhưng 2 lượt đều bị parse hoặc map sai, cần kiểm tra log raw output của judge.

## 3. Bias 2 - Length Bias

Length bias xảy ra khi judge ưu tiên câu trả lời dài hơn, dù nội dung chưa chắc tốt hơn.

Quan sát từ output hiện tại:

| Chỉ số | Giá trị |
|---|---:|
| Baseline/A thắng | 7 |
| Production/B thắng | 22 |
| Tie | 1 |
| Baseline thường bị rút gọn | Có |
| Production thường dài hơn | Có |

Ví dụ trong `pairwise_results.csv`, nhiều baseline có dạng bị cắt bằng dấu `...`, còn production thường là câu hoàn chỉnh. Vì vậy việc B thắng nhiều có thể phản ánh chất lượng tốt hơn, nhưng cũng có khả năng bị cộng hưởng bởi length bias.

### Cách giảm thiểu

- Prompt judge đã thêm chỉ dẫn: đánh giá chất lượng nội dung, không đánh giá theo độ dài hoặc vị trí.
- Absolute scoring có chiều `conciseness` để phạt câu trả lời dài không cần thiết.
- Khi chạy lại, nên tạo baseline đầy đủ thay vì baseline bị truncate để so sánh công bằng hơn.

## 4. Human Calibration

Nguồn: `human_labels.csv`, `pairwise_results.csv`, `kappa_summary.json`.

| Chỉ số | Giá trị |
|---|---:|
| Số mẫu human-labeled | 10 |
| Cohen's Kappa | 0.615 |
| Diễn giải | Substantial agreement |

Kappa `0.615` đủ dùng để theo dõi xu hướng monitoring, nhưng chưa đủ mạnh để coi LLM judge là nhãn tuyệt đối. Nên mở rộng human labels lên 30 mẫu nếu dùng để quyết định pass/fail production.
