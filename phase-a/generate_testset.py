import os
from pathlib import Path

import pandas as pd
import nest_asyncio
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Ragas 0.1.21 imports
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context
from ragas.run_config import RunConfig


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


def resolve_day18_data_path() -> Path:
    configured = os.getenv("DAY18_RAG_PATH")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        [
            PROJECT_DIR.parent / "day18-rag",
            PROJECT_DIR / "day18-rag",
            Path.cwd().parent / "day18-rag",
        ]
    )
    for candidate in candidates:
        data_path = candidate.expanduser().resolve() / "data"
        if data_path.exists():
            return data_path
    raise FileNotFoundError("Không tìm thấy thư mục data của day18-rag. Set DAY18_RAG_PATH trước khi chạy.")

def main():
    # Allow nested asyncio loops for Jupyter or similar environments
    nest_asyncio.apply()
    
    # Load environment variables (ensure OPENAI_API_KEY is set)
    load_dotenv()
    
    # Check if OPENAI_API_KEY is available
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set in the environment or .env file")

    print("Loading documents...")
    loader = DirectoryLoader(str(resolve_day18_data_path()), glob="**/*.md")
    documents = loader.load()
    print(f"Loaded {len(documents)} documents.")

    print("Initializing TestsetGenerator...")
    # Setup the generator and critic LLMs, and embeddings
    generator_llm = ChatOpenAI(model="gpt-4o-mini")
    critic_llm = ChatOpenAI(model="gpt-4o-mini")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    generator = TestsetGenerator.from_langchain(
        generator_llm=generator_llm,
        critic_llm=critic_llm,
        embeddings=embeddings
    )
    
    # Configure RunConfig to prevent rate limits (max_workers=1 to process slowly)
    run_config = RunConfig(max_workers=1, max_retries=15, max_wait=90)

    print("Generating testset of 50 questions...")
    # Generate the testset
    testset = generator.generate_with_langchain_docs(
        documents,
        test_size=50,
        distributions={
            simple: 0.5,
            reasoning: 0.25,
            multi_context: 0.25
        },
        run_config=run_config
    )

    print("Saving testset to testset_v1.csv...")
    # Convert to pandas DataFrame and save
    df = testset.to_pandas()
    df.to_csv(SCRIPT_DIR / "testset_v1.csv", index=False)
    
    print("Done! Testset saved to testset_v1.csv")

if __name__ == "__main__":
    main()
