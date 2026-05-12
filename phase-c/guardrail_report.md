# Báo cáo Guardrails - Phase C

## 1. Input Guard - PII Redaction

### Kiến trúc

- **Layer 1:** Regex cho PII phổ biến ở Việt Nam: số điện thoại, CCCD, email, ngày sinh, passport.
- **Layer 2:** Presidio NER nếu máy có sẵn spaCy model (`en_core_web_lg` hoặc `en_core_web_sm`).
- **Fallback:** Nếu chưa có spaCy model, hệ thống dùng regex/local heuristic để tránh lỗi tải model trong lúc chấm.

### Kết quả kiểm thử

Nguồn: `pii_test_results.csv`.

| Chỉ số | Kết quả |
|---|---:|
| Tổng test cases | 10 |
| Positive PII cases | 8 |
| PII cases phát hiện đúng | 8/8 |
| Negative cases không bị redact | 2/2 |
| Latency trung bình | ~14.24ms |

Các loại PII được test: `PHONE_VN`, `EMAIL`, `CCCD_VN`, `PERSON`, `DATE_TIME`, `PASSPORT`, `FINANCIAL`.

## 2. Topic Scope Validator

Topic guard dùng embedding `text-embedding-3-small`, so sánh cosine similarity với danh sách chủ đề được phép:

1. Bảo vệ dữ liệu cá nhân
2. Nghị định 13
3. Xử lý dữ liệu
4. Quyền chủ thể dữ liệu
5. Vi phạm quy định dữ liệu
6. Chính sách bảo mật
7. Cơ quan chuyên trách bảo vệ dữ liệu cá nhân

Ngưỡng hiện tại: `0.6`. Truy vấn dưới ngưỡng bị từ chối là ngoài phạm vi tài liệu.

## 3. Adversarial Defense

Nguồn: `adversarial_test_results.csv`.

| Chỉ số | Kết quả |
|---|---:|
| Tổng test attacks | 20 |
| Blocked | 18 |
| Bypassed | 2 |
| Detection rate | 90% |

| Attack type | Số lượng | Ghi chú |
|---|---:|---|
| DAN | 5 | Chặn bằng pattern `dan`, `jailbreak`, `forget everything` |
| Roleplay | 4 | Chặn bằng pattern vai trò và content policy |
| Encoding | 2 | Base64 và ROT13 bypass, cần decoder layer |
| Payload Splitting | 3 | Chặn bằng normalize punctuation/space |
| Context Manipulation | 3 | Chặn system prompt / safety override |
| Prompt Leaking | 3 | Chặn system instruction / initial prompt |

Rủi ro còn lại: encoded prompt injection vẫn vượt qua được. Cách cải thiện tiếp theo là decode Base64/ROT13 trước khi rule check, hoặc thêm LLM classifier nhẹ cho input guard.

## 4. Output Guard - Llama Guard 3

`output_guard.py` gọi Groq API với model `llama-guard-3-8b` khi có `GROQ_API_KEY`.

Nếu thiếu key hoặc API lỗi, code không còn trả về “always safe”; thay vào đó dùng fallback keyword check bảo thủ và ghi rõ reason dạng:

- `safe_offline_fallback_missing_groq_key`
- `unsafe_offline_fallback:<pattern>`
- `api_error_<status>;...`
- `api_exception_<type>;...`

Điều này giúp output chạy được khi chấm offline, nhưng kết quả Llama Guard thật vẫn yêu cầu `GROQ_API_KEY`.

## 5. Latency Benchmark

Nguồn: `latency_benchmark.csv` gồm 100 requests.

| Chỉ số | L1 | L2 | L3 | Tổng |
|---|---:|---:|---:|---:|
| Mean | ~20ms | ~1154ms | ~49ms | ~1224ms |
| P50 | ~20ms | ~1100ms | ~47ms | ~1180ms |
| P95 | ~29ms | ~1470ms | ~78ms | ~1560ms |
| Max | ~30ms | ~1486ms | ~79ms | ~1575ms |

Kết luận: P95 tổng thể thấp hơn SLO `2500ms`; guardrail overhead trung bình khoảng `70ms`, tương đương khoảng `5.8%` tổng latency.
