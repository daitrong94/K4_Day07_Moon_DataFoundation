"""K4 strategy: structure-aware chunking + contextual prefixes for policy pages.

Two ideas, both aimed at the same failure mode. A returns policy is a list of
short, self-contained clauses ("2.1 Thời gian đổi trả", "A. QUYỀN LỢI"), so a
fixed-size window cuts a fee away from the product category it applies to, and
a sentence window merges the tail of one clause with the head of the next.

1. ``PolicySectionChunker`` splits on clause headings instead of on characters,
   so one chunk is one clause. Undersized clauses are merged with the following
   one; oversized clauses fall back to RecursiveChunker.

2. ``contextual_chunk_document`` prepends a short header carrying the document
   title, category and customer_role to every chunk *before* it is embedded.
   Anthropic's contextual retrieval reports a 35% drop in retrieval failures
   from this alone: a chunk that reads "trừ phí 20%" out of context becomes
   "[Chính sách đổi trả | returns | buyer] ... trừ phí 20%".
"""
from __future__ import annotations

import re

from .chunking import RecursiveChunker
from .models import Document

# A heading is a markdown heading, a numbered clause (1. / 2.1 / 2.3.1.),
# a lettered clause (A. / b) ), or a short shouted line used as a banner.
HEADING = re.compile(
    r"""^\s*(
        \#{1,6}\s+\S               # markdown heading
      | \d+(\.\d+)*\.?\s+\S        # 1.  2.1  2.3.1.
      | [A-ZĐ][.)]\s*\S            # A.  B)
    )""",
    re.VERBOSE,
)
SHOUTED = re.compile(r"^[^a-zà-ỹ]{8,80}$")  # ALL-CAPS banner, no lowercase letters

DEFAULT_CONTEXT_FIELDS = ("title", "category", "customer_role")


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return bool(HEADING.match(stripped) or SHOUTED.match(stripped))


class PolicySectionChunker:
    """Split policy text on clause headings, keeping each clause intact.

    Args:
        chunk_size: soft ceiling; a section longer than this is split further.
        min_chunk_size: sections shorter than this are merged with the next one,
            which stops a bare heading from becoming its own useless chunk.
    """

    def __init__(self, chunk_size: int = 500, min_chunk_size: int = 120) -> None:
        self.chunk_size = chunk_size
        self.min_chunk_size = min_chunk_size
        self._fallback = RecursiveChunker(chunk_size=chunk_size)

    def _sections(self, text: str) -> list[str]:
        sections: list[str] = []
        current: list[str] = []
        for line in text.splitlines():
            if _is_heading(line) and current:
                sections.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            sections.append("\n".join(current).strip())
        return [section for section in sections if section]

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        chunks: list[str] = []
        pending = ""
        for section in self._sections(text):
            merged = f"{pending}\n{section}".strip() if pending else section
            if len(merged) < self.min_chunk_size:
                pending = merged           # too small to stand alone: keep growing
                continue
            pending = ""
            if len(merged) > self.chunk_size:
                chunks.extend(self._fallback.chunk(merged))
            else:
                chunks.append(merged)
        if pending:
            chunks.append(pending)
        return chunks


def build_context_prefix(metadata: dict, fields: tuple[str, ...] = DEFAULT_CONTEXT_FIELDS) -> str:
    """Render the metadata header that is prepended to each chunk."""
    values = [str(metadata[field]) for field in fields if metadata.get(field)]
    return f"[{' | '.join(values)}]" if values else ""


def contextual_chunk_document(
    doc: Document,
    chunker,
    fields: tuple[str, ...] = DEFAULT_CONTEXT_FIELDS,
) -> list[Document]:
    """Chunk a document and prepend its metadata context to every chunk.

    Mirrors ``ingest.chunk_document`` so it can be swapped into
    ``build_knowledge_base``; the only difference is the prefix that makes each
    chunk self-describing to the embedding model.
    """
    prefix = build_context_prefix(doc.metadata, fields)
    chunk_docs: list[Document] = []
    for index, piece in enumerate(chunker.chunk(doc.content)):
        chunk_meta = dict(doc.metadata)
        chunk_meta["doc_id"] = doc.id
        chunk_meta["chunk_index"] = index
        chunk_meta["has_context_prefix"] = bool(prefix)
        content = f"{prefix}\n{piece}" if prefix else piece
        chunk_docs.append(
            Document(id=f"{doc.id}::chunk_{index}", content=content, metadata=chunk_meta)
        )
    return chunk_docs
