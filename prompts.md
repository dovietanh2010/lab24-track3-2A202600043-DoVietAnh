# Prompts Used In Lab 24

Tài liệu này ghi lại các prompt chính đã dùng trong bài để reviewer có thể kiểm tra tính minh bạch và academic integrity.

## Phase A - RAG Answer Generation

Nguồn: `day18-rag/src/pipeline.py`.

```text
Trả lời ngắn gọn bằng tiếng Việt, CHỈ dựa trên context.
Giữ nguyên số liệu, tên cơ quan, điều/khoản nếu có.
Không thêm kiến thức ngoài context.
Nếu context không có thông tin thì nói 'Không tìm thấy.'
```

User message format:

```text
Context:
{retrieved_contexts}

Câu hỏi: {query}
```

## Phase B - Pairwise Judge

Nguồn: `phase-b/pairwise_judge.py`.

```text
You are an impartial evaluator. Compare two answers to the same question.

Question: {question}
Answer A: {answer_a}
Answer B: {answer_b}

Rate based on:
- Factual accuracy
- Relevance to question
- Conciseness

Important: judge content quality, not answer length or position.

Output JSON ONLY:
{"winner": "A" or "B" or "tie", "reason": "..."}
```

## Phase B - Absolute Judge

Nguồn: `phase-b/absolute_judge.py`.

```text
Evaluate the following answer to the question based on 4 dimensions (1-5 scale):
1. Factual accuracy (1=many errors, 5=fully accurate)
2. Relevance (1=off-topic, 5=directly answers)
3. Conciseness (1=verbose, 5=appropriately brief)
4. Helpfulness (1=useless, 5=highly useful)

Question: {question}
Answer: {answer}

Output JSON ONLY:
{"accuracy": int, "relevance": int, "conciseness": int, "helpfulness": int, "overall": float}
```

## Phase C - Output Guard

Nguồn: `phase-c/output_guard.py`.

Llama Guard 3 receives a standard user/assistant message pair:

```text
user: {user_input}
assistant: {agent_response}
```

The expected model output is `safe` or `unsafe` with category details. If the Groq API key is unavailable, the code uses a conservative offline keyword fallback and marks the reason explicitly.

## Phase C - Refusal Messages

Nguồn: `phase-c/full_pipeline.py`.

```text
Từ chối trả lời do phát hiện nội dung không phù hợp.
```

```text
Tôi không thể trả lời câu hỏi này vì nó nằm ngoài phạm vi tài liệu (Bảo vệ dữ liệu cá nhân - NĐ13).
```

```text
Hệ thống từ chối cung cấp câu trả lời do vi phạm chính sách an toàn đầu ra.
```
