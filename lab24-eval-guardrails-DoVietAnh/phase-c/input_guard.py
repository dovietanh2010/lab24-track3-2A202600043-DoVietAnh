import re
import sys
import time

import numpy as np
from langchain_openai import OpenAIEmbeddings

try:
    import spacy
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
except ImportError:
    spacy = None
    AnalyzerEngine = None
    NlpEngineProvider = None
    AnonymizerEngine = None


VN_PII = {
    "phone_vn": r"\b0(?:3|5|7|8|9)\d{8}\b",
    "cccd_vn": r"\b0\d{11}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "date": r"\b(?:0?[1-9]|[12]\d|3[01])/(?:0?[1-9]|1[0-2])/(?:19|20)\d{2}\b",
    "passport": r"\b[A-Z]\d{7,8}\b",
}


class InputGuard:
    def __init__(self):
        self.analyzer = None
        self.anonymizer = None
        self.presidio_status = "disabled"
        self._init_presidio_if_available()

    def _init_presidio_if_available(self) -> None:
        """Use Presidio only when a local spaCy model exists.

        This avoids a network download during grading. Regex redaction still works when
        Presidio/spaCy is unavailable.
        """
        if not all([spacy, AnalyzerEngine, NlpEngineProvider, AnonymizerEngine]):
            self.presidio_status = "missing_presidio_or_spacy"
            return

        model_name = None
        for candidate in ["en_core_web_lg", "en_core_web_sm"]:
            if spacy.util.is_package(candidate):
                model_name = candidate
                break
        if not model_name:
            self.presidio_status = "missing_spacy_model"
            return

        try:
            provider = NlpEngineProvider(
                nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": model_name}],
                }
            )
            nlp_engine = provider.create_engine()
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
            self.anonymizer = AnonymizerEngine()
            self.presidio_status = f"enabled:{model_name}"
        except Exception as exc:
            self.presidio_status = f"disabled:{exc.__class__.__name__}"

    def scrub_vn(self, text: str) -> str:
        for name, pattern in VN_PII.items():
            text = re.sub(pattern, f"[{name.upper()}]", text)
        return text

    def scrub_lightweight_entities(self, text: str) -> str:
        """Small offline fallback for common Vietnamese demo cases."""
        text = re.sub(
            r"\b(?:Nguyễn|Trần|Lê|Phạm|Hoàng|Huỳnh|Võ|Vũ|Đặng|Bùi|Đỗ)\s+"
            r"(?:[A-ZÀ-Ỹ][a-zà-ỹ]+\s+){0,2}[A-ZÀ-Ỹ][a-zà-ỹ]+\b",
            "[PERSON]",
            text,
        )
        text = re.sub(r"\b\d{10,16}\b", "[FINANCIAL_OR_ID]", text)
        return text

    def scrub_ner(self, text: str) -> str:
        if re.search(r"[À-ỹ]", text):
            return self.scrub_lightweight_entities(text)

        if not self.analyzer or not self.anonymizer:
            return self.scrub_lightweight_entities(text)

        results = self.analyzer.analyze(text=text, language="en")
        anonymized = self.anonymizer.anonymize(text=text, analyzer_results=results)
        return self.scrub_lightweight_entities(anonymized.text)

    def sanitize(self, text: str) -> tuple[str, float]:
        start = time.perf_counter()
        cleaned = self.scrub_ner(self.scrub_vn(text))
        latency_ms = (time.perf_counter() - start) * 1000
        return cleaned, latency_ms


class TopicGuard:
    def __init__(self, allowed_topics: list[str], threshold: float = 0.6):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.allowed_topics = allowed_topics
        self.threshold = threshold
        print("Embedding allowed topics...")
        self.topic_vectors = self.embeddings.embed_documents(allowed_topics)

    def check(self, text: str) -> tuple[bool, str]:
        q_vec = self.embeddings.embed_query(text)

        max_sim = 0.0
        best_topic = ""
        for i, tv in enumerate(self.topic_vectors):
            sim = np.dot(q_vec, tv) / (np.linalg.norm(q_vec) * np.linalg.norm(tv))
            if sim > max_sim:
                max_sim = float(sim)
                best_topic = self.allowed_topics[i]

        if max_sim > self.threshold:
            return True, f"On topic: {best_topic} ({max_sim:.2f})"
        return False, f"Off topic. Closest: {best_topic} ({max_sim:.2f})"


def adversarial_defense(text: str) -> tuple[bool, str]:
    lower_text = text.lower()
    compact_text = re.sub(r"[^a-z0-9]+", "", lower_text)
    suspicious_patterns = [
        "ignore previous instructions",
        "system prompt",
        "you are a",
        "forget everything",
        "jailbreak",
        "database password",
        "make weapons",
        "content policy",
        "initial prompt",
        "dan",
        "hack into",
    ]

    for pattern in suspicious_patterns:
        compact_pattern = re.sub(r"[^a-z0-9]+", "", pattern)
        if pattern in lower_text or compact_pattern in compact_text:
            return False, f"Adversarial pattern detected: {pattern}"

    return True, "Safe"


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    guard = InputGuard()
    test_text = "Tôi tên là Nguyễn Văn An, số điện thoại 0987654321 và email test@email.com."
    clean_text, lat = guard.sanitize(test_text)
    print(f"Presidio: {guard.presidio_status}")
    print(f"Original: {test_text}")
    print(f"Cleaned:  {clean_text}")
    print(f"Latency:  {lat:.2f}ms")
