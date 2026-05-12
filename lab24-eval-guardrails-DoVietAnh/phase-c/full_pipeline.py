import time
import asyncio
import numpy as np
import sys
import os
import argparse
import pandas as pd
from pathlib import Path

from input_guard import InputGuard, TopicGuard, adversarial_defense
from output_guard import OutputGuardAPI

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


def resolve_day18_path() -> Path:
    configured = os.getenv("DAY18_RAG_PATH")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend([PROJECT_DIR.parent / "day18-rag", PROJECT_DIR / "day18-rag"])
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if (resolved / "src" / "pipeline.py").exists():
            return resolved
    raise FileNotFoundError("Không tìm thấy day18-rag. Set DAY18_RAG_PATH trước khi chạy full_pipeline.py.")


def load_rag_core():
    sys.path.insert(0, str(resolve_day18_path()))
    from src.pipeline import build_pipeline, run_query

    return build_pipeline, run_query

ALLOWED_TOPICS = [
    "bảo vệ dữ liệu cá nhân", 
    "nghị định 13", 
    "xử lý dữ liệu", 
    "quyền chủ thể dữ liệu", 
    "vi phạm quy định dữ liệu",
    "chính sách bảo mật",
    "cơ quan chuyên trách bảo vệ dữ liệu cá nhân"
]

class FullStackPipeline:
    def __init__(self):
        print("Initializing Full Stack Pipeline...")
        self.input_guard = InputGuard()
        self.topic_guard = TopicGuard(ALLOWED_TOPICS)
        self.output_guard = OutputGuardAPI()
        
        print("Building RAG Core...")
        self.build_pipeline, self.run_query = load_rag_core()
        self.search, self.reranker = self.build_pipeline()
        
    async def process_query(self, query: str):
        timings = {}
        
        # 1. Input Guard (PII)
        sanitized_q, pii_lat = self.input_guard.sanitize(query)
        timings['L1'] = pii_lat
        
        # 2. Adversarial & Topic Check
        adv_safe, adv_reason = adversarial_defense(sanitized_q)
        if not adv_safe:
            return "Từ chối trả lời do phát hiện nội dung không phù hợp.", timings
            
        topic_start = time.perf_counter()
        is_on_topic, topic_reason = self.topic_guard.check(sanitized_q)
        timings['TopicCheck'] = (time.perf_counter() - topic_start) * 1000
        
        if not is_on_topic:
            return "Tôi không thể trả lời câu hỏi này vì nó nằm ngoài phạm vi tài liệu (Bảo vệ dữ liệu cá nhân - NĐ13).", timings
            
        # 3. RAG Core Pipeline
        rag_start = time.perf_counter()
        answer, contexts = self.run_query(sanitized_q, self.search, self.reranker)
        timings['L2'] = (time.perf_counter() - rag_start) * 1000
        
        # 4. Output Guard
        is_safe, out_reason, out_lat = self.output_guard.check(query, answer)
        timings['L3'] = out_lat
        
        if not is_safe:
            return "Hệ thống từ chối cung cấp câu trả lời do vi phạm chính sách an toàn đầu ra.", timings
            
        return answer, timings

async def run_benchmark(pipeline, num_requests=100):
    """Run latency benchmark on a sample question"""
    print(f"\n--- Running Latency Benchmark ({num_requests} requests) ---")
    query = "Nghị định 13 quy định quyền của chủ thể dữ liệu cá nhân gồm những gì?"
    
    all_latencies = []
    
    for i in range(num_requests):
        print(f"Request {i+1}/{num_requests}...")
        start = time.perf_counter()
        _, timings = await pipeline.process_query(query)
        total_lat = (time.perf_counter() - start) * 1000
        
        all_latencies.append({
            'total': total_lat,
            'L1': timings.get('L1', 0),
            'L2': timings.get('L2', 0),
            'L3': timings.get('L3', 0)
        })
        
    df = pd.DataFrame(all_latencies)
    df.to_csv(SCRIPT_DIR / "latency_benchmark.csv", index=False)
    
    print("\nBenchmark Results:")
    print(f"P50 Total Latency: {np.percentile(df['total'], 50):.2f}ms")
    print(f"P95 Total Latency: {np.percentile(df['total'], 95):.2f}ms")
    print(f"P99 Total Latency: {np.percentile(df['total'], 99):.2f}ms")
    print(f"Average L1 (PII) Latency: {df['L1'].mean():.2f}ms")
    print(f"Average L3 (Output Guard) Latency: {df['L3'].mean():.2f}ms")

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="Run one sample guarded query")
    parser.add_argument("--benchmark", action="store_true", help="Run latency benchmark")
    parser.add_argument("--requests", type=int, default=100, help="Number of benchmark requests")
    args = parser.parse_args()

    pipeline = FullStackPipeline()

    if args.sample or not args.benchmark:
        ans, t = asyncio.run(
            pipeline.process_query("Số điện thoại của tôi là 0912345678, quyền chủ thể dữ liệu là gì?")
        )
        print("\nSample Answer:", ans)
        print("Timings:", t)

    if args.benchmark:
        asyncio.run(run_benchmark(pipeline, args.requests))
