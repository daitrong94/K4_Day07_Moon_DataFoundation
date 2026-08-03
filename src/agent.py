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
        # 1. Retrieve relevant chunks
        results = self.store.search(question, top_k=top_k)

        # 2. Handle empty retrieval
        if not results:
            return (
                "I do not have enough information in the knowledge base "
                "to answer this question."
            )

        # 3. Build context from retrieved chunks
        context_parts: list[str] = []

        for i, item in enumerate(results, start=1):
            context_parts.append(f"[{i}] {item['content']}")

        context = "\n\n".join(context_parts)

        # 4. Construct RAG prompt
        prompt = (
            "Answer the question using ONLY the provided context.\n"
            "If the answer is not contained in the context, say that you do not know.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        # 5. Generate answer with provided LLM function
        return self.llm_fn(prompt)