from __future__ import annotations

import hashlib
import math

# Multilingual model suitable for the Vietnamese corpora used in this Lab.
# The local backend remains optional; required checkpoints use MockEmbedder.
LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    """Deterministic embedding backend used by tests and default classroom runs."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vector = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class LocalEmbedder:
    """Sentence Transformers-backed local embedder.

    ``trust_remote_code`` makes transformers download and execute modelling code
    from the model repository. Some strong multilingual checkpoints (e.g.
    Alibaba-NLP/gte-multilingual-base) refuse to load without it, so it is
    exposed here — but it defaults to False and must be opted into explicitly
    via LOCAL_TRUST_REMOTE_CODE=1, because it means running third-party code.
    """

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL, trust_remote_code: bool | None = None) -> None:
        import os

        from sentence_transformers import SentenceTransformer

        if trust_remote_code is None:
            trust_remote_code = os.getenv("LOCAL_TRUST_REMOTE_CODE", "").strip().lower() in {"1", "true", "yes"}

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name, trust_remote_code=trust_remote_code)

    def __call__(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(value) for value in embedding]


class OpenAIEmbedder:
    """OpenAI embeddings API-backed embedder."""

    def __init__(self, model_name: str = OPENAI_EMBEDDING_MODEL) -> None:
        from openai import OpenAI

        self.model_name = model_name
        self._backend_name = model_name
        self.client = OpenAI()

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return [float(value) for value in response.data[0].embedding]


_mock_embed = MockEmbedder()
