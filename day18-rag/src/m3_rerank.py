"""Module 3: Reranking — Cross-encoder top-20 → top-3 + latency benchmark."""

import os, sys, time
from dataclasses import dataclass

# 1. Bỏ qua lỗi thiếu DLL FFmpeg (torchcodec)
sys.modules['torchcodec'] = None

# 2. Vá lỗi tương thích cho transformers bản mới/cũ
try:
    import transformers
    if hasattr(transformers, "PreTrainedTokenizer") and not hasattr(transformers.PreTrainedTokenizer, "prepare_for_model"):
        def prepare_for_model(self, *args, **kwargs):
            return self.prepare_seq2seq_batch(*args, **kwargs)
        transformers.PreTrainedTokenizer.prepare_for_model = prepare_for_model
except ImportError:
    pass


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RERANK_TOP_K


@dataclass
class RerankResult:
    text: str
    original_score: float
    rerank_score: float
    metadata: dict
    rank: int


class CrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                # Ưu tiên FlagEmbedding
                from FlagEmbedding import FlagReranker
                self._model = FlagReranker(self.model_name, use_fp16=True)
            except (ImportError, AttributeError, RuntimeError):
                # Fallback sang sentence-transformers
                try:
                    from sentence_transformers import CrossEncoder
                    self._model = CrossEncoder(self.model_name)
                except (ImportError, AttributeError, RuntimeError):
                    # Fallback cuối cùng sang Flashrank (nếu có)
                    try:
                        from flashrank import Ranker
                        self._model = Ranker()
                    except ImportError:
                        self._model = "fallback"
        return self._model

    def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:
        """Rerank documents: top-20 → top-k."""
        if not documents:
            return []

        model = self._load_model()
        
        if model == "fallback":
            ranked = [(doc.get("score", 0.0), doc) for doc in documents][:top_k]
        elif hasattr(model, "rerank"): # Flashrank case
            from flashrank import RerankRequest
            passages = [{"text": doc.get("text", "")} for doc in documents]
            results = model.rerank(RerankRequest(query=query, passages=passages))
            ranked = [(item["score"], {"text": item["text"], "metadata": documents[0].get("metadata", {}), "score": 0.0}) for item in results[:top_k]]
        else:
            pairs = [(query, doc.get("text", "")) for doc in documents]
            if hasattr(model, "compute_score"):
                scores = model.compute_score(pairs)
            else:
                scores = model.predict(pairs)
            ranked = sorted(zip(scores, documents), key=lambda item: item[0], reverse=True)[:top_k]

        return [
            RerankResult(
                text=doc.get("text", ""),
                original_score=float(doc.get("score", 0.0)),
                rerank_score=float(score),
                metadata=doc.get("metadata", {}),
                rank=i + 1,
            )
            for i, (score, doc) in enumerate(ranked)
        ]


class FlashrankReranker:
    """Lightweight alternative (<5ms). Optional."""
    def __init__(self):
        self._model = None

    def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:
        if not documents: return []
        if self._model is None:
            try:
                from flashrank import Ranker, RerankRequest
                self._model = (Ranker(), RerankRequest)
            except ImportError: return []
        model, request_cls = self._model
        passages = [{"text": doc.get("text", "")} for doc in documents]
        results = model.rerank(request_cls(query=query, passages=passages))
        ranked = sorted(results, key=lambda item: item.get("score", 0.0), reverse=True)[:top_k]
        return [RerankResult(text=item.get("text", ""), original_score=float(documents[0].get("score", 0.0)), 
                             rerank_score=float(item.get("score", 0.0)), metadata=documents[0].get("metadata", {}), rank=i + 1)
                for i, item in enumerate(ranked)]


def benchmark_reranker(reranker, query: str, documents: list[dict], n_runs: int = 5) -> dict:
    """Benchmark latency over n_runs."""
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        reranker.rerank(query, documents)
        times.append((time.perf_counter() - start) * 1000.0)
    if not times: return {"avg_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}
    return {"avg_ms": sum(times) / len(times), "min_ms": min(times), "max_ms": max(times)}


if __name__ == "__main__":
    query = "Nhân viên được nghỉ phép bao nhiêu ngày?"
    docs = [{"text": "Nhân viên được nghỉ 12 ngày/năm.", "score": 0.8}, {"text": "Mật khẩu thay đổi mỗi 90 ngày.", "score": 0.7}]
    reranker = CrossEncoderReranker()
    for r in reranker.rerank(query, docs):
        print(f"[{r.rank}] {r.rerank_score:.4f} | {r.text}")
