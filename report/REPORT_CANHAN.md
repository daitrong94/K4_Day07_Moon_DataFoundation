# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Trọng Đại
**Nhóm:** Moon
**Ngày:** 03-08-2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding chỉ cùng một hướng trong không gian nhiều chiều — tức hai đoạn văn bản diễn đạt cùng một ý/chủ đề, dù dùng từ ngữ khác nhau. Điểm cosine càng gần 1 thì hai câu càng gần nghĩa nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Người mua có thể trả hàng trong 15 ngày kể từ khi nhận được sản phẩm."
- Câu B: "Thời hạn hoàn trả sản phẩm cho người mua là 15 ngày kể từ ngày giao hàng thành công."
- Tại sao tương đồng: cả hai câu cùng nói về một sự kiện — thời hạn 15 ngày để người mua trả hàng — chỉ khác cách diễn đạt (paraphrase), nên vector embedding của chúng gần như cùng hướng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Người bán không được đăng bán hàng cấm như vũ khí và ma túy."
- Câu B: "Hôm nay trời nắng đẹp, thích hợp để đi dạo công viên."
- Tại sao khác: hai câu không liên quan gì về chủ đề (chính sách thương mại điện tử vs. thời tiết/hoạt động cá nhân), nên vector của chúng gần như vuông góc hoặc ngược hướng nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo *góc/hướng* giữa hai vector, bỏ qua độ dài (magnitude) của chúng — nên không bị ảnh hưởng bởi việc một đoạn văn dài hay ngắn hơn đoạn kia. Euclidean distance lại đo khoảng cách tuyệt đối, dễ bị "phạt" oan hai câu cùng nghĩa chỉ vì embedding của chúng có độ lớn khác nhau (ví dụ do độ dài câu khác nhau), nên với text embeddings, cosine phản ánh đúng "cùng ý hay không" hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính:
> `số chunk = ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
>
> Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> `số chunk = ceil((10000 − 100) / (500 − 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks`
>
> Overlap tăng từ 50 lên 100 làm số chunk tăng từ 23 lên 25 (tăng ~9%), vì bước nhảy (`chunk_size − overlap`) giữa các chunk nhỏ lại nên cần nhiều chunk hơn để phủ hết văn bản. Muốn tăng overlap vì thông tin quan trọng thường nằm vắt ngang ranh giới hai chunk (ví dụ một câu bị cắt đôi ở cuối chunk này, đầu chunk kia) — overlap lớn hơn giúp mỗi chunk giữ thêm ngữ cảnh xung quanh, giảm rủi ro mất ý nghĩa khi truy xuất, đổi lại tốn thêm bộ nhớ/thời gian embedding vì nhiều chunk hơn và dữ liệu bị lặp lại nhiều hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+` (lookbehind) để tách câu ngay sau dấu `.`, `!`, `?` theo sau bởi khoảng trắng/xuống dòng — vừa đủ đơn giản để bao quát cả 4 kiểu ranh giới câu nêu trong đề bài (". ", "! ", "? ", ".\n"). Sau khi tách, lọc bỏ chuỗi rỗng và `strip()` từng câu, rồi gom nhóm `max_sentences_per_chunk` câu liên tiếp thành một chunk. Edge case xử lý: text rỗng hoặc chỉ có khoảng trắng → trả về `[]` thay vì lỗi.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy kiểu "thử separator theo thứ tự ưu tiên": nếu đoạn văn bản hiện tại đã ≤ `chunk_size` thì dừng (base case). Nếu chưa, tách bằng separator đầu tiên còn lại rồi *gộp lại theo kiểu tham lam (greedy merge)* — nối các phần liền kề cho tới sát ngưỡng `chunk_size`; phần nào tự nó vẫn quá lớn thì gọi đệ quy `_split` trên chính phần đó với danh sách separator còn lại (bỏ separator vừa dùng). Base case còn lại: hết separator để thử, hoặc gặp separator rỗng `""` → hard-split theo số ký tự cố định (đảm bảo luôn có kết quả, không bị kẹt vô hạn).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hoá qua `_make_record()` thành một dict `{id, content, metadata, embedding}` — trong đó `metadata['doc_id']` luôn được set (mặc định bằng `doc.id` nếu chưa có), để `delete_document`/`search_with_filter` sau này dùng chung một khoá tra cứu. Lưu trữ trong bộ nhớ (`self._store: list[dict]`), có kèm nhánh ChromaDB nếu thư viện có cài (mặc định fallback in-memory vì môi trường lab không cài `chromadb`). Tính độ tương tự bằng **dot product** giữa vector truy vấn và từng vector đã lưu (helper `_search_records`) — hợp lý vì các embedder trong lab đều trả vector đã chuẩn hoá (norm = 1), nên dot product ở đây tương đương cosine similarity nhưng rẻ hơn về tính toán.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước** khi tìm kiếm: `search_with_filter` duyệt `self._store`, giữ lại record nào có `metadata[k] == v` với mọi cặp trong `metadata_filter`, rồi mới gọi `_search_records` trên tập đã lọc — tránh tính similarity cho các chunk chắc chắn không phù hợp. `delete_document(doc_id)` xoá bằng cách giữ lại mọi record có `metadata['doc_id'] != doc_id`, trả về `True/False` tuỳ có record nào thực sự bị loại hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer()` gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất, nối nội dung (`content`) của chúng bằng `\n\n` làm phần ngữ cảnh (context). Prompt được dựng theo mẫu cố định: yêu cầu LLM chỉ trả lời dựa trên context, tự nói rõ nếu ngữ cảnh không đủ thông tin (giảm rủi ro "bịa" khi không có dữ liệu), rồi chèn context + câu hỏi vào cuối. Cuối cùng gọi `llm_fn(prompt)` — hàm này được inject từ bên ngoài (dependency injection), nên `KnowledgeBaseAgent` không phụ thuộc vào một nhà cung cấp LLM cụ thể nào, dễ test bằng hàm giả lập.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.1, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Chạy bằng `OpenAIEmbedder` (`text-embedding-3-small`, `EMBEDDING_PROVIDER=openai`, key trong `.env` cục bộ — không commit) để có kết quả phản ánh ngữ nghĩa thật, thay vì `MockEmbedder`. (Lần chạy đầu bằng mock cho kết quả gần-ngẫu-nhiên — xem lịch sử; giữ nguyên bộ 5 cặp câu để so sánh trực tiếp mock vs thật ở mục "bất ngờ nhất" bên dưới.)

| Cặp | Câu A | Câu B | Dự đoán | Điểm mock (trước) | Điểm thật (OpenAI) | Đúng? |
|------|-----------|-----------|---------|:---:|:---:|-------|
| 1 | "Người mua có thể trả hàng trong 15 ngày kể từ khi nhận được sản phẩm." | "Thời hạn hoàn trả sản phẩm cho người mua là 15 ngày kể từ ngày giao hàng thành công." (paraphrase) | cao | 0.0578 | **0.8334** | Đúng — rất cao |
| 2 | "Người mua có thể trả hàng trong 15 ngày kể từ khi nhận được sản phẩm." | "Con mèo đang ngủ trên ghế sofa trong phòng khách." (không liên quan) | thấp | 0.0110 | **0.2276** | Đúng — thấp rõ rệt so với cặp 1 |
| 3 | "Shopee hỗ trợ thanh toán bằng thẻ tín dụng, ví điện tử và COD." | "Bạn có thể thanh toán đơn hàng qua thẻ ghi nợ, ShopeePay hoặc trả tiền khi nhận hàng." (paraphrase) | cao | -0.1224 | **0.7194** | Đúng — cao |
| 4 | "Người bán không được đăng bán hàng cấm như vũ khí và ma túy." | "Hôm nay trời nắng đẹp, thích hợp để đi dạo công viên." (không liên quan) | thấp | 0.1364 | **0.2470** | Đúng — thấp |
| 5 | "Chính sách bảo mật quy định Shopee thu thập tên, email và số điện thoại của người dùng." | "Người bán phải chịu trách nhiệm về chất lượng và nguồn gốc sản phẩm đăng bán." (cùng miền chính sách, khác chủ đề con) | thấp | -0.2675 | **0.2908** | Đúng — thấp hơn hẳn 2 cặp paraphrase (1, 3) dù cùng miền chính sách TMĐT |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **độ lệch giữa mock và embedder thật trên cùng 5 cặp câu**: với `MockEmbedder`, cặp paraphrase #3 (cùng nói về phương thức thanh toán) ra điểm **âm** (-0.1224) trong khi cặp không liên quan #4 lại ra điểm **dương** cao hơn (0.1364) — sai hoàn toàn trực giác. Đổi sang `OpenAIEmbedder`, đúng 5/5 dự đoán khớp trực giác, và đặc biệt rõ: hai cặp paraphrase (#1, #3) đạt 0.72–0.83 — cao hẳn so với mọi cặp không paraphrase (0.22–0.29), kể cả cặp #5 tuy cùng miền chính sách TMĐT nhưng khác chủ đề con (bảo mật vs. trách nhiệm người bán) vẫn chỉ 0.29, gần với mức "không liên quan" chứ không nhích lên do "cùng lĩnh vực". Bài học: `compute_similarity()` chỉ là công thức toán đúng; **chất lượng embedding mới quyết định kết quả có ý nghĩa hay không** — cùng một hàm, cùng 5 cặp câu, đổi embedder là đổi hẳn kết luận.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> Chạy đúng **5 câu hỏi benchmark chính thức của nhóm** (đã được Trần Tuấn Anh và Nguyễn Xuân Đức độc lập thống nhất giống hệt nhau trong `REPORT_NHOM.md` của họ — xem `report/SO_SANH_NHOM.md` mục 1). Pipeline: `build_knowledge_base("data/k4_ecommerce", OpenAIEmbedder(), chunker=RecursiveChunker(400))` — **embedder thật** (`text-embedding-3-small`, key trong `.env` cục bộ), thay cho mock ở lần chạy trước. `llm_fn` vẫn là hàm giả lập trích nguyên văn ngữ cảnh (không có quyền dùng API LLM sinh văn bản thật trong lab này) — chỉ để xác nhận pipeline retrieve → prompt → answer nối thông đúng luồng và trích dẫn đúng chunk.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền... | `shopee-return-refund-policy` — "**15 ngày** kể từ khi đơn hàng được giao thành công. **24 giờ** đối với thực phẩm tươi sống..." | 0.5991 | **Có** — Hit@1 đúng, đúng câu chứa đáp án | Trích đúng "15 ngày" / "24 giờ" từ ngữ cảnh |
| 2 | Nhà bán trên Tiki bị xử lý thế nào nếu gian lận... *(filter seller)* | `tiki-seller-rights-obligations` — liệt kê đúng hành vi gian lận nêu trong câu hỏi | 0.6543 | **Có** — Hit@1 đúng | Trích đúng danh sách hành vi cấm, tuy chunk top-1 chưa gồm đoạn "Hình thức xử lý" (ở chunk kế) |
| 3 | Shopee hỗ trợ phương thức thanh toán nào, hạn mức Apple Pay? *(filter buyer)* | `shopee-payment-methods` — mở đầu "Shopee hiện hỗ trợ 9 hình thức thanh toán chính" | 0.6712 | **Có** — Hit@1 đúng | Trích đúng tài liệu; hạn mức Apple Pay nằm ở chunk khác cùng doc (không lọt top-1 vì `top_k=3` đã ưu tiên đoạn mở đầu) |
| 4 | Hàng hóa cấm đăng bán trên sàn TMĐT bao gồm loại nào? | `tiki-seller-rights-obligations` — câu tổng quát "không được kinh doanh hàng hóa bị cấm..." | 0.5301 | **Không** — `shopee-prohibited-products-policy` (tài liệu gold, có danh mục chi tiết) không lọt top-3 | Agent trả lời dựa trên câu tổng quát, thiếu danh mục cụ thể (súng, ma túy, hàng giả…) |
| 5 | Thời gian xử lý khiếu nại vận chuyển tối đa bao nhiêu ngày? | `shopee-shipping-policy` — "Thời gian xử lý khiếu nại tối đa **10 ngày làm việc**..." | 0.6641 | **Có** — Hit@1 đúng | Trích đúng "10 ngày làm việc" |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4 / 5** (Hit@1 = Hit@3 = 4/5 — tăng mạnh so với lần chạy mock trước đó, xem `report/SO_SANH_NHOM.md`). Câu 4 là **failure case thật**: hai tài liệu cùng nhắc "hàng hóa bị cấm" ở hai mức độ chi tiết khác nhau (câu tổng quát trong `tiki-seller-rights-obligations` vs. danh mục đầy đủ trong `shopee-prohibited-products-policy`) — embedding đánh giá câu tổng quát "giống câu hỏi" hơn vì câu hỏi cũng diễn đạt chung chung, trong khi tài liệu gold chứa toàn tên hàng hóa cụ thể (súng, ma túy, hàng giả...) nên vector lệch xa hơn so với cách diễn đạt của câu hỏi. Đây là ứng viên tốt cho Bài 3.5 (Phân tích lỗi) của nhóm.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Từ việc đọc chéo code 3 nhánh còn lại (xem `report/SO_SANH_NHOM.md`): Nguyễn Xuân Đức trung thực báo cáo Hit@3 = 0/10 khi chạy mock thay vì tô hồng kết quả — cách làm này giúp cả nhóm sớm nhận ra mock là nút thắt thật sự (điều tôi vừa xác nhận lại bằng embedder thật ở trên). Phổ Hiếu Anh đóng góp kỹ thuật Hybrid BM25+RRF — về lý thuyết hữu ích nhất cho các câu hỏi có số liệu/tên riêng (giống câu 3 ở trên, nơi "Apple Pay" và "10.000–25.000.000 VNĐ" là token hiếm mà BM25 khớp tốt hơn dense).

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 *(Hit@1=Hit@3=4/5 với OpenAIEmbedder thật, đúng 5 câu hỏi nhóm; trừ 1 điểm vì `llm_fn` vẫn là hàm giả lập, chưa phải LLM sinh văn bản thật)* |
| **Tổng phần cá nhân** | **59 / 60** |
