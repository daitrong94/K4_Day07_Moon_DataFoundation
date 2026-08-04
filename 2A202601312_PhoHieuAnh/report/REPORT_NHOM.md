# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** K4-Moon
**Thành viên:**
| # | Họ tên | MSSV | Nhánh git | Chiến lược phụ trách |
|---|---|---|---|---|
| 1 | Phó Hiếu Anh | 2A202601312 | `feat/2A202601312-phohieuanh` | `PolicySectionChunker` + contextual prefix + Hybrid BM25/RRF (custom) |
| 2 | Trần Tuấn Anh | 2A202601086 | `2a202601086-TranTuanAnh` | `RecursiveChunker` + metadata pre-filter (+ nhánh ChromaDB thật) |
| 3 | Nguyễn Xuân Đức | 2A202601112 | `NguyenXuanDuc` | `RecursiveChunker(chunk_size=400)` |
| 4 | Hoàng Trọng Đại | — | `main` | `RecursiveChunker(400)` + **chạy đối chứng bằng embedder thật (OpenAI)** + đọc chéo 4 nhánh |

**Ngày:** 2026-08-04

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:** Chính sách **đổi trả – bảo hành – giao hàng** của ba nhà bán lẻ điện máy trực tuyến Việt Nam (CellphoneS, Di Động Việt, Hoàng Hà Mobile), cộng quy chế hoạt động sàn để có góc nhìn `customer_role=both`.

### Danh sách tài liệu (Data Inventory)

9 tài liệu, tổng **88.065 ký tự**. Thu thập bằng `scripts/fetch_public_pages.py` (kiểm tra `robots.txt`, delay 1,5 giây/request), làm sạch bằng `scripts/clean_crawled.py`. Danh sách URL nguồn: `data/urls.csv`; kiểm kê: `data/k4_ecommerce/sources.csv`.

| # | Tên tài liệu | doc_id | Nguồn | Ngày lấy | Số ký tự | customer_role | category |
|---|---|---|---|---|---:|---|---|
| 1 | Chính sách bảo hành và đổi trả sản phẩm | `cps-chinh-sach-bao-hanh` | [cellphones.com.vn](https://cellphones.com.vn/chinh-sach-bao-hanh) | 2026-08-03 | 1.118 | buyer | warranty |
| 2 | Chính sách hủy giao dịch, đổi trả hàng | `cps-chinh-sach-doi-tra` | [cellphones.com.vn](https://cellphones.com.vn/quy-che-hoat-dong-ung-dung-cellphones/chinh-sach-doi-tra) | 2026-08-03 | 3.935 | buyer | returns |
| 3 | Chính sách giao hàng | `cps-chinh-sach-giao-hang` | [cellphones.com.vn](https://cellphones.com.vn/chinh-sach-giao-hang) | 2026-08-03 | 11.522 | buyer | shipping |
| 4 | Hướng dẫn hủy giao dịch và đổi trả | `cps-huy-giao-dich-doi-tra` | [cellphones.com.vn](https://cellphones.com.vn/huong-dan-huy-giao-dich-doi-tra) | 2026-08-03 | 5.872 | buyer | returns |
| 5 | Quy chế hoạt động ứng dụng CellphoneS | `cps-quy-che-hoat-dong` | [cellphones.com.vn](https://cellphones.com.vn/quy-che-hoat-dong-ung-dung-cellphones) | 2026-08-03 | 29.325 | both | platform-rules |
| 6 | Chính sách bảo hành đổi trả máy qua sử dụng | `ddv-bao-hanh-doi-tra-may-cu` | [didongviet.vn](https://didongviet.vn/chinh-sach-bao-hanh-doi-tra-may-qua-su-dung.html) | 2026-08-03 | 11.529 | buyer | warranty |
| 7 | Chính sách bảo hành và đổi trả máy mới | `ddv-bao-hanh-doi-tra-may-moi` | [didongviet.vn](https://didongviet.vn/chinh-sach-bao-hanh-dien-thoai.html) | 2026-08-03 | 15.582 | buyer | warranty |
| 8 | Chính sách bao xài đổi trả 15/30 ngày | `hhm-bao-xai-doi-tra-15-ngay` | [hoanghamobile.com](https://hoanghamobile.com/tin-tuc/chinh-sach-bao-xai-doi-tra-trong-15-ngay-dau-tai-hoang-ha-mobile/) | 2026-08-03 | 2.933 | buyer | returns |
| 9 | Chính sách bảo hành | `hhm-chinh-sach-bao-hanh` | [hoanghamobile.com](https://hoanghamobile.com/tin-tuc/chinh-sach-bao-hanh-tai-hoang-ha-mobile/) | 2026-08-03 | 6.249 | buyer | warranty |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa **trang chính sách công khai**, không cần đăng nhập, không có dữ liệu cá nhân/thông tin đăng nhập/tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` trong metadata (`document_version=not-stated` vì các trang này không công bố số phiên bản — đúng quy ước ở `docs/DATA_COLLECTION.md`).
- [x] **Đã tôn trọng `robots.txt`:** Thế Giới Di Động, FPT Shop, Sendo, Điện Máy Xanh, PNJ, Coolmate… đều `Disallow` trang chính sách nên bị loại khỏi corpus dù đúng chủ đề.

### Cấu trúc Metadata (Metadata Schema)

Schema được khai báo trong [`data/k4_ecommerce/metadata_schema.json`](../data/k4_ecommerce/metadata_schema.json) và **được ép bằng `scripts/validate_metadata.py`** — không phải mô tả suông. Validator kiểm kiểu, enum, regex, `doc_id` không trùng, và `sources.csv` khớp 1-1 với file `.md`; trả exit code 1 nếu sai. Đây chính là "Checklist trước benchmark" ở `docs/DATA_COLLECTION.md` được tự động hóa.

| Trường | Kiểu | Bắt buộc | Ví dụ | Tại sao hữu ích cho truy xuất? |
|---|---|:---:|---|---|
| `doc_id` | slug (duy nhất) | ✔ | `hhm-bao-xai-doi-tra-15-ngay` | Khóa để `delete_document()` xóa và để chấm Hit@3 theo tài liệu gold. |
| `title` | string | ✔ | `Chính sách bao xài đổi trả 15/30 ngày` | Đưa vào tiền tố ngữ cảnh của mỗi chunk. |
| `source_url` | url `^https://` | ✔ | `https://hoanghamobile.com/tin-tuc/...` | Truy vết câu trả lời về trang gốc. **K4 bắt buộc.** |
| `retrieved_at` | date `YYYY-MM-DD` | ✔ | `2026-08-03` | Kiểm tra độ mới. **K4 bắt buộc.** |
| `document_version` | date \| `not-stated` | ✔ | `2022-12-12` | **Ngày hiệu lực do chính trang công bố**, không phải ngày ta crawl. **K4 bắt buộc.** |
| `customer_role` | enum `buyer\|seller\|both` | ✔ | `both` | **Trường lọc bắt buộc của K4.** Tách câu hỏi người mua khỏi tài liệu quy chế. |
| `category` | enum 6 giá trị | ✔ | `shipping` | Ngăn câu hỏi giao hàng bị kéo về tài liệu đổi trả. |
| `retailer` | enum `cellphones\|didongviet\|hoanghamobile` | ✔ | `hoanghamobile` | Câu hỏi hay nêu đích danh thương hiệu; cả 3 bên đều có "phí nhập lại" nhưng **con số khác nhau** → không lọc thì rất dễ đúng chủ đề mà sai thương hiệu. |
| `language` | enum `vi\|en` | ✔ | `vi` | Giữ chỗ để mở rộng song ngữ mà không đổi schema. |
| `chunk_index` | int | – | `7` | Do `ingest` gắn; ghép lại ngữ cảnh liền kề. |

**Giá trị `document_version` là thật, không phải điền cho có** — trích từ chính nội dung trang:

| doc_id | document_version | Câu trong trang |
|---|---|---|
| `cps-chinh-sach-giao-hang` | `2022-12-12` | "Hiệu lực áp dụng: Kể từ ngày 12/12/2022 đến khi có thông báo thay thế mới." |
| `cps-quy-che-hoat-dong` | `2022-03-10` | "Hiệu lực áp dụng: Kể từ ngày 10/03/2022…" |
| `hhm-chinh-sach-bao-hanh` | `2022-06-08` | "Áp dụng từ ngày 08/06/2022:" |
| `hhm-bao-xai-doi-tra-15-ngay` | `2022-06-08` | "*Cập nhật từ 08/06/2022" |
| 5 tài liệu còn lại | `not-stated` | Trang không công bố ngày hiệu lực — ghi trung thực thay vì bịa. |

> **Giới hạn thành thật về `customer_role`:** corpus này là **nhà bán lẻ**, không phải sàn nhiều người bán, nên thực tế chỉ sinh ra `buyer` và `both`; giá trị `seller` có trong enum nhưng chưa có tài liệu nào dùng. Muốn có tài liệu `seller` thật thì phải lấy từ seller-center của một sàn — mà các sàn đó đều `Disallow` trong `robots.txt` (xem checklist trên).

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy trên **toàn bộ 9 tài liệu** (88.065 ký tự), embedder `AITeamVN/Vietnamese_Embedding` (1024 chiều, GPU). Lệnh tái lập: `HF_HOME=./.hf-cache .venv/bin/python scripts/run_benchmark.py`.

| Chiến lược | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|-------------|------------|-------------------|
| `FixedSizeChunker(500, 50)` | 199 | 490 | ❌ Cắt giữa mệnh đề — mức phí bị tách khỏi tên nhóm sản phẩm |
| `SentenceChunker(3)` | 210 | 417 | ⚠️ Câu trọn vẹn, nhưng gộp cuối điều khoản này với đầu điều khoản kia |
| `RecursiveChunker(500)` | 216 | 406 | ⚠️ Tôn trọng đoạn văn, vẫn không biết ranh giới điều khoản |
| `PolicySectionChunker(500)` | 279 | 313 | ✅ Mỗi chunk = một điều khoản |
| `PolicySectionChunker` + contextual prefix | 279 | 381 | ✅ Điều khoản + tự mang theo ngữ cảnh tài liệu |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Phó Hiếu Anh** *(corpus A — 9 chính sách bán lẻ)*
- **Loại chiến lược:** Custom — `PolicySectionChunker` + contextual prefix (`src/custom_chunking.py`)
- **Mô tả & lý do chọn cho chủ đề này:** Trang chính sách bán lẻ là một chuỗi điều khoản ngắn, tự chứa ("2.1 Thời gian đổi trả", "A. QUYỀN LỢI"). Cắt theo ký tự làm mức phí "trừ 20%" rời khỏi dòng nêu nhóm sản phẩm nó áp dụng, nên chiến lược này cắt theo **tiêu đề điều khoản** thay vì theo độ dài; điều khoản quá ngắn được gộp với điều khoản kế, quá dài thì rơi về `RecursiveChunker`. Sau đó mỗi chunk được **gắn tiền tố ngữ cảnh** `[title | category | customer_role]` trước khi embed — kỹ thuật contextual retrieval của Anthropic (giảm 35% số lần truy xuất trượt), biến một chunk trơ như "trừ phí 20%" thành một chunk tự khai báo nó thuộc chính sách nào, của ai.
- **Code snippet:**
```python
class PolicySectionChunker:
    def chunk(self, text: str) -> list[str]:
        chunks, pending = [], ""
        for section in self._sections(text):          # cắt tại dòng tiêu đề điều khoản
            merged = f"{pending}\n{section}".strip() if pending else section
            if len(merged) < self.min_chunk_size:
                pending = merged                       # quá ngắn -> gộp tiếp
                continue
            pending = ""
            if len(merged) > self.chunk_size:
                chunks.extend(self._fallback.chunk(merged))   # quá dài -> recursive
            else:
                chunks.append(merged)
        if pending:
            chunks.append(pending)
        return chunks

# và trước khi embed:
content = f"[{title} | {category} | {customer_role}]\n{piece}"
```

**Thành viên 2 — Trần Tuấn Anh** *(corpus B — 8 chính sách Shopee/Tiki)*
- **Loại chiến lược:** `RecursiveChunker` + **metadata pre-filtering** theo `customer_role`
- **Mô tả & lý do chọn cho chủ đề này:** Ưu tiên giữ nguyên cấu trúc tiêu đề (`\n\n`, `\n`) và trọn vẹn từng điều khoản chính sách, sau đó **thu hẹp tập ứng viên bằng metadata trước khi tính similarity**. Lập luận cốt lõi của bạn ấy: corpus Shopee/Tiki trộn lẫn tài liệu người mua và người bán nói cùng một trường từ vựng ("đơn hàng", "hoàn tiền", "vi phạm"), nên semantic search thuần rất dễ trả lời câu hỏi của người bán bằng quy định của người mua — filter `customer_role` cắt hẳn nhóm tài liệu sai vai trò ra khỏi cuộc thi điểm.
- **Code snippet:**
```python
# Bench.py — tìm kiếm có/không pre-filter tùy câu hỏi
if meta_filter:
    results = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter)
else:
    results = store.search(query, top_k=3)
```
- **Kết quả bạn ấy tự báo cáo:** 42/42 test pass; **4/5** câu có chunk liên quan trong top-3; 2/2 câu có dùng filter (`seller` cho Q2, `buyer` cho Q3) đạt **Hit@1**. Câu trượt là Q4 (hàng cấm).
- **⚠️ Đính chính sau khi nhóm chạy lại (xem hộp bên dưới):** con số trên **không** được sinh ra bởi cấu hình mô tả ở trên. `Bench.py` thực tế chạy bằng `MockEmbedder` và `FixedSizeChunker(500, 50)`.

> #### Kiểm chứng: kết quả của `Bench.py` được sinh bằng MockEmbedder, không phải embedder ngữ nghĩa
>
> Khi khôi phục corpus B để chạy lại, nhóm phát hiện điểm số trong `Bench.py` **trùng khớp tới 3 chữ số thập phân ở cả 5 câu** với một lần chạy bằng `MockEmbedder` trên harness của Hiếu Anh:
>
> | Câu | Điểm trong báo cáo `Bench.py` | Chạy lại `run_benchmark.py`, backend **mock**, `fixed_500_50` |
> |---|---:|---:|
> | 1 | 0.3468 | **0.347** |
> | 2 | 0.2290 | **0.229** |
> | 3 | 0.3050 | **0.305** |
> | 4 | 0.3823 | **0.382** |
> | 5 | 0.1597 | **0.160** |
>
> Nguyên nhân nằm ngay trong mã nguồn `Bench.py`, không phải suy đoán:
> - `get_embedder()` trả `MockEmbedder()` khi biến môi trường `EMBEDDING_PROVIDER` **không được đặt** — và đó là mặc định.
> - `run_benchmark()` gọi `build_knowledge_base(data_dir, embedding_fn=embedder)` **không truyền `chunker`**, nên `ingest.py` rơi về `chunker = chunker or FixedSizeChunker()` = `FixedSizeChunker(500, 50)` — **không phải** `RecursiveChunker` như phần mô tả chiến lược ghi.
> - Hàm `simple_llm` chỉ **echo lại dòng ngữ cảnh đầu tiên** (`f"[Gold Grounded Answer] dựa trên chunk truy xuất được: {context_lines[0][:150]}..."`), nên cột "Câu trả lời của Agent" trong báo cáo — vốn đọc rất trôi chảy và đúng gold answer — không thể là output thật của đoạn mã này.
>
> `MockEmbedder` băm MD5 nên **xác định (deterministic)**: bất kỳ ai chạy mock trên cùng corpus + cùng câu hỏi + cùng chunker đều ra đúng dãy số đó. Đây là lý do kiểm chứng này đáng tin.
>
> **Xác nhận độc lập:** Hoàng Trọng Đại phát hiện **cùng lỗi này** khi đọc chéo code, hoàn toàn tách biệt với đường kiểm chứng bằng số ở trên — `report/SO_SANH_NHOM.md` mục 2 ghi: *"`Bench.py` thực chất gọi `build_knowledge_base()` **không truyền chunker** → chạy `FixedSizeChunker` mặc định, lệch với chiến lược `RecursiveChunker` ghi trong `REPORT_NHOM.md`"*. Hai người, hai phương pháp (một đọc code, một khớp số), cùng một kết luận.
>
> **Đã được sửa:** commit `edb85ba` trên `main` truyền `chunker=RecursiveChunker(chunk_size=500)` và viết lại `simple_llm` cho khớp format prompt thật của `KnowledgeBaseAgent.answer()`.
>
> **Nhóm giữ nguyên phát hiện này trong báo cáo thay vì lặng lẽ sửa số**, vì nó dẫn thẳng tới bài học phương pháp quan trọng nhất của lab (xem Phần 4): *4/5 và 0/5 của hai bạn cùng dùng mock **không** phản ánh chênh lệch chất lượng — cả hai đều là kết quả ngẫu nhiên.*

**Thành viên 3 — Nguyễn Xuân Đức** *(corpus B — 8 chính sách Shopee/Tiki)*
- **Loại chiến lược:** `RecursiveChunker(chunk_size=400)` — chạy trên **`MockEmbedder`**
- **Mô tả & lý do chọn cho chủ đề này:** Chọn chunk 400 ký tự vì chính sách TMĐT được viết thành các gạch đầu dòng ngắn; recursive ngắt ưu tiên tại `\n\n` rồi `\n` nên không làm nát điều khoản, mà chunk vẫn đủ nhỏ để nhét nhiều chunk vào ngữ cảnh LLM. Bạn ấy **không cài được embedder thật** (chưa cài `requirements-local.txt`) nên toàn bộ benchmark chạy bằng `MockEmbedder` (băm MD5).
- **Kết quả bạn ấy tự báo cáo:** 42/42 test pass; **0/5** câu có chunk liên quan trong top-3. Baseline chunking đo trên `shopee-return-refund-policy.md`: fixed 30 chunk (195,1 ký tự) / sentences 22 chunk (198,3) / recursive 35 chunk (123,9).
- **Vì sao nhóm giữ lại kết quả 0/5 thay vì bỏ đi:** đây là **thí nghiệm đối chứng** — xem mục "Bài học rút ra" ở Phần 4.

**Thành viên 4 — Hoàng Trọng Đại** *(corpus B — nhánh `main`)*
- **Loại chiến lược:** `RecursiveChunker(400)`, cộng thêm **vai trò đối chứng của cả nhóm**: đọc chéo code cả 4 nhánh, trích code từng người bằng `git show <branch>:src/*.py` ra package riêng rồi chạy lại trên **cùng corpus, cùng 5 câu hỏi, cùng embedder** để so sánh công bằng (`report/SO_SANH_NHOM.md` trên nhánh `main`).
- **Đóng góp quyết định — lần chạy bằng embedder THẬT:** bạn ấy là người duy nhất chạy được `OpenAIEmbedder` (`text-embedding-3-small`). Giữ nguyên chunking, nguyên corpus, nguyên 5 câu hỏi, **chỉ đổi embedder**:

  | Biến thể | Hit@1 | Hit@3 |
  |---|---:|---:|
  | Mock — bất kỳ chiến lược nào trong 5 | 0–1/5 | 2/5 |
  | **OpenAI `text-embedding-3-small` + `RecursiveChunker(400)`** | **4/5** | **4/5** |

  Đây là **phép đo tách biến sạch nhất mà nhóm có**: 2/5 → 4/5 chỉ do đổi embedder.
- **Bug thật bạn ấy phát hiện khi đọc chéo:** `delete_document` trên nhánh Trần Tuấn Anh lọc theo `record["id"]`, trong khi pipeline thật (`ingest.build_knowledge_base`) sinh chunk-id dạng `"policy-x::chunk_0"` và chỉ gắn `doc_id` vào **metadata**. Hệ quả: chạy `delete_document()` sau `build_knowledge_base()` **không xóa được gì**, dù `tests/test_solution.py` vẫn xanh 100% (vì test gốc gọi thẳng `add_documents()` với `Document.id == doc_id`). Bạn ấy viết `tests/test_extra_coverage.py` để bắt đúng ca này.
- **Bạn ấy cũng đã sửa `Bench.py` trên `main`** (commit `edb85ba`): cả lỗi `target_doc_id` ở Q4 lẫn lỗi thiếu tham số `chunker` — xem hai hộp kiểm chứng bên dưới.

### So Sánh Giữa Các Thành Viên

**a) So sánh theo thành viên** (mỗi người một chiến lược, cùng bộ 5 câu hỏi chung của nhóm):

| Thành viên | Chiến lược **thực tế đã chạy** | Embedder **thực tế** | Corpus | Hit@3 | Grounded@3 | Điểm truy xuất (/10) |
|---|---|---|---|:---:|:---:|:---:|
| **Phó Hiếu Anh** | `PolicySectionChunker` + contextual prefix | `AITeamVN/Vietnamese_Embedding` (**thật**, 1024d) | A + B | **5/5** | **1.00** | **10/10** |
| **Hoàng Trọng Đại** | `RecursiveChunker(400)` | `OpenAI text-embedding-3-small` (**thật**) | B | **4/5** | — *(không đo)* | **8/10** |
| **Trần Tuấn Anh** | `FixedSizeChunker(500, 50)` *(mặc định của `ingest.py`)* | `MockEmbedder` (băm MD5) | B | 4/5 *(tự báo cáo)* | 0.60 *(nhóm đo lại)* | — *(xem ghi chú)* |
| **Nguyễn Xuân Đức** | `RecursiveChunker(400)` | `MockEmbedder` (băm MD5) | B | 0/5 | 0.00 | — *(xem ghi chú)* |

**Ghi chú về cột điểm:** nhóm **không chấm điểm truy xuất** cho hai lần chạy bằng `MockEmbedder`, vì thứ hạng khi đó là ngẫu nhiên — chấm 8/10 hay 0/10 đều không phản ánh chất lượng chiến lược. Đây là quyết định có chủ ý, lý do ngay dưới đây.

**Hai người dùng embedder thật, hai mô hình khác nhau, kết quả gần nhau (5/5 và 4/5)** — trong khi hai người dùng mock cho 4/5 và 0/5, tức **biên độ rộng hơn cả khoảng cách giữa hai embedder thật**. Riêng điều đó đã đủ nói rằng con số từ mock không mang thông tin.

> **Điều so sánh này làm lộ ra — và nó NGƯỢC với kết luận nhóm định viết ban đầu:**
>
> Bản nháp đầu tiên của báo cáo này kết luận: *"khoảng cách 4/5 vs 0/5 chứng minh embedder quan trọng hơn chunking"*. **Kết luận đó sai.** Trần Tuấn Anh và Nguyễn Xuân Đức **dùng CÙNG một embedder** (`MockEmbedder`) — nên chênh lệch 4/5 vs 0/5 giữa hai bạn hoàn toàn là **may rủi**, sinh ra từ việc hai chunker khác nhau cắt ra những chuỗi khác nhau rồi được băm MD5 thành các vector ngẫu nhiên khác nhau.
>
> Chạy lại cả 6 chiến lược trên corpus B **bằng backend mock** cho thấy rõ biên độ may rủi đó:
>
> | Chiến lược (backend **mock**) | Hit@3 | Grounded@3 |
> |---|---:|---:|
> | `fixed_500_50` *(đúng cấu hình `Bench.py` của Tuấn Anh)* | **1.00** | 0.60 |
> | `sentences_3` | 0.40 | 0.00 |
> | `recursive_500` | 0.40 | 0.00 |
> | `policy_sections` | 0.80 | 0.20 |
> | `policy_contextual` | 0.40 | 0.20 |
> | `policy_contextual_hybrid` | 0.40 | 0.20 |
>
> **Với embedder ngẫu nhiên, Hit@3 vẫn dao động 0.40 – 1.00 tùy chunker.** Nói cách khác, một mô hình nhúng **không hiểu gì về ngôn ngữ** vẫn có thể chạm điểm cao nếu chọn đúng (may) cấu hình. Chỉ `Grounded@3` là trụ được — mock cao nhất chỉ **0.60**, trong khi embedder thật đạt **1.00** ở cả 5 câu.
>
> **Đối chiếu chéo với số của Hoàng Trọng Đại — và một khác biệt cần nói thẳng.** Bạn ấy chạy lại cả 4 nhánh dưới mock và thu được Hit@3 = **2/5 cho mọi biến thể**, trong khi harness của tôi cho 0.40 – 1.00. Hai dãy số này **không mâu thuẫn**, chúng chấm theo hai định nghĩa gold khác nhau:
> - Bộ của bạn ấy giữ `target_doc_id = "k4-prohibited-products"` ở Q4 (id không tồn tại) nên **Q4 luôn trượt với mọi biến thể** — khớp đúng dòng "Q4 — 0/5 biến thể" trong `SO_SANH_NHOM.md`. Bộ của tôi đã sửa id nên Q4 có thể đạt.
> - Harness của tôi tính Hit@3 là "có chunk thuộc **tập** `gold_doc_ids` trong top-3" (một số câu có 2 tài liệu gold), còn bạn ấy so với **một** `target_doc_id` duy nhất — chặt hơn.
>
> Bài học phụ, nhưng đắt: **hai bảng điểm cùng tên "Hit@3" mà lệch nhau tới 3/5 câu chỉ vì định nghĩa nhãn gold.** Muốn so điểm giữa các thành viên thì phải chốt **cùng file benchmark**, không chỉ chốt cùng câu hỏi.
>
> **Bằng chứng sạch nhất về nguyên nhân lại đến từ Hoàng Trọng Đại**, vì bạn ấy đổi **đúng một biến**: giữ nguyên `RecursiveChunker(400)`, nguyên corpus, nguyên 5 câu hỏi, chỉ thay mock → `OpenAI text-embedding-3-small`, và Hit@1 nhảy **0/5 → 4/5**. Đây mới là phép đo cho phép nói "embedder là nút thắt", chứ không phải phép so 4/5 với 0/5 giữa hai người **cùng dùng mock** như bản nháp đầu của báo cáo này đã làm.
>
> **Bài học đúng, thay cho kết luận sai ban đầu:** một điểm số chỉ có nghĩa khi so được với **đường cơ sở ngẫu nhiên (random baseline)**, và một so sánh chỉ kết luận được nhân quả khi **đổi đúng một biến**. Nhóm có sẵn cả hai thứ mà suýt bỏ qua: đường cơ sở là lần chạy mock của Nguyễn Xuân Đức, phép tách biến là lần chạy OpenAI của Hoàng Trọng Đại.

**b) So sánh theo chiến lược.** Cùng corpus, cùng 5 câu hỏi, cùng embedder — chỉ khác chiến lược chia nhỏ. Đo bằng `scripts/run_benchmark.py`:

| Chiến lược | Hit@3 | MRR@3 | Grounded@3 | Điểm mạnh | Điểm yếu |
|---|---:|---:|---:|---|---|
| `fixed_500_50` | 0.80 | 0.60 | 1.00 | Đơn giản nhất, chunk dài nên vô tình chứa nhiều ngữ cảnh | Trượt hẳn Q5 khi không lọc metadata (Hit=0); cắt giữa mệnh đề |
| `sentences_3` | 0.80 | 0.67 | 1.00 | Không bao giờ cắt giữa câu | Gộp cuối điều khoản này với đầu điều khoản kia |
| `recursive_500` | 0.80 | 0.60 | **0.80** | Tôn trọng ranh giới đoạn văn | Grounded thấp nhất — cắt bảng phí ra khỏi dòng nêu nhóm sản phẩm |
| `policy_sections` | 0.80 | 0.80 | 0.80 | MRR cao: chunk đúng được đẩy lên hạng 1 | Chunk ngắn (313 ký tự) nên thiếu ngữ cảnh tài liệu |
| **`policy_contextual`** | **1.00** | **0.87** | **1.00** | Thắng cả 3 chỉ số | Chunk phình thêm ~68 ký tự/chunk; tiền tố lặp lại có thể làm nhiễu nếu corpus lớn |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

`policy_contextual` — và điều đáng nói là **hai cải tiến đóng vai trò khác nhau, đo tách được**:

1. Đi từ `recursive_500` → `policy_sections`: Hit@3 giữ nguyên 0.80 nhưng **MRR nhảy 0.60 → 0.80**. Cắt theo điều khoản không giúp tìm thêm tài liệu mới, nó giúp **đẩy đúng chunk lên hạng 1** — vì chunk giờ là một mệnh đề trọn vẹn thay vì một lát cắt ngẫu nhiên.
2. Đi từ `policy_sections` → `policy_contextual`: **Hit@3 0.80 → 1.00 và Grounded@3 0.80 → 1.00**. Tiền tố ngữ cảnh cứu đúng câu hỏi mà chunk nhỏ bị "mồ côi": chunk chỉ ghi "trừ phí 15%" không có gì cho biết nó thuộc chính sách nào, cho tới khi được gắn `[Chính sách bao xài… | returns | buyer]`.

Nói ngắn: **chia theo cấu trúc cải thiện thứ hạng, gắn ngữ cảnh cải thiện độ phủ.** Chỉ làm một trong hai thì không đạt 1.00.

### Kiểm chứng chéo: chạy lại trên corpus thứ hai

Kết quả trên một bộ dữ liệu chưa chứng minh được điều gì — chiến lược có thể chỉ đang khớp may mắn với đặc thù corpus. Nhóm chạy **cùng harness, cùng 5 chiến lược, cùng embedder** trên một corpus TMĐT thứ hai hoàn toàn độc lập: 8 chính sách Shopee/Tiki (~27.000 ký tự) do **Nguyễn Xuân Đức và Trần Tuấn Anh** thu thập, đặt tại `data/team_k4_corpus/`, bộ câu hỏi riêng tại `data/benchmark_team_corpus.json`.

```bash
.venv/bin/python scripts/run_benchmark.py \
  --data-dir data/team_k4_corpus --benchmark data/benchmark_team_corpus.json
```

| Chiến lược | Corpus A — bán lẻ (9 tl, 88KB)<br>Hit@3 / MRR@3 / Grounded@3 | Corpus B — sàn TMĐT (8 tl, 27KB)<br>Hit@3 / MRR@3 / Grounded@3 |
|---|:---:|:---:|
| `fixed_500_50` | 0.80 / 0.60 / 1.00 | 1.00 / 1.00 / 1.00 |
| `sentences_3` | 0.80 / 0.67 / 1.00 | 1.00 / 1.00 / **0.40** |
| `recursive_500` | 0.80 / 0.60 / 0.80 | 1.00 / 1.00 / 0.80 |
| `policy_sections` | 0.80 / 0.80 / 0.80 | 1.00 / 1.00 / 0.80 |
| **`policy_contextual`** | **1.00 / 0.87 / 1.00** | **1.00 / 1.00 / 1.00** |

**`policy_contextual` là chiến lược DUY NHẤT đạt tối đa cả ba chỉ số trên cả hai corpus.** `fixed_500_50` hoàn hảo ở corpus B nhưng rơi xuống 0.80/0.60 ở corpus A — nếu nhóm chỉ thử một bộ dữ liệu thì đã kết luận sai.

Hai điều corpus thứ hai làm lộ ra mà corpus thứ nhất không thấy được:

**a) Corpus dễ khiến mọi chiến lược trông như nhau.** Ở corpus B, cả 5 chiến lược đều Hit@3 = MRR@3 = **1.00** — không phân biệt được gì. Lý do: 8 tài liệu ngắn, mỗi tài liệu một chủ đề tách bạch, mỗi câu hỏi ứng đúng một tài liệu, không có nguồn gây nhiễu. Corpus A phân biệt được vì có **3 nhà bán lẻ nói cùng chủ đề với số liệu khác nhau** cộng một tài liệu 29KB gần trùng lặp. Bài học phương pháp: muốn benchmark có sức phân biệt thì corpus phải có nhiễu thật, không phải càng sạch càng tốt.

**b') Thử nghiệm bổ sung: hybrid BM25 + RRF — một kết quả ÂM có ích.**

Tài liệu về RAG production khuyến nghị hợp nhất BM25 (từ vựng) với dense (ngữ nghĩa) bằng Reciprocal Rank Fusion, báo cáo +7,4% NDCG trên benchmark TMĐT. Nhóm cài đặt đầy đủ bằng thư viện chuẩn (`src/hybrid.py`, 28 unit test ở `tests/test_hybrid.py`) và đo qua **ba vòng lặp**:

| Vòng | Thiết kế | Corpus A | Corpus B (câu hỏi nhóm) |
|---|---|:---:|:---:|
| — | `policy_contextual` (baseline) | 1.00 / 0.87 / 1.00 | 1.00 / 0.90 / 1.00 |
| v1 | RRF ngang quyền dense–BM25 | **0.80 / 0.80** / 1.00 | **0.80 / 0.80** / 1.00 |
| v2 | + cổng chặn theo tần suất tài liệu | 0.80 / 0.80 / 1.00 | 0.80 / 0.80 / 1.00 |
| v3 | + cổng chỉ mở cho token chứa chữ số | **1.00 / 0.87 / 1.00** | **1.00 / 0.90 / 1.00** |

*(ô ghi Hit@3 / MRR@3 / Grounded@3)*

**v1 làm TỆ ĐI.** Nguyên nhân đo được, không phải phỏng đoán: câu hỏi Q1 *"Điện thoại mua mới được đổi **sang** máy khác trong bao nhiêu ngày?"* — âm tiết `sang` chỉ xuất hiện ở **5/279 chunk**, tức "hiếm" theo mọi ngưỡng thống kê, nên BM25 chấm điểm cao cho các chunk chứa nó. Nhưng `sang` là **hư từ**, không mang thông tin truy xuất. Tiếng Việt tách theo âm tiết khiến hư từ trông y hệt thuật ngữ chuyên ngành — đúng vấn đề mà word segmentation (underthesea/VnCoreNLP) sinh ra để giải quyết.

**v3 sửa được bằng cách thu hẹp phạm vi:** chỉ cho BM25 tham gia khi truy vấn chứa token **có chữ số** — vì các trường hợp dense thật sự mù đều là số (`10km`, `50.000.000`, `15%`, `1800.2097`). Sau đó hybrid **bằng đúng** baseline ở cả ba cấu hình: không hại, nhưng cũng **không lợi**.

**Vì sao không lợi — và đây mới là điều đáng học:** ca lỗi Q3 mà nhóm kỳ vọng hybrid sẽ cứu lại nằm ngoài tầm với của BM25. Corpus có đúng 3 chunk chứa `10km`, và **cả chunk đúng lẫn hai chunk sai đều chứa nó**:

```
=< 10km  ... bán kính =< 10km (ngoại trừ các Huyện Cần Giờ, Củ Chi...)
=< 10km  ... bán kính =< 10km, ngoại trừ các huyện Chương Mỹ, Đan Phượng...
 > 10km  ... Trong vòng 1 - 2 ngày (Khoảng cách >10km)
```

Token phân biệt không phải `10km` mà là **toán tử so sánh `=<` vs `>`** — thứ mà cả embedding lẫn BM25 đều không mã hóa được. Chỉ **cross-encoder reranker**, vốn đọc cặp (câu hỏi, chunk) cùng lúc thay vì mã hóa độc lập, mới phân biệt được chiều so sánh. Đó là hướng đi tiếp theo, ngoài phạm vi lab.

> **Bài học phương pháp:** một kỹ thuật được benchmark quốc tế chứng minh có lợi (+7,4% NDCG) vẫn có thể **vô ích hoặc có hại** trên corpus khác ngôn ngữ và khác dạng lỗi. Nhóm giữ lại `policy_contextual_hybrid` trong harness làm bằng chứng đo đạc, nhưng **chiến lược nộp bài vẫn là `policy_contextual`** vì đơn giản hơn mà kết quả tương đương.

**b) Chỉ còn Grounded@3 phân biệt được — và nó phơi bày `sentences_3`.** Chỉ số này rơi xuống **0.40** ở corpus B trong khi Hit@3 vẫn 1.00: chiến lược tìm **đúng tài liệu** nhưng lấy **sai đoạn**. Chi tiết ở phần Phân tích lỗi (ca lỗi 3).

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

#### Ghi chú trung thực: nhóm có HAI corpus và HAI bộ câu hỏi

Trong quá trình làm, nhóm chia dữ liệu thành hai hướng thay vì một:

| | Corpus A — bán lẻ điện máy | Corpus B — sàn TMĐT |
|---|---|---|
| Tài liệu | 9 tl, 88.065 ký tự (CellphoneS, Di Động Việt, Hoàng Hà Mobile) | 8 tl, ~27.000 ký tự (Shopee, Tiki) |
| Người thu thập | Phó Hiếu Anh | Nguyễn Xuân Đức, Trần Tuấn Anh, Hoàng Trọng Đại |
| Bộ câu hỏi | [`data/k4_ecommerce/benchmark.json`](../data/k4_ecommerce/benchmark.json) | [`data/benchmark_tta_queries.json`](../data/benchmark_tta_queries.json) |
| Ai đã chạy | Phó Hiếu Anh (5 chiến lược) | cả **4/4** thành viên |

**Bộ câu hỏi CHUNG chính thức của nhóm — theo đúng yêu cầu "5 câu hỏi phải trùng nhau" của `docs/SCORING.md` — là bộ trên corpus B**, vì đó là bộ duy nhất cả bốn thành viên đều chạy (Trần Tuấn Anh trong `Bench.py`, Nguyễn Xuân Đức trong `bench.py`, Hoàng Trọng Đại trên `main`, Phó Hiếu Anh trong `scripts/run_benchmark.py`). Kết quả đối chiếu 4 người trên bộ này ở mục **"Kết quả bộ câu hỏi chung — cả 4 thành viên"** bên dưới.

Bộ câu hỏi corpus A dưới đây được giữ lại làm **bộ mở rộng**: nó khó hơn có chủ đích (3 nhà bán lẻ nói cùng chủ đề với số liệu khác nhau) và là bộ duy nhất phân biệt được 5 chiến lược chia nhỏ — xem mục "Kiểm chứng chéo" ở Phần 2 để biết vì sao corpus B **không** phân biệt được.

Bộ câu hỏi máy đọc được: [`data/k4_ecommerce/benchmark.json`](../data/k4_ecommerce/benchmark.json) — mỗi câu kèm `gold_doc_ids` (chấm Hit@3) và `gold_keywords` (chấm Grounded@3).

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Tài liệu chứa thông tin | Filter |
|---|---|---|---|---|
| 1 | Điện thoại mua mới được đổi sang máy khác trong bao nhiêu ngày? | 30 ngày — thời gian đổi mới tiêu chuẩn cho nhóm Điện thoại/Máy tính bảng/Macbook tại CellphoneS | `cps-chinh-sach-doi-tra`, `cps-quy-che-hoat-dong` | – |
| 2 | Nhập lại máy trong 15 ngày đầu tại Hoàng Hà Mobile bị trừ bao nhiêu phần trăm? | Trừ phí **15%** trên giá hiện tại (hoặc giá tại thời điểm mua nếu thấp hơn) | `hhm-bao-xai-doi-tra-15-ngay` | `retailer=hoanghamobile` |
| 3 | Đơn hàng ở khoảng cách xa hơn 10km thì bao lâu được giao tới? | Nội thành HCM/HN: **24–48 giờ** khi >10km (1–2 giờ nếu ≤10km); khu vực khác 1–2 ngày, nội/liên tỉnh 2–5 ngày | `cps-chinh-sach-giao-hang` | – |
| 4 | Máy chưa khui seal và chưa kích hoạt được đổi trả miễn phí trong bao lâu? | **7 ngày đầu tiên**, hoàn tiền 100% | `ddv-bao-hanh-doi-tra-may-moi` | – |
| 5 | Khách hàng muốn hủy đơn hàng đã đặt online thì phải làm gì? | Gọi tổng đài **1800.2097** (Miền Nam) / **1800.2044** (Miền Bắc) hoặc email; hoặc từ chối nhận hàng khi shipper giao | `cps-huy-giao-dich-doi-tra`, `cps-chinh-sach-doi-tra` | `customer_role=buyer` |

Bộ câu hỏi đa dạng theo yêu cầu: 1 câu mơ hồ không nêu thương hiệu (Q1), 1 câu hỏi con số cụ thể có nêu thương hiệu (Q2), 1 câu khác chủ đề hoàn toàn — giao hàng (Q3), 1 câu diễn đạt sát tài liệu (Q4), 1 câu hỏi quy trình (Q5).

### Tổng hợp chất lượng truy xuất của nhóm

Chiến lược `policy_contextual`, top-3, embedder `AITeamVN/Vietnamese_Embedding`:

| # | Top-1 doc_id | Score | Chunk liên quan trong top-3? | Điểm | Ghi chú |
|---|---|---:|:---:|:---:|---|
| 1 | `ddv-bao-hanh-doi-tra-may-cu` | 0.525 | ✅ (hạng 3) | **1** | Top-1 là **nhầm nhà bán lẻ** — xem phân tích lỗi ở Phần 4 |
| 2 | `hhm-bao-xai-doi-tra-15-ngay` | 0.700 | ✅ (hạng 1) | **2** | Chunk hạng 1 chứa đúng câu "trừ phí 15%" |
| 3 | `cps-chinh-sach-giao-hang` | 0.532 | ✅ (hạng 1) | **1** | Đúng tài liệu nhưng hạng 1–2 nói về **≤10km**, ngược câu hỏi |
| 4 | `ddv-bao-hanh-doi-tra-may-moi` | 0.652 | ✅ (hạng 1) | **2** | Hạng 3 chứa nguyên văn "đổi trả miễn phí 7 ngày đầu tiên" |
| 5 | `cps-huy-giao-dich-doi-tra` | 0.439 | ✅ (hạng 1) | **2** | Hạng 1 chứa đủ cả hai số tổng đài |
| | | | **5/5** | **8/10** | |

### Kết quả bộ câu hỏi CHUNG — cả 4 thành viên (corpus B, Shopee/Tiki)

Đây là bảng đối chiếu chính theo `docs/SCORING.md`: cùng 5 câu hỏi, cùng corpus, mỗi người chạy trên **mã nguồn `src` của riêng mình**. Hai cột đầu dùng **embedder thật**, hai cột sau dùng **mock** — đọc bảng phải tách hai nhóm này ra.

| # | Câu hỏi chung của nhóm | Gold answer | Phó Hiếu Anh<br>`policy_contextual`<br>**Vietnamese_Embedding** | Hoàng Trọng Đại<br>`recursive(400)`<br>**OpenAI** | Trần Tuấn Anh<br>`fixed_500_50`<br>*Mock* | Nguyễn Xuân Đức<br>`recursive(400)`<br>*Mock* |
|---|---|---|:---:|:---:|:---:|:---:|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền với đơn giao thành công? | 15 ngày (24 giờ với thực phẩm tươi sống) | ✅ top-1 | ✅ **top-1** (0.599) | ✅ top-3 | ❌ |
| 2 | Nhà bán Tiki bị xử lý thế nào nếu gian lận? | Ngưng hợp tác vĩnh viễn, thu hồi khuyến mãi, phong tỏa sao kê 90 ngày | ✅ top-1 | ✅ **top-1** (0.654, filter `seller`) | ✅ top-1 (filter `seller`) | ❌ |
| 3 | Hạn mức Apple Pay trên Shopee? | 10.000 – 25.000.000 VNĐ, 9 phương thức thanh toán | ✅ top-1 | ✅ **top-1** (0.671, filter `buyer`) | ✅ top-1 (filter `buyer`) | ❌ |
| 4 | Hàng hóa cấm đăng bán gồm những loại nào? | Hàng giả/nhái, vũ khí, ma túy, thuốc lá điện tử… | ✅ top-1 | ❌ **trượt cả top-3** | ❌ | ❌ |
| 5 | Thời gian xử lý khiếu nại vận chuyển tối đa? | 10 ngày làm việc | ✅ top-1 | ✅ **top-1** (0.664) | ✅ top-3 | ❌ |
| | **Hit@3** | | **5/5** | **4/5** | 4/5 *(ngẫu nhiên)* | 0/5 *(ngẫu nhiên)* |
| | **Điểm truy xuất (/10)** | | **10** | **8** | — | — |

*Ghi chú cách đọc:* với Phó Hiếu Anh, ✅ top-1 nghĩa là **tài liệu** hạng 1 đúng tài liệu gold ở cả 5 câu; ở mức **chunk** thì MRR@3 = 0.90, Grounded@3 = 1.00. Hai cột mock được in nhạt có chủ ý — chúng **không phải thước đo chất lượng**, chỉ có mặt để làm đường cơ sở ngẫu nhiên.

**Bốn điều bảng này nói ra mà từng báo cáo riêng lẻ không nói được:**

1. **Q4 là ca lỗi THẬT của cả nhóm, không phải lỗi của riêng ai.** Ban đầu nhóm tưởng Q4 trượt vì `Bench.py` khai `target_doc_id = "k4-prohibited-products"` trong khi id thật là `shopee-prohibited-products-policy` (đã sửa ở commit `edb85ba`). **Nhưng Hoàng Trọng Đại sửa id rồi chạy lại bằng OpenAI embedder thì Q4 vẫn trượt cả top-3.** Vậy đây là lỗi truy xuất thật, đã loại được cả nguyên nhân "do mock" lẫn "do nhãn sai". Nguyên nhân bạn ấy chỉ ra: `tiki-seller-rights-obligations` có **câu tổng quát** "không được kinh doanh hàng hóa bị cấm", còn tài liệu gold chứa **danh mục cụ thể** (súng, ma túy, hàng giả…); câu hỏi diễn đạt chung chung nên embedding kéo về phía câu tổng quát. Đây là ứng viên chính cho Bài 3.5 của nhóm.
2. **Cột của Nguyễn Xuân Đức toàn ❌ nhưng cột "câu trả lời của Agent" trong báo cáo bạn ấy lại toàn đúng** — vì hàm LLM giả lập bắt theo từ khóa câu hỏi chứ không đọc ngữ cảnh truyền vào. Cảnh báo phương pháp cho cả nhóm: **chấm RAG phải chấm trên chunk truy xuất được, không chấm trên câu trả lời sinh ra.**
3. **Hai lần chạy bằng embedder thật cho kết quả gần nhau (5/5 và 4/5) dù dùng hai mô hình khác nhau và hai chiến lược chunking khác nhau** — trong khi hai lần chạy mock chênh nhau 4/5 vs 0/5. Biên độ do *ngẫu nhiên* lớn hơn biên độ do *chiến lược*: dấu hiệu kinh điển rằng bộ benchmark 5 câu này **quá nhỏ để xếp hạng** các chiến lược tốt.
4. **Chỉ Hit@3 thôi thì corpus B không phân biệt được hai người dùng embedder thật.** Phải thêm Grounded@3 (đúng tài liệu *và* đúng đoạn chứa dữ kiện) mới thấy khác biệt — chi tiết ở Phần 2, mục "Kiểm chứng chéo".

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

Có, nhưng **không đều** — và chỗ không đều mới là điều đáng nói. Chạy A/B trên *mọi* chiến lược:

| Chiến lược | Q5 có lọc (`customer_role=buyer`) | Q5 không lọc | Q2 có lọc (`retailer`) | Q2 không lọc |
|---|:---:|:---:|:---:|:---:|
| `fixed_500_50` | 1 / 0.50 | **0 / 0.00** | 1 / 0.50 | 1 / 0.50 |
| `sentences_3` | 1 / **1.00** | 1 / 0.50 | 1 / 0.33 | 1 / 0.33 |
| `recursive_500` | 1 / 0.50 | 1 / 0.33 | 1 / 0.50 | 1 / 0.50 |
| `policy_sections` | 1 / **1.00** | 1 / 0.33 | 1 / 1.00 | 1 / 1.00 |
| `policy_contextual` | 1 / **1.00** | 1 / 0.50 | 1 / 1.00 | 1 / 1.00 |

*(ô ghi `Hit@3 / MRR@3`)*

- **Q5 — lọc giúp mọi chiến lược.** Nặng nhất với `fixed_500_50`: **Hit@3 từ 0 lên 1**, tức là không lọc thì trượt hoàn toàn. Lý do: tài liệu `cps-quy-che-hoat-dong` (29.325 ký tự, 1/3 corpus, `customer_role=both`) chứa lại gần như nguyên văn nội dung hủy giao dịch, nên nó chiếm hết top-3 bằng các bản sao. Lọc `customer_role=buyer` loại đúng tài liệu đó.
- **Q2 — lọc `retailer` không đổi gì cả.** Kết quả trung thực: vì câu hỏi đã nói thẳng "tại Hoàng Hà Mobile", embedder đã tự khớp cụm đó trong tiền tố ngữ cảnh, filter chỉ lặp lại việc mà retrieval đã làm đúng. **Metadata filter chỉ có giá trị khi tín hiệu phân biệt KHÔNG nằm sẵn trong câu chữ của câu hỏi.**
- Suy ra: lợi ích của lọc metadata **tỉ lệ nghịch với chất lượng chunking**. Nó cứu `fixed_500_50` khỏi điểm 0, nhưng chỉ nâng MRR cho `policy_contextual`. Đừng dùng metadata để che khuyết điểm chunking.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Chia theo cấu trúc nâng thứ hạng, gắn ngữ cảnh nâng độ phủ** — đo tách bạch được: `recursive → policy_sections` chỉ đổi MRR (0.60→0.80), `policy_sections → policy_contextual` mới đổi Hit@3 (0.80→1.00).
2. **Embedding đo *cách viết*, không đo *ý nghĩa số học*.** Cặp "15 ngày" vs "30 ngày" đạt cosine **0.8898** và "dưới 10km" vs "xa hơn 10km" đạt **0.8622** — cao hơn hẳn hai câu diễn đạt lại thật sự cùng ý (0.6617 / 0.5531). Đây chính là nguyên nhân gốc của lỗi ở Q3.
3. **Metadata filter là lưới an toàn cho chunking kém, không phải nguồn lợi ích độc lập** — nó cứu `fixed_500_50` khỏi Hit@3=0 ở Q5, nhưng không thêm gì cho `policy_contextual` ở Q2. Trên corpus B, lọc **không đổi kết quả của bất kỳ chiến lược nào** vì câu hỏi đã chứa sẵn từ "người bán".
4. **Kiểm chứng chéo trên corpus thứ hai đổi hẳn kết luận.** `fixed_500_50` đạt 1.00/1.00/1.00 ở corpus B — nếu chỉ thử một bộ dữ liệu, nhóm đã kết luận baseline đơn giản nhất là đủ tốt.
5. **Embedder là nút thắt — và nhóm chứng minh được bằng phép tách đúng một biến.** Hoàng Trọng Đại giữ nguyên `RecursiveChunker(400)`, nguyên corpus, nguyên 5 câu hỏi, **chỉ đổi** `MockEmbedder` → `OpenAI text-embedding-3-small`: Hit@1 nhảy từ **0/5 lên 4/5**. Đây là bằng chứng nhân quả, khác hẳn với việc so điểm giữa hai thành viên đang khác nhau nhiều thứ cùng lúc.
6. **"Câu trả lời đúng" không chứng minh "retrieval đúng".** Báo cáo của Nguyễn Xuân Đức có 0/5 chunk liên quan nhưng 5/5 câu trả lời đúng, vì hàm LLM giả lập bắt theo từ khóa của câu hỏi. Đây là dạng lỗi đánh giá dễ mắc nhất trong RAG và nhóm sẽ demo trực tiếp bằng ca này.
7. **Đọc chéo code bắt được lỗi mà 42/42 test xanh vẫn bỏ lọt.** Hoàng Trọng Đại phát hiện `delete_document` trên một nhánh lọc theo `record["id"]`, nên khi chạy qua pipeline thật (`ingest` sinh chunk-id `"doc::chunk_0"`, `doc_id` nằm trong metadata) thì **không xóa được gì** — trong khi `tests/test_solution.py` vẫn xanh vì test gốc gọi thẳng `add_documents()`. Bài học: **bộ test được cấp sẵn định nghĩa mức tối thiểu, không định nghĩa "đã đúng".**
8. **Cùng một cái tên "Hit@3" mà ra hai bảng điểm lệch nhau tới 3/5 câu**, chỉ vì một bên so với một `target_doc_id` còn một bên so với tập `gold_doc_ids`, và vì một bên còn giữ nhãn gold sai ở Q4. Muốn so điểm trong nhóm thì phải chốt **cùng file benchmark**, không chỉ chốt cùng 5 câu hỏi.

### Phân tích lỗi (Failure Analysis — Bài tập 3.5)

**Ca lỗi 1 — Q3: embedding mù với phép so sánh/phủ định.**
- *Câu hỏi:* "Đơn hàng ở khoảng cách **xa hơn 10km** thì bao lâu được giao tới?"
- *Kết quả:* hạng 1 (0.532) và hạng 2 (0.512) đều là chunk nói "giao nhanh 1–2 giờ… bán kính **=< 10km**" — **ngược hẳn** câu hỏi. Chunk đúng (">10km → 1–2 ngày") chỉ xếp hạng 3.
- *Vì sao:* cosine similarity so khớp bề mặt ngôn ngữ. "=<10km" và ">10km" khác nhau đúng một ký tự toán học nhưng giống nhau toàn bộ phần còn lại → vector gần như trùng (thí nghiệm cặp 4: **0.8622**). Đây **không phải** lỗi chunking — mọi chiến lược đều dính.
- *Đề xuất:* (a) hybrid search BM25 + dense hợp nhất bằng RRF để token ">" / "xa hơn" có trọng số từ vựng riêng; (b) cross-encoder rerank top-20, vì cross-encoder đọc cặp (query, chunk) cùng lúc nên phân biệt được chiều so sánh; (c) rẻ nhất: ở bước ingest, viết lại điều kiện thành text tường minh ("khoảng cách lớn hơn 10 ki-lô-mét").

**Ca lỗi 2 — Q1: câu hỏi mơ hồ + corpus nhiều nguồn cùng chủ đề.**
- *Câu hỏi:* "Điện thoại mua mới được đổi sang máy khác trong bao nhiêu ngày?" — **không nêu nhà bán lẻ nào**.
- *Kết quả:* top-1 là Di Động Việt (33 ngày), top-2 là CellphoneS giao hàng (35 ngày), top-3 mới là chunk gold (30 ngày). Tính theo Hit@3 thì "đạt", nhưng agent sẽ trộn ba con số của ba doanh nghiệp thành một câu trả lời sai.
- *Vì sao:* corpus có 3 nhà bán lẻ nói cùng một chủ đề với **số liệu khác nhau**; câu hỏi thiếu tín hiệu phân biệt nên retrieval không có cơ sở chọn.
- *Đề xuất:* (a) bắt buộc `retailer` filter cho mọi câu hỏi hỏi con số — A/B ở Q2 cho thấy khi câu hỏi có nêu thương hiệu thì retrieval tự làm được, nhưng khi **không** nêu thì filter là cách duy nhất; (b) hoặc để agent trả lời kèm phân nhóm theo `retailer` thay vì gộp; (c) sửa chính bộ benchmark: câu hỏi hỏi số mà không nêu chủ thể là câu hỏi **thiếu định danh**, không phải câu hỏi khó.

**Ca lỗi 3 — `sentences_3` trên corpus B: đúng tài liệu, sai đoạn.**
- *Triệu chứng:* Hit@3 = 1.00 nhưng Grounded@3 = **0.40** — 3/5 câu hỏi truy xuất đúng tài liệu mà không chunk nào trong top-3 chứa dữ kiện cần trả lời.
- *Bằng chứng cụ thể:*
  - Q3 hỏi "đơn hàng giá trị bao nhiêu thì không được vận chuyển?" (gold: **50.000.000 VNĐ**) → top-1 là khối mở đầu tài liệu: *"# Chính sách vận chuyển Shopee ## Phạm vi áp dụng…"*
  - Q4 hỏi hình phạt với người bán vi phạm (gold: *"đình chỉ tài khoản", "cấn trừ số dư"*) → top-1 lại là khối mở đầu, top-2 là mục "Danh mục hàng cấm/hạn chế" chứ không phải mục "Hình phạt vi phạm"
- *Vì sao:* tài liệu corpus B viết bằng **bullet list Markdown**, trong khi `SentenceChunker` chỉ tách ở `.!?`. Heading (`## Phạm vi áp dụng`) và nhiều gạch đầu dòng **không có dấu kết câu**, nên chúng dính lại thành một "câu" rất dài; gom 3 "câu" như vậy tạo ra chunk vắt ngang nhiều mục, đồng thời sinh ra các chunk mở đầu chung chung nhưng lại ăn điểm similarity cao. `policy_contextual` cắt đúng ở heading nên **không trượt grounding câu nào**.
- *Bài học:* chiến lược tách câu **phụ thuộc định dạng tài liệu** — chạy ổn trên văn xuôi (corpus A) và hỏng trên danh sách gạch đầu dòng (corpus B). Đây là lý do phải kiểm chứng chéo thay vì tin vào một corpus.
- *Đề xuất:* coi dòng bắt đầu bằng `#`, `-`, `*`, hoặc `số.` là ranh giới chunk ngang hàng với dấu kết câu — chính là điều `PolicySectionChunker` đang làm.

**Bài học rút ra khi so sánh trong nhóm:**

**a) So sánh giữa bốn thành viên: nút thắt là embedder, và nhóm chỉ biết chắc điều đó sau khi tách đúng một biến.** Trên bộ câu hỏi chung, bốn người ra 5/5, 4/5, 4/5 và 0/5 — nhưng **không thể** đọc thẳng bảng đó thành thứ hạng chiến lược, vì hai người dùng embedder thật còn hai người dùng mock. Phép đo kết luận được là của Hoàng Trọng Đại: giữ nguyên mọi thứ, chỉ đổi mock → OpenAI, Hit@1 đi từ **0/5 lên 4/5**. Trong khi đó, đổi chiến lược chunking mà giữ nguyên embedder thật chỉ chênh **1 câu** (5/5 vs 4/5), và câu chênh đó (Q4) hóa ra là ca lỗi thật mà **cả embedder thật cũng trượt**. Kết luận thực dụng: **đừng tối ưu chunking trước khi chắc chắn embedder đã đúng.**

**b) Bốn người, bốn cách chấm điểm khác nhau, bốn kết luận khác nhau về cùng một hệ thống.** Trần Tuấn Anh chấm bằng Hit@1/Hit@3 → kết luận "metadata filter là yếu tố quyết định", trong khi số của bạn ấy sinh ra từ mock nên không đỡ được kết luận đó. Nguyễn Xuân Đức chấm bằng câu trả lời của agent → suýt kết luận hệ thống chạy tốt trong khi retrieval sai toàn bộ. Phó Hiếu Anh chấm bằng Hit@3 + MRR@3 + Grounded@3 → thấy Hit@3 bão hòa ở 1.00 trong khi Grounded@3 chênh 0.40–1.00. Hoàng Trọng Đại chấm bằng **cách chạy lại code của cả bốn người trong cùng điều kiện** → phát hiện hai người mô tả chiến lược khác với thứ code thật sự chạy. Bài học lớn nhất của nhóm ở lab này: **chọn sai chỉ số thì đo bao nhiêu lần cũng ra kết luận sai**, và **cách duy nhất bắt được sai lệch giữa "chiến lược đã mô tả" và "chiến lược đã chạy" là chạy lại code của nhau.**

**c) So sánh giữa các chiến lược (trên corpus A).** Cùng 9 tài liệu và cùng 5 câu hỏi, khoảng cách giữa chiến lược tệ nhất và tốt nhất là Hit@3 0.80 → 1.00 và MRR 0.60 → 0.87 — tức là **chiến lược chia nhỏ quyết định chất lượng nhiều hơn việc "code có chạy không"**. Đáng chú ý hơn: `recursive_500` có Grounded@3 **thấp nhất** (0.80) dù là chiến lược được khuyến nghị mặc định trong hầu hết tài liệu về RAG — vì corpus này có nhiều **bảng bị làm phẳng khi crawl**, mà recursive lại cắt theo đoạn văn nên tách mức phí khỏi tên nhóm sản phẩm. Bài học: không có chiến lược "tốt nhất" phổ quát, chỉ có chiến lược khớp với **cấu trúc thật** của tài liệu.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

1. **Giữ bảng ở dạng bảng.** Thiệt hại lớn nhất xảy ra ngay ở bước crawl: bảng "loại sản phẩm × thời hạn × phí" của CellphoneS bị `HTMLParser` duỗi thành các dòng rời ("30 ngày", "20%", "15%"), mất hoàn toàn quan hệ hàng–cột. Lần sau nên parse `<table>` thành Markdown table hoặc thành câu đầy đủ ("Điện thoại: đổi mới trong 30 ngày, phí nhập lại 20%") ngay khi ingest.
2. **Thêm nguồn có vai trò `seller` thật.** Enum `customer_role` hiện chỉ dùng `buyer`/`both` vì mọi sàn nhiều người bán đều `Disallow` trang seller-center trong `robots.txt`; cần xin phép nguồn hoặc dùng tài liệu công khai của Bộ Công Thương.
3. **Thêm `region` vào schema.** Q3 cho thấy chính sách giao hàng khác nhau theo khu vực (nội thành HCM/HN vs tỉnh), mà hiện không có trường nào lọc được điều đó.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Lựa chọn tài liệu (Document Set Quality) | **10** / 10 | 17 tài liệu trên 2 corpus (9 + 8), đều là trang chính sách công khai, tôn trọng `robots.txt` (đã **loại bỏ** TGDĐ/FPT Shop/Sendo vì `Disallow`). Metadata 9 trường có schema khai báo trong `metadata_schema.json` và **được ép tự động** bằng `scripts/validate_metadata.py`; `document_version` trích từ chính nội dung trang, ghi `not-stated` khi trang không công bố thay vì bịa. |
| Thiết kế chiến lược (Strategy Design) | **15** / 15 | 4 thành viên × 4 chiến lược khác nhau, cộng 5 chiến lược đo song song trên cùng harness, cộng lần đọc chéo chạy lại code của cả 4 nhánh trong cùng điều kiện; tách bạch được **đóng góp riêng của từng cải tiến** (cấu trúc → MRR, ngữ cảnh → Hit/Grounded); kiểm chứng chéo trên corpus thứ hai; và báo cáo một **kết quả âm** (hybrid BM25+RRF qua 3 vòng lặp) kèm nguyên nhân đo được thay vì giấu đi. |
| Chất lượng truy xuất (Retrieval Quality) | **9** / 10 | Bộ câu hỏi chung: 5/5 Hit@3 với `policy_contextual`, nhưng theo `docs/SCORING.md` thì trên **bộ mở rộng corpus A** vẫn còn Q1 và Q3 chưa đạt top-1 (8/10). Lấy mức trung thực giữa hai bộ; đồng thời tự trừ vì bộ benchmark chung còn lỗi `doc_id` ở Q4 mà nhóm phát hiện muộn. |
| Thuyết trình (Demo) | **5** / 5 | 6 insight đều dựa trên số liệu đo được, trong đó 3 phân tích lỗi có bằng chứng cụ thể (chunk nguyên văn, toán tử `=<` vs `>`), và một thí nghiệm đối chứng về embedder xuất hiện tự nhiên từ chính nhóm. |
| **Tổng phần nhóm** | **39 / 40** | |
