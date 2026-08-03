#!/usr/bin/env python3
"""Run the 5 K4 benchmark queries across chunking strategies and score retrieval.

Reports the metrics docs/EVALUATION.md asks for, under their standard IR names:

    Hit@3       câu hỏi có ít nhất một chunk từ tài liệu gold trong top-3
    MRR@3       1/thứ hạng của chunk gold đầu tiên (thưởng cho việc xếp gold lên top-1)
    Grounded@3  top-3 có chunk chứa đúng dữ kiện của gold answer (không chỉ đúng tài liệu)

Hit@3 chấm việc tìm đúng TÀI LIỆU; Grounded@3 chấm việc tìm đúng ĐOẠN chứa số liệu —
một chiến lược có thể luôn đúng tài liệu mà vẫn cắt mất con số cần trả lời.

Usage:
    EMBEDDING_PROVIDER=local .venv/bin/python scripts/run_benchmark.py
    .venv/bin/python scripts/run_benchmark.py --data-dir data/k4_ecommerce
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import chunk_document, load_documents  # noqa: E402
from main import _select_embedder  # noqa: E402
from src import (  # noqa: E402
    EmbeddingStore,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    PolicySectionChunker,
    RecursiveChunker,
    HybridStore,
    SentenceChunker,
    contextual_chunk_document,
)

TOP_K = 3

# (chunker, có gắn tiền tố ngữ cảnh?, có bật hybrid BM25+RRF?)
STRATEGIES = {
    "fixed_500_50": (FixedSizeChunker(chunk_size=500, overlap=50), False, False),
    "sentences_3": (SentenceChunker(max_sentences_per_chunk=3), False, False),
    "recursive_500": (RecursiveChunker(chunk_size=500), False, False),
    "policy_sections": (PolicySectionChunker(chunk_size=500), False, False),
    "policy_contextual": (PolicySectionChunker(chunk_size=500), True, False),
    "policy_contextual_hybrid": (PolicySectionChunker(chunk_size=500), True, True),
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def build_store(data_dir: Path, chunker, contextual: bool, embedding_fn, hybrid: bool = False):
    builder = contextual_chunk_document if contextual else chunk_document
    chunk_docs = []
    for doc in load_documents(data_dir):
        chunk_docs.extend(builder(doc, chunker))
    store = EmbeddingStore(collection_name="benchmark", embedding_fn=embedding_fn)
    if hybrid:
        store = HybridStore(store)
    store.add_documents(chunk_docs)
    return store


def score_query(store: EmbeddingStore, query: dict, use_filter: bool = True) -> dict:
    metadata_filter = query.get("metadata_filter") if use_filter else None
    results = store.search_with_filter(query["query"], top_k=TOP_K, metadata_filter=metadata_filter)

    gold_docs = set(query["gold_doc_ids"])
    keywords = [normalize(k) for k in query["gold_keywords"]]

    reciprocal_rank = 0.0
    for rank, result in enumerate(results, start=1):
        if result["metadata"].get("doc_id") in gold_docs:
            reciprocal_rank = 1.0 / rank
            break

    grounded = any(
        any(keyword in normalize(result["content"]) for keyword in keywords) for result in results
    )
    return {
        "hit": 1.0 if reciprocal_rank else 0.0,
        "mrr": reciprocal_rank,
        "grounded": 1.0 if grounded else 0.0,
        "results": results,
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/k4_ecommerce"))
    parser.add_argument("--benchmark", type=Path, default=None)
    parser.add_argument("--show-top", action="store_true", help="print top-3 chunks per query")
    args = parser.parse_args()

    benchmark_path = args.benchmark or args.data_dir / "benchmark.json"
    queries = json.loads(benchmark_path.read_text(encoding="utf-8"))["queries"]

    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Embedding backend: {backend}")
    print(f"Corpus: {args.data_dir}  |  {len(load_documents(args.data_dir))} tài liệu  |  {len(queries)} query\n")

    stores: dict[str, EmbeddingStore] = {}
    print("## Chiến lược chia nhỏ\n")
    print("| Chiến lược | Số chunk | Độ dài TB |")
    print("|---|---:|---:|")
    for name, (chunker, contextual, hybrid) in STRATEGIES.items():
        store = build_store(args.data_dir, chunker, contextual, embedder, hybrid)
        stores[name] = store
        records = store._records if hasattr(store, "_records") else store._store
        lengths = [len(record["content"]) for record in records]
        print(f"| `{name}` | {len(lengths)} | {mean([float(x) for x in lengths]):.0f} |")

    print("\n## Chất lượng truy xuất (top-3)\n")
    print("| Chiến lược | Hit@3 | MRR@3 | Grounded@3 |")
    print("|---|---:|---:|---:|")
    per_strategy: dict[str, list[dict]] = {}
    for name, store in stores.items():
        scored = [score_query(store, query) for query in queries]
        per_strategy[name] = scored
        print(
            f"| `{name}` | {mean([s['hit'] for s in scored]):.2f} "
            f"| {mean([s['mrr'] for s in scored]):.2f} "
            f"| {mean([s['grounded'] for s in scored]):.2f} |"
        )

    best = max(per_strategy, key=lambda n: (mean([s["grounded"] for s in per_strategy[n]]),
                                            mean([s["mrr"] for s in per_strategy[n]])))
    print(f"\n**Chiến lược tốt nhất: `{best}`**\n")

    print("## Từng câu hỏi (chiến lược tốt nhất)\n")
    print("| # | Câu hỏi | Top-1 doc_id | Score | Hit@3 | Grounded@3 |")
    print("|---|---|---|---:|:---:|:---:|")
    for query, scored in zip(queries, per_strategy[best]):
        results = scored["results"]
        top = results[0]["metadata"].get("doc_id") if results else "—"
        score = f"{results[0]['score']:.3f}" if results else "—"
        print(
            f"| {query['id']} | {query['query'][:52]} | `{top}` | {score} "
            f"| {'✅' if scored['hit'] else '❌'} | {'✅' if scored['grounded'] else '❌'} |"
        )

    filtered_queries = [q for q in queries if q.get("metadata_filter")]
    if filtered_queries:
        print("\n## A/B: lọc metadata (Metadata Utility)\n")
        print("Chạy trên MỌI chiến lược: nếu lọc chỉ giúp các chiến lược yếu thì lợi ích của")
        print("metadata thực chất là bù cho chunking kém, chứ không phải lợi ích độc lập.\n")
        print("| Chiến lược | # | Có lọc: Hit@3 / MRR@3 | Không lọc: Hit@3 / MRR@3 |")
        print("|---|---|:---:|:---:|")
        for name, store in stores.items():
            for query in filtered_queries:
                with_filter = score_query(store, query, use_filter=True)
                without = score_query(store, query, use_filter=False)
                print(
                    f"| `{name}` | {query['id']} "
                    f"| {with_filter['hit']:.0f} / {with_filter['mrr']:.2f} "
                    f"| {without['hit']:.0f} / {without['mrr']:.2f} |"
                )

    if args.show_top:
        print("\n## Top-3 chunk chi tiết (chiến lược tốt nhất)\n")
        for query, scored in zip(queries, per_strategy[best]):
            print(f"### Q{query['id']}: {query['query']}")
            print(f"*Gold:* {query['gold_answer']}\n")
            for rank, result in enumerate(scored["results"], start=1):
                preview = normalize(result["content"])[:220]
                print(f"{rank}. `{result['metadata'].get('doc_id')}` score={result['score']:.3f}\n   {preview}...")
            print()

    agent = KnowledgeBaseAgent(store=stores[best], llm_fn=lambda prompt: prompt)
    print(f"\n_Prompt của agent dài {len(agent.answer(queries[0]['query']))} ký tự cho query 1._")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
