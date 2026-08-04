# So Sánh Chiến Lược Giữa Các Thành Viên — Lab 7 (K4)

**Ngày:** 2026-08-03
**Nguồn:** [github.com/daitrong94/K4_Day07_Moon_DataFoundation](https://github.com/daitrong94/K4_Day07_Moon_DataFoundation) — 4 nhánh: `main` (tôi), `2a202601086-TranTuanAnh`, `NguyenXuanDuc`, `feat/2A202601312-phohieuanh`

> Tài liệu này phục vụ Bài tập 3.4 (Chạy đánh giá & So sánh trong nhóm) — bổ sung số liệu thực đo cho Phần 2/3 của `REPORT_NHOM.md`.

---

## 1. Phương pháp so sánh

Đọc code + report của cả 3 thành viên còn lại, sau đó **chạy lại chéo** cài đặt của từng người trên **cùng một điều kiện** để so sánh công bằng — thay vì chỉ đọc số liệu mỗi người tự báo cáo (vốn chạy trên corpus/tham số khác nhau):

- **Cùng corpus:** `data/k4_ecommerce/` ở nhánh `main` (8 tài liệu Shopee/Tiki) — đúng bộ mà tôi, Trần Tuấn Anh, Nguyễn Xuân Đức đều dùng.
- **Cùng 5 câu hỏi benchmark:** lấy nguyên bộ mà Trần Tuấn Anh và Nguyễn Xuân Đức đã độc lập thống nhất giống hệt nhau trong `REPORT_NHOM.md` của họ (kể cả gold answer + target doc) — đây rõ ràng là bộ câu hỏi nhóm đã chốt, tôi dùng lại thay vì tạo bộ khác.
- **Cùng embedder:** `MockEmbedder` cho mọi biến thể (không ai trong nhóm cài `EMBEDDING_PROVIDER=local` được trong môi trường tương ứng), để chênh lệch kết quả phản ánh đúng khác biệt về **chiến lược chunking/retrieval**, không lẫn với khác biệt embedder.
- Code của từng nhánh được trích riêng (`git show <branch>:src/*.py`) thành các package độc lập rồi chạy trực tiếp — không sửa lại logic của ai.

## 2. Cách tiếp cận từng thành viên

| Thành viên | Chunking | Vector store | Điểm khác biệt đáng chú ý |
|---|---|---|---|
| **Tôi** (Hoàng Trọng Đại) | `RecursiveChunker(400)` | dense in-memory, dot product | `_make_record` luôn set `metadata['doc_id']` mặc định |
| **Trần Tuấn Anh** | `RecursiveChunker` (mặc định 500, theo report) | dense, có nhánh ChromaDB thật (`collection.query`) | `Bench.py` thực chất gọi `build_knowledge_base()` **không truyền chunker** → chạy `FixedSizeChunker` mặc định, lệch với chiến lược `RecursiveChunker` ghi trong `REPORT_NHOM.md` |
| **Nguyễn Xuân Đức** | `RecursiveChunker(400)` | dense, chủ động tắt Chroma dù có cài (`self._use_chroma = False` cứng) | Report ghi rõ trung thực Hit@3 = 0/10 do mock — không tô hồng kết quả |
| **Phổ Hiếu Anh** | `PolicySectionChunker` (cắt theo tiêu đề điều khoản) + tiền tố ngữ cảnh (`[title \| category \| customer_role]`) | `HybridStore` = dense + BM25 Okapi, hợp nhất bằng Reciprocal Rank Fusion | Tự thu thập **bộ corpus riêng** (CellphoneS/Di Động Việt/Hoàng Hà Mobile, 9 tài liệu) và bộ câu hỏi riêng, khác nhóm chính — nên không nằm trong benchmark Hit@1/Hit@3 dùng chung corpus ở mục 4, chỉ so sánh phần kỹ thuật retrieval |

## 3. Phát hiện khi đọc chéo code

**Bug thật, không phải suy đoán — đã viết test xác minh (`tests/test_extra_coverage.py::TestDeleteDocumentThroughIngestPipeline`):**

Nhánh Trần Tuấn Anh cài `delete_document` theo:
```python
self._store = [record for record in self._store if record["id"] != doc_id]
```
`tests/test_solution.py` gốc **không bắt được lỗi này** vì nó gọi `add_documents()` trực tiếp với `Document.id == doc_id`. Nhưng pipeline thật (`ingest.py` → `build_knowledge_base()`) tạo chunk-id dạng `"policy-x::chunk_0"` khác hẳn `doc_id`, trong khi gắn `doc_id` vào `metadata`. Chạy thử trực tiếp:

```
TranTuanAnh:   chunks=14  removed_flag=False  size_after=14  -> BUG: không xóa được
NguyenXuanDuc: chunks=14  removed_flag=True   size_after=0   -> OK xóa đúng
Tôi:                                                          -> OK (đã có test riêng, xem mục 6)
```

→ Nếu chạy `delete_document()` sau khi `build_knowledge_base()` thật, nhánh Trần Tuấn Anh sẽ **không xóa được gì cả**, dù `tests/test_solution.py` vẫn xanh 100%. Đây là ví dụ cụ thể cho lý do cần bài test phụ ngoài bộ test được cấp sẵn.

**Quan sát khác (không phải lỗi, chỉ là điểm khác biệt):**
- Trần Tuấn Anh là người duy nhất trong nhóm thật sự implement nhánh ChromaDB (`collection.query`, chuyển `distance → score`); ba người còn lại đều fallback in-memory.
- `ChunkingStrategyComparator` của Trần Tuấn Anh trả thêm `num_chunks`, `max_length`, `min_length` — nhiều thông tin hơn yêu cầu tối thiểu của đề bài.
- Phổ Hiếu Anh là người duy nhất tự động hoá checklist `docs/DATA_COLLECTION.md` bằng `scripts/validate_metadata.py` (exit code 1 nếu sai) thay vì kiểm tra tay.

## 4. Kết quả benchmark (chạy thực tế — cùng corpus, cùng câu hỏi, cùng MockEmbedder)

| Biến thể | Số chunk | Hit@1 | Hit@3 |
|---|---:|---:|---:|
| Tôi — `RecursiveChunker(400)` | 67 | 0/5 | 2/5 |
| Trần Tuấn Anh — `RecursiveChunker(500)` | 51 | 1/5 | 2/5 |
| Nguyễn Xuân Đức — `RecursiveChunker(400)` | 67 | 0/5 | 2/5 |
| Phổ Hiếu Anh baseline — `RecursiveChunker(500)` dense-only *(ablation)* | 51 | 1/5 | 2/5 |
| Phổ Hiếu Anh HYBRID — `PolicySectionChunker` + contextual prefix + BM25/RRF | 71 | 1/5 | 2/5 |

Chi tiết từng câu (V = trúng, x = trượt), giống nhau ở cả 5 biến thể về việc **Q2 và Q3 luôn Hit@3** nhờ `metadata_filter`, còn Q1/Q4/Q5 thất thường:

| # Câu hỏi | Lọc metadata | Kết quả chung |
|---|---|---|
| Q1 — thời hạn trả hàng | không | Chỉ 2/5 biến thể Hit@1 (Trần Tuấn Anh, Phổ Hiếu Anh baseline) |
| Q2 — Tiki xử lý gian lận | `customer_role=seller` | **Cả 5/5 biến thể Hit@3**, không biến thể nào Hit@1 |
| Q3 — thanh toán Apple Pay | `customer_role=buyer` | 2/5 Hit@3 (tôi, Đức); còn lại trượt cả top-3 |
| Q4 — hàng cấm | không | **0/5 biến thể** trúng top-3 |
| Q5 — khiếu nại vận chuyển | không | **0/5 biến thể** trúng top-3 |

## 4b. Xác nhận bằng embedder thật (`OpenAIEmbedder`, `text-embedding-3-small`)

Chạy lại đúng 5 câu hỏi trên bằng embedder ngữ nghĩa thật (không phải mock) để tách bạch "do chunking" hay "do embedder":

| Biến thể | Chunking | Hit@1 | Hit@3 |
|---|---|---:|---:|
| Mock (mục 4) — bất kỳ chiến lược nào trong 5 | — | 0-1/5 | 2/5 |
| **OpenAIEmbedder — `RecursiveChunker(400)`** | (giống chiến lược của tôi) | **4/5** | **4/5** |

Đổi duy nhất embedder (giữ nguyên chunking, giữ nguyên 5 câu hỏi, giữ nguyên corpus) đưa Hit@1 từ 0/5 lên 4/5 — xác nhận trực tiếp giả thuyết ở mục 5.1: **embedder là nút thắt chính, không phải chunking.** Chi tiết từng câu + phân tích lỗi Q4 (tài liệu gold không lọt top-3 dù dùng embedder thật) ở `REPORT_CANHAN.md` mục 5.

## 5. Bài học rút ra

1. **Chunking không phải nút thắt chính — đã xác nhận bằng embedder thật (mục 4b).** Cả 5 cách chunk khác nhau khi dùng mock đều dừng ở Hit@3 = 2/5; đổi sang `OpenAIEmbedder` mà giữ nguyên chunking, Hit@3 nhảy lên 4/5. Kết luận này khớp với cảnh báo trong README lab, trùng độc lập với kết luận của Nguyễn Xuân Đức (báo cáo trung thực 0/10), và nay có bằng chứng thực nghiệm trực tiếp chứ không chỉ suy luận.
2. **Metadata filter là công cụ hiệu quả nhất đo được**, không phải chunking. Q2/Q3 (có filter) đạt Hit@3 tốt hơn hẳn Q1/Q4/Q5 (không filter) ở mọi biến thể mock — filter thu hẹp ứng viên *trước khi* so vector nhiễu, nên tác dụng độc lập với chất lượng embedding.
3. **Hybrid BM25+RRF của Phổ Hiếu Anh là hướng đúng về lý thuyết** (BM25 không cần hiểu ngữ nghĩa, chỉ cần khớp từ hiếm/số liệu — miễn nhiễm một phần với embedder kém), nhưng trên corpus+câu hỏi của nhóm mình, lần chạy mock **chưa cho thấy cải thiện rõ** so với baseline dense-only (1/5 ngang nhau) — vẫn cần chạy Hybrid với embedder thật (chưa làm) để tách bạch đóng góp thật của BM25 khỏi nhiễu do mock.
4. **`Q4` (hàng cấm) vẫn thất bại kể cả với embedder thật** (Hit@1 = Hit@3 = 4/5, riêng Q4 trượt cả top-3) — đây là ứng viên tốt nhất cho "Bài tập 3.5 — Phân tích lỗi" của nhóm, vì đã loại được nguyên nhân "do mock". Nguyên nhân thật: hai tài liệu cùng đề cập "hàng hóa bị cấm" ở hai mức chi tiết khác nhau (câu tổng quát trong `tiki-seller-rights-obligations` vs. danh mục cụ thể trong `shopee-prohibited-products-policy`); câu hỏi diễn đạt chung chung nên embedding kéo về phía câu tổng quát thay vì tài liệu gold chứa toàn danh từ riêng (súng, ma túy...). Xem chi tiết ở `REPORT_CANHAN.md` mục 5.

## 6. Bài test phụ đã thêm (`tests/test_extra_coverage.py`)

9 test, chạy trên `src/` của riêng tôi, lấy cảm hứng trực tiếp từ việc đọc chéo 3 nhánh còn lại:

| Test | Vì sao thêm |
|---|---|
| `TestDeleteDocumentThroughIngestPipeline` (2 test) | Phát hiện bug ở nhánh Trần Tuấn Anh (mục 3) — test gốc không đi qua `ingest.chunk_document()` nên không lộ ra |
| `TestRecursiveChunkerRespectsSize` (2 test) | Test gốc không có trường hợp "một token dài hơn chunk_size, không separator nào cắt được" — dễ vỡ nếu hard-split cài sai |
| `TestSentenceChunkerRunOnText` | Văn bản không có dấu câu — edge case không có trong `SAMPLE_TEXT` của test gốc |
| `TestSearchWithFilterEmptyDictSameAsNone` | `metadata_filter={}` là giá trị hay bị code khác xử lý nhầm thành "lọc mọi thứ" thay vì "không lọc" |
| `TestAgentEmptyStoreDoesNotCrash` | Test gốc luôn có ≥3 tài liệu trong store; chưa test knowledge base rỗng |
| `TestChunkingStrategyComparatorOnRealPolicyText` (2 test) | Test gốc chỉ chạy trên đoạn văn tổng hợp ngắn; thêm test trên văn bản K4 thật (`returns-policy.md`) để kiểm tra thuộc tính khách quan (không mất/bịa nội dung, recursive không vượt size nhiều hơn fixed) |

Kết quả: **9/9 pass** trên `src/` của tôi. Chạy cùng bộ này (đã đối chiếu 2 test đầu) lên `store.py` của Trần Tuấn Anh cho thấy bug ở mục 3.

```
pytest tests/test_extra_coverage.py -v
# 9 passed
```

## 7. Khả năng tái lập

Script dùng để tạo bảng ở mục 4 trích code từng nhánh bằng `git show <branch>:src/*.py` vào các package độc lập rồi chạy cùng corpus/câu hỏi/embedder — không sửa logic của ai. Không commit script này vào repo (vì nó phụ thuộc bản sao tạm thời code của người khác, không phải một phần bài nộp cá nhân); có thể cung cấp lại nếu nhóm muốn chạy lại hoặc mở rộng sang `EMBEDDING_PROVIDER=local`.
