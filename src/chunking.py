from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Split on whitespace following . ! or ?
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        limit = self.max_sentences_per_chunk
        return [" ".join(sentences[i : i + limit]) for i in range(0, len(sentences), limit)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        raw_chunks = self._split(text, self.separators)
        cleaned_chunks = []
        for c in raw_chunks:
            stripped = c.strip()
            if stripped:
                cleaned_chunks.append(stripped)
        return cleaned_chunks

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        
        if not remaining_separators or remaining_separators[0] == "":
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i : i + self.chunk_size])
            return chunks
        
        separator = remaining_separators[0]
        # Split text by separator
        parts = current_text.split(separator)
        
        # Merge parts back together using the separator
        docs = []
        current_doc = []
        total = 0
        for s in parts:
            # We want to check if adding s exceeds the chunk size
            sep_len = len(separator) if current_doc else 0
            if total + len(s) + sep_len > self.chunk_size:
                if total > 0:
                    docs.append(separator.join(current_doc))
                    current_doc = []
                    total = 0
                if len(s) > self.chunk_size:
                    # Recursive split s with next separators
                    sub_splits = self._split(s, remaining_separators[1:])
                    docs.extend(sub_splits)
                else:
                    current_doc.append(s)
                    total = len(s)
            else:
                current_doc.append(s)
                total += len(s) + sep_len
        
        if current_doc:
            docs.append(separator.join(current_doc))
            
        return docs


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_size_chunker = FixedSizeChunker(chunk_size=chunk_size)
        sentence_chunker = SentenceChunker()
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)
        
        results = {}
        for key, chunker in [
            ('fixed_size', fixed_size_chunker),
            ('by_sentences', sentence_chunker),
            ('recursive', recursive_chunker)
        ]:
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            results[key] = {
                'count': count,
                'avg_length': avg_length,
                'chunks': chunks
            }
        return results

