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

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "I don't have any documents in my knowledge base to answer this question."

        context_parts = []
        for i, r in enumerate(results, 1):
            doc_id = r["metadata"].get("doc_id", "unknown")
            context_parts.append(f"[{i}] {r['content']} (Source: {doc_id})")
        context = "\n".join(context_parts)

        prompt = (
            "Instruction: Answer the question using only the provided context. "
            "If the context does not contain the answer, say that you do not know.\n"
            f"Context:\n{context}\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)

