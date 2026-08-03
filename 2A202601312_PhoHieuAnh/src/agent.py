from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    NO_CONTEXT = "(không truy xuất được tài liệu liên quan)"

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def _build_context(self, results: list[dict]) -> str:
        if not results:
            return self.NO_CONTEXT

        blocks = []
        for rank, result in enumerate(results, start=1):
            source = result["metadata"].get("doc_id") or result["metadata"].get("source", "unknown")
            blocks.append(f"[{rank}] nguồn={source} score={result['score']:.3f}\n{result['content']}")
        return "\n\n".join(blocks)

    def build_prompt(self, question: str, context: str) -> str:
        return (
            "Bạn là trợ lý trả lời dựa trên tài liệu được cung cấp.\n"
            "Chỉ dùng thông tin trong NGỮ CẢNH. Nếu ngữ cảnh không đủ, hãy nói rõ là không đủ dữ liệu.\n"
            "Trích dẫn số hiệu đoạn [n] cho mỗi ý bạn đưa ra.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI:"
        )

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        prompt = self.build_prompt(question, self._build_context(results))
        return self.llm_fn(prompt)
