# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Tuấn Anh  
**Nhóm:** [Tên nhóm]  
**Ngày:** 08/03/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding hướng về cùng một phía trong không gian vector đa chiều, thể hiện hai đoạn văn bản tương đồng cao về mặt ý nghĩa/ngữ nghĩa bất kể độ dài ngắn khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Hệ thống hỗ trợ thanh toán qua thẻ ngân hàng và ví điện tử."
- Câu B: "Khách hàng có thể dùng thẻ ATM hoặc ví điện tử để thanh toán đơn hàng."
- Tại sao tương đồng: Cả hai câu đều cung cấp thông tin về cùng các phương thức thanh toán áp dụng (thẻ & ví điện tử).

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Thời gian xử lý yêu cầu đổi trả hàng là 3 ngày làm việc."
- Câu B: "Thuật toán học máy sử dụng mạng nơ-ron đa tầng để dự báo."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn độc lập (chính sách thương mại điện tử vs khoa học máy tính).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo góc giữa hai vector mà bỏ qua độ dài (magnitude) của vector. Điều này giúp đánh giá sự tương đồng ngữ nghĩa chính xác hơn, vì một đoạn văn dài và một câu tóm tắt ngắn của đoạn đó vẫn có góc vector nhỏ (similarity cao), trong khi khoảng cách Euclid lại bị kéo rộng ra do chênh lệch số lượng từ/chiều dài vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Bước dịch chuyển `step = chunk_size - overlap = 500 - 50 = 450`.  
> Công thức tính số chunk: ` làm_tròn_lên((10000 - 50) / 450) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23`.  
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap` tăng từ 50 lên 100, bước dịch chuyển `step` giảm xuống `500 - 100 = 400`. Số chunk sẽ là `làm_tròn_lên((10000 - 100) / 400) = làm_tròn_lên(9900 / 400) = 25 chunks` (tăng 2 chunks). Tăng độ chồng chéo giúp giữ lại ngữ cảnh ở các vùng ranh giới giữa hai chunk kế tiếp, tránh hiện tượng câu hoặc ý niệm quan trọng bị cắt đôi làm mất thông tin khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `re.split(r"(?<=[.!?])\s+", text.strip())` để phân tách câu dựa trên ranh giới các dấu chấm, hỏi, cảm thán theo sau bởi khoảng trắng. Sau đó lọc bỏ khoảng trắng thừa và gom từng nhóm tối đa `max_sentences_per_chunk` câu ghép lại bằng khoảng trắng để tạo thành từng chunk hoàn chỉnh.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Sử dụng danh sách các dấu phân cách theo thứ tự ưu tiên giảm dần (`["\n\n", "\n", ". ", " ", ""]`). Thuật toán thử phân tách bằng separator hiện tại; nếu khối nào vượt quá `chunk_size`, nó đệ quy thực hiện lại với separator cấp tiếp theo. Base case là khi khối văn bản $\le$ `chunk_size` hoặc đã hết separator thì cắt cứng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ danh sách các tài liệu dưới dạng dictionary gồm `id`, `content`, `metadata` và `embedding` thu được từ `_embedding_fn`. Khi gọi `search`, câu hỏi được nhúng thành vector query, tính tích vô hướng (dot product) / cosine similarity với từng record trong store, sắp xếp giảm dần theo điểm số `score` và lấy `top_k` kết quả đầu tiên.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện tiền lọc (pre-filtering): duyệt qua danh sách trong `_store` để giữ lại các record có metadata thỏa mãn tất cả tiêu chuẩn trong `metadata_filter`, rồi mới tính similarity search trên danh sách đã lọc. `delete_document` lọc và loại bỏ các record có `id` hoặc `metadata["doc_id"]` trùng với `doc_id` cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k)` để truy xuất các chunk liên quan nhất. Nếu không tìm thấy chunk nào, trả về câu thông báo không đủ thông tin. Nếu có, ghép các chunk thành chuỗi context dạng `[1] content_1\n\n[2] content_2` và inject vào prompt RAG tiêu chuẩn yêu cầu LLM trả lời dựa duy nhất trên context này.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\DAY07\DAY07_2A202601086_TranTuanAnh
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.11s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Hệ thống chấp nhận thanh toán qua ví điện tử và thẻ ngân hàng. | Khách hàng có thể chuyển khoản hoặc dùng thẻ để thanh toán. | cao | -0.0275 | Sai |
| 2 | Quy trình đổi trả sản phẩm trong vòng 7 ngày. | Hàng bị lỗi được hỗ trợ 1 đổi 1 trong tuần đầu tiên. | cao | -0.0803 | Sai |
| 3 | Chính sách bảo mật thông tin cá nhân của người mua. | Thời gian giao hàng dự kiến từ 2 đến 3 ngày làm việc. | thấp | -0.1228 | Đúng |
| 4 | Điều kiện dành cho người bán đăng sản phẩm trên sàn. | Thuật toán xử lý ngôn ngữ tự nhiên phân tích ngữ pháp. | thấp | 0.2005 | Sai |
| 5 | Phương thức vận chuyển hỏa tốc trong nội thành. | Giao hàng nhanh trong 2 giờ đối với khu vực trung tâm. | cao | -0.0828 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là cặp 4 (hai câu không liên quan) lại có điểm tương đồng cao hơn cặp 1, 2, 5 (các cặp câu có cùng ý nghĩa). Nguyên nhân là do `MockEmbedder` chỉ băm (hash MD5) các ký tự chuỗi thành vector ngẫu nhiên để phục vụ unit test chứ không phản ánh đúng ngữ nghĩa thực tế. Điều này cho thấy khi triển khai RAG thật, bắt buộc phải dùng mô hình nhúng ngữ nghĩa chuyên dụng (như `LocalEmbedder` - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` hoặc OpenAI embeddings) để có kết quả truy xuất chính xác.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền đối với đơn hàng giao thành công thông thường là bao nhiêu ngày? | et Banking. - **Điều kiện:** từ 10.000 VNĐ trở lên... (Chunk 15 ngày nằm trong Top-3) | 0.3468 | Có (Top-3) | Dựa trên tài liệu: 15 ngày kể từ khi giao thành công... |
| 2 | Nhà bán trên Tiki bị xử lý như thế nào nếu thực hiện các hành vi gian lận như tự đặt đơn hoặc lôi kéo khách giao dịch ngoài sàn? | gian lận có liên quan. - Phong tỏa sao kê 90 ngày. ## III. Điều kiện về quảng cáo... (Filter: seller) | 0.2290 | Có (Top-1) | Nhà Bán bị ngưng hợp tác vĩnh viễn, thu hồi khuyến mãi, phong tỏa sao kê 90 ngày... |
| 3 | Shopee hỗ trợ những phương thức thanh toán chính nào và hạn mức điều kiện đối với Apple Pay là bao nhiêu? | # Các phương thức thanh toán trên Shopee Shopee hiện hỗ trợ 9 hình thức thanh toán chính... (Filter: buyer) | 0.3050 | Có (Top-1) | Shopee hỗ trợ 9 hình thức thanh toán chính. Apple Pay hạn mức 10.000 đến 25.000.000 VNĐ... |
| 4 | Các loại hàng hóa cấm đăng bán hoặc kinh doanh trên sàn giao dịch thương mại điện tử bao gồm những loại nào? | c khiếu nại. **Đối với người bán:** Đăng ký → Cung cấp thông tin → Đăng tải sản phẩm... | 0.3823 | Không | Không đủ thông tin trong ngữ cảnh được cung cấp... |
| 5 | Chính sách vận chuyển Shopee quy định thời gian xử lý khiếu nại đối với hư hỏng/mất mát hàng hóa tối đa là bao nhiêu ngày? | \| Phương thức \| Đơn vị \| Thời gian \| (Chunk khiếu nại 10 ngày làm việc nằm trong Top-3) | 0.1597 | Có (Top-3) | Thời gian xử lý khiếu nại tối đa là 10 ngày làm việc... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua thử nghiệm, việc kết hợp metadata filtering (như lọc theo `customer_role: seller` hoặc `customer_role: buyer`) đóng vai trò cực kỳ quan trọng giúp loại bỏ hoàn toàn nhiễu và đạt tỷ lệ chính xác Top-1 tuyệt đối (100%), vượt trội hơn hẳn so với việc chỉ tìm kiếm tương đồng vector thuần túy.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
