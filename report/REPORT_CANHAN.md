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

> **Lưu ý:** phần này chạy bằng `MockEmbedder` (mặc định của lab), không phải embedder ngữ nghĩa thật (`EMBEDDING_PROVIDER=local`). README đã cảnh báo mock "gần như ngẫu nhiên theo chuỗi" — kết quả dưới đây minh hoạ đúng điều đó, không dùng để kết luận chất lượng ngữ nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Người mua có thể trả hàng trong 15 ngày kể từ khi nhận được sản phẩm." | "Thời hạn hoàn trả sản phẩm cho người mua là 15 ngày kể từ ngày giao hàng thành công." (paraphrase) | cao | 0.0578 | Sai hướng độ lớn — đúng dấu (dương) nhưng gần 0, không "cao" như kỳ vọng |
| 2 | "Người mua có thể trả hàng trong 15 ngày kể từ khi nhận được sản phẩm." | "Con mèo đang ngủ trên ghế sofa trong phòng khách." (không liên quan) | thấp | 0.0110 | Đúng — gần 0 |
| 3 | "Shopee hỗ trợ thanh toán bằng thẻ tín dụng, ví điện tử và COD." | "Bạn có thể thanh toán đơn hàng qua thẻ ghi nợ, ShopeePay hoặc trả tiền khi nhận hàng." (paraphrase) | cao | -0.1224 | **Sai hẳn** — hai câu paraphrase lại có điểm âm |
| 4 | "Người bán không được đăng bán hàng cấm như vũ khí và ma túy." | "Hôm nay trời nắng đẹp, thích hợp để đi dạo công viên." (không liên quan) | thấp | 0.1364 | **Sai hẳn** — cặp không liên quan lại có điểm dương cao hơn cả cặp paraphrase ở trên |
| 5 | "Chính sách bảo mật quy định Shopee thu thập tên, email và số điện thoại của người dùng." | "Người bán phải chịu trách nhiệm về chất lượng và nguồn gốc sản phẩm đăng bán." (cùng miền chính sách, khác chủ đề con) | thấp | -0.2675 | Đúng hướng (thấp/âm) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 3 và 4: hai câu paraphrase gần như cùng nghĩa (nói về phương thức thanh toán) lại có điểm **âm** (-0.1224), trong khi hai câu hoàn toàn không liên quan (chính sách hàng cấm vs. thời tiết) lại có điểm **dương** (0.1364) cao hơn. Điều này khẳng định đúng cảnh báo của lab: `MockEmbedder` sinh vector từ hash MD5 của chuỗi ký tự (`hashlib.md5`) rồi biến đổi thành số giả-ngẫu-nhiên — nó không hề "đọc hiểu" nội dung câu, chỉ tình cờ tạo ra vector có hướng gần/xa nhau dựa trên chuỗi byte đầu vào. Bài học rút ra: cosine similarity chỉ tốt bằng chất lượng của embedding tạo ra nó — công thức toán đúng không đảm bảo kết quả có ý nghĩa nếu vector đầu vào không thực sự mã hoá ngữ nghĩa. Muốn dự đoán mức tương tự "có ý nghĩa", bắt buộc phải dùng embedder ngữ nghĩa thật (`LocalEmbedder`/`OpenAIEmbedder`).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> **Lưu ý:** nhóm chưa chốt chính thức 5 câu hỏi đánh giá trong `REPORT_NHOM.md` tại thời điểm viết báo cáo này, nên dưới đây là **5 câu hỏi đề xuất** của tôi trên bộ dữ liệu `data/k4_ecommerce/` (đúng chủ đề K4), chạy bằng `build_knowledge_base()` + `MockEmbedder` (chưa cài `EMBEDDING_PROVIDER=local`). Kết quả cần chạy lại với embedder thật + bộ câu hỏi nhóm thống nhất trước khi tổng hợp vào `REPORT_NHOM.md`. `llm_fn` dùng hàm giả lập (không có API key LLM thật trong môi trường lab) chỉ để xác nhận pipeline retrieve → prompt → answer nối thông đúng luồng.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng? | `shipping-policy` — bảng giới hạn kích thước/trọng lượng gói hàng | 0.2364 | Không (top-1 sai); `returns-policy` chỉ đứng thứ 2 (0.2105), đúng tài liệu nhưng không trúng đúng câu "15 ngày" | Có trả lời (agent stub), nhưng context top-1 không chứa đáp án thật |
| 2 | Shopee hỗ trợ những phương thức thanh toán nào? | `prohibited-products` — đoạn về giữ tem/bao bì | 0.2429 | Không ở top-1; `payment-methods` đứng thứ 2 (0.2327) và có nội dung đúng | Trả lời dựa trên context lẫn cả đoạn không liên quan |
| 3 | Người bán không được đăng bán những loại hàng hóa nào? *(metadata_filter={"customer_role":"seller"})* | `prohibited-products` — mục "Danh mục hàng cấm/hạn chế" | 0.1126 | **Có** — đúng tài liệu, đúng nội dung ngay top-1 | Trả lời đúng hướng nhờ context liên quan |
| 4 | Shopee thu thập những loại thông tin cá nhân nào của người dùng? | `shipping-policy` — đoạn về xử lý khiếu nại | 0.3177 | **Không** — cả top-3 đều không thuộc `privacy-policy-shopee`, truy xuất thất bại hoàn toàn | Agent buộc phải trả lời dựa trên context sai chủ đề |
| 5 | Nhà bán trên Tiki có nghĩa vụ gì nếu vi phạm chính sách khuyến mãi? *(metadata_filter={"customer_role":"seller"})* | `prohibited-products` — đoạn liệt kê dịch vụ bất hợp pháp | 0.1792 | Một phần — đúng vai trò `seller` nhờ filter, nhưng sai tài liệu; `seller-listing` (chứa "Hình thức xử lý vi phạm") chỉ lọt top-3 ở vị trí cuối và là đoạn tiêu đề, chưa tới đúng đoạn có đáp án | Context không đủ để trả lời chính xác nghĩa vụ cụ thể |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5 (câu 1, 2, 3 có chunk đúng tài liệu trong top-3; câu 4 thất bại hoàn toàn; câu 5 chỉ đúng vai trò nhờ metadata filter nhưng chưa đúng đoạn nội dung).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(Chưa có dữ liệu — nhóm chưa demo/so sánh chiến lược. Sẽ cập nhật sau khi nhóm chạy benchmark chung với `EMBEDDING_PROVIDER=local` theo `REPORT_NHOM.md`.)*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 6 / 10 *(dùng mock embedder + câu hỏi chưa chốt với nhóm; cần chạy lại với `EMBEDDING_PROVIDER=local` và bộ câu hỏi chính thức)* |
| **Tổng phần cá nhân** | **56 / 60** |
