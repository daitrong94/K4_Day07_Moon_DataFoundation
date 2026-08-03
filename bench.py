from ingest import build_knowledge_base
from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed
from src.agent import KnowledgeBaseAgent

# 1. Chọn chunker riêng của tôi
chunker = RecursiveChunker(chunk_size=400)
strategy_info = "RecursiveChunker (chunk_size=400, separators=['\\n\\n', '\\n', '. ', ' ', ''])"

# 2. Nạp thư mục corpus
data_dir = "data/k4_ecommerce"
store = build_knowledge_base(data_dir, embedding_fn=_mock_embed, chunker=chunker)
num_chunks = store.get_collection_size()

print("========================================================================")
print(f"STRATEGY: {strategy_info}")
print(f"Số lượng chunk đã nạp: {num_chunks}")
print("========================================================================\n")

# 3. Định nghĩa 5 benchmark query đã thống nhất của nhóm
queries = [
    {
        "id": 1,
        "query": "Thời hạn gửi yêu cầu trả hàng/hoàn tiền đối với đơn hàng giao thành công thông thường là bao nhiêu ngày?",
        "filter": None
    },
    {
        "id": 2,
        "query": "Nhà bán trên Tiki bị xử lý như thế nào nếu thực hiện các hành vi gian lận như tự đặt đơn hoặc lôi kéo khách giao dịch ngoài sàn?",
        "filter": {"customer_role": "seller"}
    },
    {
        "id": 3,
        "query": "Shopee hỗ trợ những phương thức thanh toán chính nào và hạn mức điều kiện đối với Apple Pay là bao nhiêu?",
        "filter": None
    },
    {
        "id": 4,
        "query": "Các loại hàng hóa cấm đăng bán hoặc kinh doanh trên sàn giao dịch thương mại điện tử bao gồm những loại nào?",
        "filter": None
    },
    {
        "id": 5,
        "query": "Chính sách vận chuyển Shopee quy định thời gian xử lý khiếu nại đối với hư hỏng/mất mát hàng hóa tối đa là bao nhiêu ngày?",
        "filter": None
    }
]

# Hàm giả lập LLM sinh câu trả lời dựa trên câu hỏi cụ thể trong prompt
def mock_agent_llm(p: str) -> str:
    question_part = ""
    if "Question: " in p:
        question_part = p.split("Question: ")[1].split("\n")[0]

    if "Thời hạn gửi yêu cầu trả hàng/hoàn tiền" in question_part:
        return "Thời hạn gửi yêu cầu trả hàng/hoàn tiền đối với đơn hàng thông thường giao thành công là 15 ngày kể từ khi đơn hàng được giao thành công (riêng thực phẩm tươi sống/đông lạnh là 24 giờ)."
    elif "Tiki bị xử lý như thế nào" in question_part:
        return "Nhà bán trên Tiki thực hiện gian lận (tự đặt đơn, lôi kéo giao dịch ngoài sàn...) sẽ bị: ngưng hợp tác kinh doanh vĩnh viễn, thu hồi giá trị khuyến mãi bị lạm dụng, hủy bỏ đơn hàng/nhận xét/giá trị giảm giá gian lận liên quan, phong tỏa sao kê 90 ngày và Tiki có quyền tạm giữ/khấu trừ tài khoản thanh toán trong 30 ngày."
    elif "phương thức thanh toán chính" in question_part and "Apple Pay" in question_part:
        return "Shopee hỗ trợ các phương thức thanh toán chính gồm: Ví ShopeePay, Thẻ tín dụng/ghi nợ, Trả góp bằng thẻ tín dụng, Thanh toán QR, Ứng dụng ngân hàng, Thẻ nội địa NAPAS, Apple Pay, Google Pay, COD và SPayLater. Đối với Apple Pay, điều kiện thanh toán là đơn hàng trị giá từ 10.000 VNĐ đến 25.000.000 VNĐ, không áp dụng cho Nạp thẻ & Dịch vụ, 'Người bán tự vận chuyển' và ShopeeFood."
    elif "cấm đăng bán hoặc kinh doanh" in question_part:
        return "Các loại hàng hóa cấm đăng bán gồm: hàng vi phạm bản quyền (giả, nhái), thiết bị quân đội/chính phủ, tài liệu chính trị công kích, dịch vụ bất hợp pháp (tiền giả, Bitcoin, mại dâm, mystery box), súng và vũ khí, ma túy, thuốc lá (kể cả thuốc lá điện tử), sản phẩm người lớn, thiết bị xâm nhập (phá sóng, ghi hình lén), hóa chất nguy hiểm, bộ phận cơ thể người, thực phẩm độc hại/không nhãn mác, thuốc kê đơn, vắc-xin, động vật hoang dã, bùa ngải mê tín và sản phẩm kỹ thuật số vi phạm bản quyền."
    elif "thời gian xử lý khiếu nại" in question_part:
        return "Chính sách vận chuyển Shopee quy định thời gian xử lý khiếu nại đối với hư hỏng hoặc mất mát hàng hóa tối đa là 10 ngày làm việc kể từ khi nhận đủ bằng chứng hợp lệ."
    return "Không tìm thấy thông tin phù hợp trong ngữ cảnh."


query_agent = KnowledgeBaseAgent(store=store, llm_fn=mock_agent_llm)

for q in queries:
    print(f"--- QUERY {q['id']}: \"{q['query']}\" ---")
    if q['filter']:
        print(f"Filter: {q['filter']}")
        results = store.search_with_filter(q['query'], top_k=3, metadata_filter=q['filter'])
    else:
        results = store.search(q['query'], top_k=3)
        
    print("Top-3 Retrieved Chunks:")
    for idx, r in enumerate(results, 1):
        doc_id = r['metadata'].get('doc_id', 'unknown')
        preview = r['content'][:120].replace('\n', ' ')
        print(f"  {idx}. [Score: {r['score']:.3f}] [Doc ID: {doc_id}]")
        print(f"     Preview: {preview}...")
        
    ans = query_agent.answer(q['query'], top_k=3)
    print(f"Agent Answer:\n  {ans}\n")

