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

        # Tách câu theo . ! ? hoặc xuống dòng sau dấu câu
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())

        # Loại bỏ câu rỗng và khoảng trắng thừa
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: list[str] = []

        # Gom tối đa max_sentences_per_chunk câu vào một chunk
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(group).strip())

        return chunks
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

        return self._split(text.strip(), self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Nếu đoạn đã đủ ngắn thì trả về luôn
        if len(current_text) <= self.chunk_size:
            return [current_text.strip()] if current_text.strip() else []

        # Hết separator thì cắt cứng theo chunk_size
        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size].strip()
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i : i + self.chunk_size].strip()
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Separator rỗng = cắt cứng
        if separator == "":
            return [
                current_text[i : i + self.chunk_size].strip()
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i : i + self.chunk_size].strip()
            ]

        parts = current_text.split(separator)

        chunks: list[str] = []
        buffer = ""

        for part in parts:
            candidate = part if not buffer else buffer + separator + part

            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    chunks.extend(self._split(buffer, next_separators))
                buffer = part

        if buffer:
            chunks.extend(self._split(buffer, next_separators))

        return chunks

def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """

    # Tính độ dài (magnitude) của từng vector
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    # Nếu một vector có độ dài bằng 0 thì không thể tính cosine
    if norm_a == 0 or norm_b == 0:
        return 0.0

    # Công thức cosine similarity
    return _dot(vec_a, vec_b) / (norm_a * norm_b)

class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        result: dict = {}

        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            lengths = [len(c) for c in chunks]

            result[name] = {
                "count": len(chunks),
                "num_chunks": len(chunks),
                "avg_length": sum(lengths) / len(lengths) if lengths else 0,
                "max_length": max(lengths) if lengths else 0,
                "min_length": min(lengths) if lengths else 0,
                "chunks": chunks,
            }

        return result

