"""
Module 1: Advanced Chunking Strategies
======================================
Implement semantic, hierarchical, and structure-aware chunking.
Compare with basic chunking baseline.

Test: pytest tests/test_m1.py
"""

import glob
import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (  # noqa: E402
    DATA_DIR,
    HIERARCHICAL_CHILD_SIZE,
    HIERARCHICAL_PARENT_SIZE,
    SEMANTIC_THRESHOLD,
)


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    parent_id: str | None = None


def load_documents(data_dir: str = DATA_DIR) -> list[dict]:
    """Load all markdown files from data/."""
    docs = []
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(fp, encoding="utf-8") as f:
            docs.append({"text": f.read(), "metadata": {"source": os.path.basename(fp)}})
    return docs


def _split_sentences(text: str) -> list[str]:
    """Split text into sentence-like units without external dependencies."""
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n\s*\n+", text)
    return [part.strip() for part in parts if part.strip()]


def _tokenize(text: str) -> list[str]:
    """Tokenize Unicode words for lightweight cosine similarity."""
    return re.findall(r"[\w]+", text.lower(), flags=re.UNICODE)


def _cosine_sim(a: Counter, b: Counter) -> float:
    """Cosine similarity between sparse token-count vectors."""
    if not a or not b:
        return 0.0
    dot = sum(a[token] * b[token] for token in set(a) & set(b))
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _split_text_windows(text: str, size: int, overlap: int = 0) -> list[str]:
    """Split text into character windows, preferring whitespace boundaries."""
    text = text.strip()
    if not text:
        return []
    if size <= 0 or len(text) <= size:
        return [text]

    chunks = []
    start = 0
    overlap = max(0, min(overlap, size // 2))
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start + size * 0.6:
                end = boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks


def _stats(chunks: list[Chunk]) -> dict:
    lengths = [len(chunk.text) for chunk in chunks]
    if not lengths:
        return {"num_chunks": 0, "avg_length": 0, "min_length": 0, "max_length": 0}
    return {
        "num_chunks": len(chunks),
        "avg_length": round(sum(lengths) / len(lengths), 2),
        "min_length": min(lengths),
        "max_length": max(lengths),
    }


def chunk_basic(text: str, chunk_size: int = 500, metadata: dict | None = None) -> list[Chunk]:
    """
    Basic chunking: split by paragraphs.
    This is the baseline used for comparison.
    """
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) > chunk_size and current:
            chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
            current = ""
        current += para + "\n\n"
    if current.strip():
        chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
    return chunks


def chunk_semantic(
    text: str,
    threshold: float = SEMANTIC_THRESHOLD,
    metadata: dict | None = None,
) -> list[Chunk]:
    """
    Group neighboring sentences by cosine similarity.

    The lab description suggests sentence-transformers. This implementation keeps
    the same idea but uses a dependency-free lexical vector fallback so tests and
    local runs work even when model downloads are unavailable.
    """
    metadata = metadata or {}
    sentences = _split_sentences(text)
    if not sentences:
        return []

    vectors = [Counter(_tokenize(sentence)) for sentence in sentences]
    chunks: list[Chunk] = []
    current_group = [sentences[0]]

    for i in range(1, len(sentences)):
        sim = _cosine_sim(vectors[i - 1], vectors[i])
        current_text = " ".join(current_group)

        # Headings/short intro fragments should stay attached to their content.
        if sim < threshold and len(current_text) >= 120:
            chunks.append(Chunk(
                text=current_text.strip(),
                metadata={**metadata, "chunk_index": len(chunks), "strategy": "semantic"},
            ))
            current_group = []
        current_group.append(sentences[i])

    if current_group:
        chunks.append(Chunk(
            text=" ".join(current_group).strip(),
            metadata={**metadata, "chunk_index": len(chunks), "strategy": "semantic"},
        ))

    return chunks


def chunk_hierarchical(
    text: str,
    parent_size: int = HIERARCHICAL_PARENT_SIZE,
    child_size: int = HIERARCHICAL_CHILD_SIZE,
    metadata: dict | None = None,
) -> tuple[list[Chunk], list[Chunk]]:
    """
    Build parent-child chunks.

    Production pattern: index small child chunks for precise retrieval, then use
    parent_id to recover the larger parent chunk as LLM context.
    """
    metadata = metadata or {}
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    if not paragraphs:
        return [], []

    parents: list[Chunk] = []
    children: list[Chunk] = []
    current: list[str] = []
    current_len = 0
    source = metadata.get("source", "doc")

    def flush_parent() -> None:
        if not current:
            return
        parent_text = "\n\n".join(current).strip()
        parent_index = len(parents)
        parent_id = f"{source}_parent_{parent_index}"
        parents.append(Chunk(
            text=parent_text,
            metadata={
                **metadata,
                "chunk_index": parent_index,
                "chunk_type": "parent",
                "parent_id": parent_id,
                "strategy": "hierarchical",
            },
            parent_id=parent_id,
        ))

    for para in paragraphs:
        projected_len = current_len + len(para) + (2 if current else 0)
        if current and projected_len > parent_size:
            flush_parent()
            current = []
            current_len = 0
        current.append(para)
        current_len += len(para) + (2 if current_len else 0)

    flush_parent()

    child_overlap = max(0, min(child_size // 5, 80))
    for parent in parents:
        pid = parent.metadata["parent_id"]
        for child_text in _split_text_windows(parent.text, child_size, overlap=child_overlap):
            children.append(Chunk(
                text=child_text,
                metadata={
                    **metadata,
                    "chunk_index": len(children),
                    "chunk_type": "child",
                    "parent_id": pid,
                    "strategy": "hierarchical",
                },
                parent_id=pid,
            ))

    return parents, children


def chunk_structure_aware(text: str, metadata: dict | None = None) -> list[Chunk]:
    """
    Parse markdown headers and return complete logical sections.

    Tables, lists, and code blocks remain inside their section because the split
    only happens on markdown heading lines outside fenced code blocks.
    """
    metadata = metadata or {}
    chunks: list[Chunk] = []
    current_lines: list[str] = []
    current_header = ""
    current_level: int | None = None
    in_code_block = False

    def flush_section() -> None:
        section_text = "\n".join(current_lines).strip()
        if not section_text:
            return
        chunks.append(Chunk(
            text=section_text,
            metadata={
                **metadata,
                "chunk_index": len(chunks),
                "section": current_header,
                "section_level": current_level,
                "strategy": "structure",
            },
        ))

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block

        header_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if header_match and not in_code_block:
            flush_section()
            current_lines = [line]
            current_header = header_match.group(2).strip()
            current_level = len(header_match.group(1))
        else:
            current_lines.append(line)

    flush_section()
    if chunks:
        return chunks

    stripped_text = text.strip()
    if not stripped_text:
        return []
    return [Chunk(
        text=stripped_text,
        metadata={
            **metadata,
            "chunk_index": 0,
            "section": "",
            "section_level": None,
            "strategy": "structure",
        },
    )]


def compare_strategies(documents: list[dict]) -> dict:
    """
    Run all strategies on documents and return comparison statistics.

    Returns:
        {"basic": {...}, "semantic": {...}, "hierarchical": {...}, "structure": {...}}
    """
    all_basic: list[Chunk] = []
    all_semantic: list[Chunk] = []
    all_parents: list[Chunk] = []
    all_children: list[Chunk] = []
    all_structure: list[Chunk] = []

    for doc in documents:
        text = doc.get("text", "")
        metadata = doc.get("metadata", {})

        all_basic.extend(chunk_basic(text, metadata=metadata))
        all_semantic.extend(chunk_semantic(text, metadata=metadata))

        parents, children = chunk_hierarchical(text, metadata=metadata)
        all_parents.extend(parents)
        all_children.extend(children)

        all_structure.extend(chunk_structure_aware(text, metadata=metadata))

    results = {
        "basic": _stats(all_basic),
        "semantic": _stats(all_semantic),
        "hierarchical": {
            **_stats(all_children),
            "num_parents": len(all_parents),
            "num_children": len(all_children),
        },
        "structure": _stats(all_structure),
    }

    print("\nStrategy      | Chunks     | Avg Len | Min | Max")
    print("-" * 52)
    for name in ["basic", "semantic", "hierarchical", "structure"]:
        stats = results[name]
        chunk_label = (
            f"{stats['num_parents']}p/{stats['num_children']}c"
            if name == "hierarchical"
            else str(stats["num_chunks"])
        )
        print(
            f"{name:<13} | {chunk_label:>10} | "
            f"{stats['avg_length']:>7} | {stats['min_length']:>3} | {stats['max_length']:>3}"
        )

    return results


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")
    results = compare_strategies(docs)
    for name, stats in results.items():
        print(f"  {name}: {stats}")
