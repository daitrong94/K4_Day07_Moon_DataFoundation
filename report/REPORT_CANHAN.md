# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:* Độ tương tự cosine cao (gần 1.0) nghĩa là hai vector có hướng rất gần nhau trong không gian vector biểu diễn. Trong xử lý ngôn ngữ tự nhiên, điều này thể hiện hai đoạn văn bản có sự tương đồng lớn về mặt ngữ nghĩa và ngữ cảnh, bất kể độ dài hay từ ngữ cụ thể được sử dụng có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sản phẩm này có thể đổi trả trong vòng 7 ngày không?"
- Câu B: "Chính sách hoàn tiền của shop có giới hạn thời gian dưới một tuần không?"
- Tại sao tương đồng: Cả hai câu đều hỏi về giới hạn thời gian đổi trả/hoàn tiền của cửa hàng (7 ngày tương đương 1 tuần), có cùng ý nghĩa ngữ nghĩa cốt lõi dù dùng từ vựng khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Làm thế nào để thanh toán đơn hàng bằng ví điện tử?"
- Câu B: "Vui lòng kiểm tra kỹ danh mục hàng cấm trước khi đăng bán."
- Tại sao khác: Câu A nói về phương thức thanh toán của người mua, còn Câu B nói về quy định đăng bán sản phẩm của người bán. Hai chủ đề hoàn toàn khác biệt về cả từ vựng và ngữ cảnh.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* Khoảng cách Euclid bị ảnh hưởng nặng nề bởi độ dài của văn bản (độ lớn của vector), khiến hai văn bản cùng chủ đề nhưng khác độ dài có khoảng cách rất xa nhau. Độ tương tự cosine chỉ tập trung vào góc giữa hai vector (hướng ngữ nghĩa), giúp đo lường độ tương đồng chính xác mà không phụ thuộc vào độ dài văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Công thức tính số lượng chunk là: ceil((length - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* Khi overlap tăng lên 100, số lượng chunk sẽ tăng lên (bằng ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25 chunks). Chúng ta muốn độ chồng chéo nhiều hơn để đảm bảo thông tin ngữ cảnh ở ranh giới giữa các chunk không bị cắt đứt hoặc mất mát, giúp mô hình embedding và LLM hiểu trọn vẹn ngữ nghĩa của văn bản.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?* Dùng biểu thức chính quy `(?<=[.!?])\s+` để tách câu tại khoảng trắng đứng sau các dấu kết thúc câu (`.`, `!`, `?`). Cách tiếp cận này giúp giữ nguyên các dấu câu ở cuối câu và xử lý tốt các ký tự xuống dòng liên tiếp bằng cách strip khoảng trắng thừa của từng câu đơn trước khi gộp nhóm.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?* Thuật toán sử dụng đệ quy để tách văn bản theo các dấu phân tách có thứ tự ưu tiên giảm dần. Trường hợp cơ sở (base case) là khi văn bản nhỏ hơn `chunk_size` (trả về chính nó) hoặc khi hết danh sách phân tách thì cắt cố định theo kích thước `chunk_size`. Khi một đoạn văn bản bị chia nhỏ vượt quá kích thước cho phép, nó sẽ được đệ quy xử lý bằng dấu phân tách có ưu tiên thấp hơn tiếp theo.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Lưu trữ thế nào? Tính độ tương tự ra sao?* Các chunk tài liệu được chuẩn hóa thông qua hàm `_make_record` để sao chép metadata, đảm bảo có `doc_id` và sinh ra ID chunk duy nhất kết hợp với chỉ số tự tăng. Các record này được lưu trữ in-memory trong một danh sách `self._store`. Khi tìm kiếm (`search`), query được nhúng thành một vector duy nhất, sau đó tính tích vô hướng (dot product) với từng vector embedding của record trong store để tính điểm số tương tự, cuối cùng sắp xếp giảm dần và lấy `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Lọc (filter) trước hay sau? Xóa bằng cách nào?* Lọc metadata được thực hiện trước khi tính toán tương tự (pre-filtering). Record chỉ được đưa vào so sánh nếu thỏa mãn tất cả các tiêu chí trong `metadata_filter`. Thao tác xóa (`delete_document`) duyệt qua store và giữ lại những record có `metadata['doc_id']` khác với `doc_id` cần xóa, trả về `True` nếu số lượng record bị giảm đi (tức là đã xóa thành công ít nhất một chunk).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?* Gọi `search` trên `EmbeddingStore` để tìm `top_k` chunk tương quan nhất. Các chunk này được nối lại thành chuỗi ngữ cảnh, đánh số thứ tự dạng `[1]`, `[2]`, ... kèm tên file gốc (`doc_id`) để phục vụ đối chiếu nguồn (grounding). Prompt được tạo ra có cấu trúc chặt chẽ gồm: phần chỉ dẫn (chỉ sử dụng ngữ cảnh được cung cấp, nói rõ nếu không đủ thông tin), phần Context, câu hỏi (Question), và nhãn kết thúc "Answer:" trước khi chuyển tiếp cho hàm LLM sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0 -- D:\CODE\AITHUCCHIEN\LABS\K4-Day07-DF-2A202601112-NguyenXuanDuc\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\CODE\AITHUCCHIEN\LABS\K4-Day07-DF-2A202601112-NguyenXuanDuc
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
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

============================= 42 passed in 0.19s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42



---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Shopee hỗ trợ những phương thức thanh toán chính nào? | Tôi có thể thanh toán đơn hàng bằng những hình thức nào trên Shopee? | Cao | -0.08792 | Không |
| 2 | Thời hạn đổi trả hàng là 15 ngày. | Thực phẩm tươi sống phải được yêu cầu trả hàng trong vòng 24 giờ. | Trung bình | 0.08980 | Có phần đúng |
| 3 | Nhà bán bị cấm lôi kéo khách hàng giao dịch ngoài Tiki. | Làm thế nào để đăng ký tài khoản mua hàng ShopeeVIP? | Thấp | 0.23195 | Không |
| 4 | Mức bồi thường khi mất hàng là 70% giá trị sản phẩm. | Nếu hàng hóa bị thất lạc, Shopee sẽ đền bù 70% giá bán sản phẩm. | Cao | 0.08885 | Không |
| 5 | Thành viên hạng Vàng được trả hàng COM không giới hạn. | Người dùng ShopeeVIP chỉ được trả hàng COM tối đa 15 lần một tháng. | Trung bình/Thấp | 0.08029 | Có phần đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:* Kết quả bất ngờ nhất là Cặp 3 (hai câu hoàn toàn khác biệt) lại có điểm tương đồng cao nhất (0.23195), trong khi Cặp 1 và Cặp 4 (hai câu có ý nghĩa tương tự nhau) lại có điểm tương đồng âm hoặc rất thấp. Điều này xảy ra do mô hình `MockEmbedder` hoạt động bằng cách băm chuỗi (MD5) để tạo ra các vector số ngẫu nhiên xác định chứ không biểu diễn ngữ nghĩa của câu. Để có độ tương đồng ngữ nghĩa chính xác, bắt buộc phải sử dụng các mô hình embeddings thực sự được huấn luyện (như mô hình đa ngữ cục bộ hoặc của OpenAI).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền đối với đơn hàng giao thành công thông thường là bao nhiêu ngày? | tiki-seller-rights-obligations: Đảm bảo hàng hóa được phê duyệt bởi cơ quan nhà nước... | 0.241 | Không (No) | Thời hạn đổi trả thông thường là 15 ngày, riêng thực phẩm tươi sống/đông lạnh là 24 giờ. |
| 2 | Nhà bán trên Tiki bị xử lý như thế nào nếu thực hiện các hành vi gian lận như tự đặt đơn hoặc lôi kéo khách giao dịch ngoài sàn? | shopee-prohibited-products-policy: Chính sách áp dụng cho tất cả người bán trên Shopee... | 0.223 | Không (No) | Sẽ bị: ngưng hợp tác kinh doanh vĩnh viễn, thu hồi khuyến mãi lạm dụng, phong tỏa sao kê 90 ngày... |
| 3 | Shopee hỗ trợ những phương thức thanh toán chính nào và hạn mức điều kiện đối với Apple Pay là bao nhiêu? | shopee-marketplace-rules: Shopee cam kết bảo mật thông tin cá nhân của thành viên... | 0.247 | Không (No) | Hỗ trợ 9 phương thức thanh toán. Apple Pay từ 10.000 VNĐ đến 25.000.000 VNĐ, có một số hạn chế... |
| 4 | Các loại hàng hóa cấm đăng bán hoặc kinh doanh trên sàn giao dịch thương mại điện tử bao gồm những loại nào? | shopee-shipping-policy: Cây cảnh chỉ giao hỏa tốc; Thực phẩm dưới 30 ngày giao nhanh... | 0.425 | Không (No) | Liệt kê các danh mục hàng cấm như hàng giả nhái, vũ khí, ma túy, thuốc lá điện tử, bùa ngải... |
| 5 | Chính sách vận chuyển Shopee quy định thời gian xử lý khiếu nại đối với hư hỏng/mất mát hàng hóa tối đa là bao nhiêu ngày? | shopee-return-refund-policy: Shopee cho phép người mua gửi yêu cầu hoàn trả trong... | 0.316 | Không (No) | Quy định thời gian xử lý khiếu nại tối đa là 10 ngày làm việc kể từ khi nhận đủ bằng chứng hợp lệ. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 0 / 5

**Lý do lỗi (Failure Analysis):**
* **Precision (Độ chính xác):** Đạt 0% do sử dụng `MockEmbedder` khiến việc tính toán khoảng cách vector hoàn toàn ngẫu nhiên và chọn sai tài liệu/phân đoạn. Tuy nhiên, Agent vẫn sinh câu trả lời đúng vì hàm sinh câu trả lời LLM đang được cấu hình cứng (mocked) theo từ khóa của query để chạy demo luồng kỹ thuật, còn thực tế context truyền vào không chứa thông tin trả lời.
* **Chunk Coherence (Mạch lạc):** Các chunk tạo bởi `RecursiveChunker(chunk_size=400)` được cắt gọn gàng tại các dấu ranh giới tự nhiên như dòng hoặc câu. Tuy nhiên, do retrieval bị sai từ đầu nên tính mạch lạc chưa giúp ích được cho LLM.
* **Metadata Utility (Hữu ích của bộ lọc):** Rất tốt. Đối với Câu 2, bộ lọc `{"customer_role": "seller"}` đã giới hạn thành công danh sách tìm kiếm từ 67 chunk xuống chỉ còn các tài liệu dành cho người bán (seller) như `tiki-seller-rights-obligations` và `shopee-prohibited-products-policy`, loại bỏ hoàn toàn các tài liệu của người mua (buyer) để tránh nhiễu.
* **Grounding (Chất lượng thông tin nền):** Không đạt trên môi trường thực tế (nếu dùng LLM thật), vì Context được truyền vào prompt hoàn toàn lệch chủ đề so với câu hỏi, khiến mô hình thật sẽ bị ảo giác hoặc từ chối trả lời. Đề xuất cải tiến quan trọng nhất là cấu hình sử dụng mô hình embedding thật (`LocalEmbedder` hoặc `OpenAIEmbedder`).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:* Học được cách chia nhỏ văn bản (chunking) kết hợp giữa tiêu đề heading và ranh giới đoạn. Việc gắn tiêu đề heading cha vào các chunk con giúp lưu giữ ngữ cảnh cực kỳ tốt khi mô hình thực hiện tìm kiếm ngữ nghĩa, ngăn chặn việc mất thông tin nguồn khi chia các tài liệu có cấu trúc phân cấp phức tạp.

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

