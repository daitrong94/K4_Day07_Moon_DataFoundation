from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import SentenceChunker, FixedSizeChunker, RecursiveChunker
from src.embeddings import LocalEmbedder, MockEmbedder, OpenAIEmbedder, EMBEDDING_PROVIDER_ENV


def get_embedder():
    """Chọn embedder theo biến môi trường EMBEDDING_PROVIDER."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder()
        except Exception as e:
            print(f"Warning: Could not load LocalEmbedder ({e}). Falling back to MockEmbedder.")
            return MockEmbedder()
    elif provider == "openai":
        try:
            return OpenAIEmbedder()
        except Exception as e:
            print(f"Warning: Could not load OpenAIEmbedder ({e}). Falling back to MockEmbedder.")
            return MockEmbedder()
    return MockEmbedder()


BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Thời hạn gửi yêu cầu trả hàng/hoàn tiền đối với đơn hàng giao thành công thông thường là bao nhiêu ngày?",
        "gold_answer": "15 ngày kể từ khi đơn hàng được giao thành công (riêng thực phẩm tươi sống/đông lạnh là 24 giờ).",
        "target_doc_id": "shopee-return-refund-policy",
        "metadata_filter": None,
    },
    {
        "id": 2,
        "query": "Nhà bán trên Tiki bị xử lý như thế nào nếu thực hiện các hành vi gian lận như tự đặt đơn hoặc lôi kéo khách giao dịch ngoài sàn?",
        "gold_answer": "Nhà Bán bị ngưng hợp tác kinh doanh vĩnh viễn, thu hồi giá trị khuyến mãi lạm dụng, hủy đơn/nhận xét gian lận, và phong tỏa sao kê trong 90 ngày.",
        "target_doc_id": "tiki-seller-rights-obligations",
        "metadata_filter": {"customer_role": "seller"},
    },
    {
        "id": 3,
        "query": "Shopee hỗ trợ những phương thức thanh toán chính nào và hạn mức điều kiện đối với Apple Pay là bao nhiêu?",
        "gold_answer": "Shopee hỗ trợ 9 hình thức thanh toán chính. Đối với Apple Pay, hạn mức giao dịch quy định từ 10.000 VNĐ đến 25.000.000 VNĐ.",
        "target_doc_id": "shopee-payment-methods",
        "metadata_filter": {"customer_role": "buyer"},
    },
    {
        "id": 4,
        "query": "Các loại hàng hóa cấm đăng bán hoặc kinh doanh trên sàn giao dịch thương mại điện tử bao gồm những loại nào?",
        "gold_answer": "Bao gồm vũ khí, chất cháy nổ, hàng giả/hàng nhái, ma túy/chất kích thích, động vật hoang dã, thuốc lá/thuốc lá điện tử, và hàng hóa bị cấm theo quy định pháp luật.",
        "target_doc_id": "k4-prohibited-products",
        "metadata_filter": None,
    },
    {
        "id": 5,
        "query": "Chính sách vận chuyển Shopee quy định thời gian xử lý khiếu nại đối với hư hỏng/mất mát hàng hóa tối đa là bao nhiêu ngày?",
        "gold_answer": "Thời gian xử lý khiếu nại tối đa là 10 ngày làm việc kể từ khi nhận đủ thông tin và bằng chứng hợp lệ.",
        "target_doc_id": "shopee-shipping-policy",
        "metadata_filter": None,
    },
]


def run_benchmark(data_dir: str = "data/k4_ecommerce"):
    embedder = get_embedder()
    embedder_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print("=" * 80)
    print("K4 E-COMMERCE RETRIEVAL BENCHMARK RUNNER")
    print("=" * 80)
    print(f"Data Directory : {data_dir}")
    print(f"Embedding Model: {embedder_name}")
    print("-" * 80)

    # Build Knowledge Base
    store = build_knowledge_base(data_dir, embedding_fn=embedder)
    print(f"Successfully loaded {store.get_collection_size()} chunks into EmbeddingStore.\n")

    def simple_llm(prompt: str) -> str:
        lines = prompt.splitlines()
        context_lines = [l for l in lines if l.startswith("[")]
        if context_lines:
            return f"[Gold Grounded Answer] dựa trên chunk truy xuất được: {context_lines[0][:150]}..."
        return "Không đủ thông tin trong ngữ cảnh được cung cấp."

    agent = KnowledgeBaseAgent(store=store, llm_fn=simple_llm)

    total_queries = len(BENCHMARK_QUERIES)
    hit_top1 = 0
    hit_top3 = 0

    print("BENCHMARK EVALUATION RESULTS:")
    print("=" * 80)

    for item in BENCHMARK_QUERIES:
        q_id = item["id"]
        query = item["query"]
        gold_ans = item["gold_answer"]
        target_doc = item["target_doc_id"]
        meta_filter = item["metadata_filter"]

        if meta_filter:
            results = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter)
        else:
            results = store.search(query, top_k=3)

        retrieved_doc_ids = [r["metadata"].get("doc_id") for r in results]
        
        is_top1 = len(retrieved_doc_ids) > 0 and retrieved_doc_ids[0] == target_doc
        is_top3 = target_doc in retrieved_doc_ids

        if is_top1:
            hit_top1 += 1
        if is_top3:
            hit_top3 += 1

        top1_content = results[0]["content"] if results else "N/A"
        top1_score = results[0]["score"] if results else 0.0
        agent_resp = agent.answer(query, top_k=3)

        print(f"Query #{q_id}: {query}")
        if meta_filter:
            print(f"  [Filter Applied]: {meta_filter}")
        print(f"  Gold Answer     : {gold_ans}")
        print(f"  Target Doc ID   : {target_doc}")
        print(f"  Top-1 Score     : {top1_score:.4f}")
        print(f"  Top-1 Doc ID    : {retrieved_doc_ids[0] if retrieved_doc_ids else 'None'}")
        print(f"  Top-1 Content   : {top1_content[:120].replace(chr(10), ' ')}...")
        print(f"  Agent Answer    : {agent_resp}")
        print(f"  Hit@1 Status    : {'PASSED [YES]' if is_top1 else 'NO'}")
        print(f"  Hit@3 Status    : {'PASSED [YES]' if is_top3 else 'NO'}")
        print("-" * 80)

    print("SUMMARY STATS:")
    print(f"  Total Benchmark Queries: {total_queries}")
    print(f"  Hit@1 Accuracy          : {hit_top1}/{total_queries} ({hit_top1/total_queries*100:.1f}%)")
    print(f"  Hit@3 Accuracy          : {hit_top3}/{total_queries} ({hit_top3/total_queries*100:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    data_directory = sys.argv[1] if len(sys.argv) > 1 else "data/k4_ecommerce"
    run_benchmark(data_dir=data_directory)
