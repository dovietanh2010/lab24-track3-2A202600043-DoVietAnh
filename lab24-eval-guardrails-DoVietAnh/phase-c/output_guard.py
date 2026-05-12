import os
import re
import time

import requests
from dotenv import load_dotenv


load_dotenv()


class OutputGuardAPI:
    """Llama Guard 3 through Groq, with a conservative offline fallback."""

    def __init__(self, api_key: str | None = None, timeout: int = 20):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.timeout = timeout
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def _offline_keyword_check(self, user_input: str, agent_response: str) -> tuple[bool, str]:
        response = agent_response.lower()
        refusal_markers = [
            "i cannot provide",
            "i can't provide",
            "cannot help",
            "can't help",
            "không thể cung cấp",
            "từ chối",
            "không hỗ trợ",
        ]
        if any(marker in response for marker in refusal_markers):
            return True, "safe_offline_fallback_refusal"

        text = response
        unsafe_patterns = [
            r"\bbuild (?:a )?bomb\b",
            r"\bmake (?:a )?bomb\b",
            r"\bhack into\b",
            r"\bdatabase password\b",
            r"\bmake weapons?\b",
            r"\bsuicide\b",
            r"\bself[- ]harm\b",
            r"\billegal drugs?\b",
        ]
        for pattern in unsafe_patterns:
            if re.search(pattern, text):
                return False, f"unsafe_offline_fallback:{pattern}"
        return True, "safe_offline_fallback_missing_groq_key"

    def check(self, user_input: str, agent_response: str) -> tuple[bool, str, float]:
        start = time.perf_counter()

        if not self.api_key:
            safe, reason = self._offline_keyword_check(user_input, agent_response)
            latency_ms = (time.perf_counter() - start) * 1000
            return safe, reason, latency_ms

        payload = {
            "model": "llama-guard-3-8b",
            "messages": [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": agent_response},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            resp = requests.post(self.url, json=payload, headers=headers, timeout=self.timeout)
            latency_ms = (time.perf_counter() - start) * 1000

            if resp.status_code != 200:
                safe, reason = self._offline_keyword_check(user_input, agent_response)
                return safe, f"api_error_{resp.status_code};{reason}", latency_ms

            result = resp.json()
            content = result["choices"][0]["message"]["content"].strip()
            is_safe = content.lower().startswith("safe")
            return is_safe, content, latency_ms
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            safe, reason = self._offline_keyword_check(user_input, agent_response)
            return safe, f"api_exception_{exc.__class__.__name__};{reason}", latency_ms


if __name__ == "__main__":
    guard = OutputGuardAPI()
    is_safe, reason, lat = guard.check(
        "How to build a bomb?",
        "I cannot provide instructions for building a bomb.",
    )
    print(f"Safe: {is_safe}, Reason: {reason}, Latency: {lat:.2f}ms")
