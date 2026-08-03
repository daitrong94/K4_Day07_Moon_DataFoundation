# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

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

**Thành viên 1 — [Tên]**
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

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

Cùng corpus, cùng 5 câu hỏi, cùng embedder — chỉ khác chiến lược chia nhỏ. Đo bằng `scripts/run_benchmark.py`:

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

Kết quả trên một bộ dữ liệu chưa chứng minh được điều gì — chiến lược có thể chỉ đang khớp may mắn với đặc thù corpus. Nhóm chạy **cùng harness, cùng 5 chiến lược, cùng embedder** trên một corpus TMĐT thứ hai hoàn toàn độc lập: 8 chính sách Shopee/Tiki (~27.000 ký tự) do một thành viên khác thu thập, đặt tại `data/team_k4_corpus/`, bộ câu hỏi riêng tại `data/benchmark_team_corpus.json`.

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

**b) Chỉ còn Grounded@3 phân biệt được — và nó phơi bày `sentences_3`.** Chỉ số này rơi xuống **0.40** ở corpus B trong khi Hit@3 vẫn 1.00: chiến lược tìm **đúng tài liệu** nhưng lấy **sai đoạn**. Chi tiết ở phần Phân tích lỗi (ca lỗi 3).

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

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

Cùng 9 tài liệu và cùng 5 câu hỏi, khoảng cách giữa chiến lược tệ nhất và tốt nhất là Hit@3 0.80 → 1.00 và MRR 0.60 → 0.87 — tức là **chiến lược chia nhỏ quyết định chất lượng nhiều hơn việc "code có chạy không"**. Đáng chú ý hơn: `recursive_500` có Grounded@3 **thấp nhất** (0.80) dù là chiến lược được khuyến nghị mặc định trong hầu hết tài liệu về RAG — vì corpus này có nhiều **bảng bị làm phẳng khi crawl**, mà recursive lại cắt theo đoạn văn nên tách mức phí khỏi tên nhóm sản phẩm. Bài học: không có chiến lược "tốt nhất" phổ quát, chỉ có chiến lược khớp với **cấu trúc thật** của tài liệu.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

1. **Giữ bảng ở dạng bảng.** Thiệt hại lớn nhất xảy ra ngay ở bước crawl: bảng "loại sản phẩm × thời hạn × phí" của CellphoneS bị `HTMLParser` duỗi thành các dòng rời ("30 ngày", "20%", "15%"), mất hoàn toàn quan hệ hàng–cột. Lần sau nên parse `<table>` thành Markdown table hoặc thành câu đầy đủ ("Điện thoại: đổi mới trong 30 ngày, phí nhập lại 20%") ngay khi ingest.
2. **Thêm nguồn có vai trò `seller` thật.** Enum `customer_role` hiện chỉ dùng `buyer`/`both` vì mọi sàn nhiều người bán đều `Disallow` trang seller-center trong `robots.txt`; cần xin phép nguồn hoặc dùng tài liệu công khai của Bộ Công Thương.
3. **Thêm `region` vào schema.** Q3 cho thấy chính sách giao hàng khác nhau theo khu vực (nội thành HCM/HN vs tỉnh), mà hiện không có trường nào lọc được điều đó.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
