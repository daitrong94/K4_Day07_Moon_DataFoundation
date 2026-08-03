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
> Hai vector chỉ về gần cùng một **hướng** trong không gian embedding, nghĩa là mô hình cho rằng hai đoạn văn bản nói về cùng một chủ đề / dùng cùng kiểu diễn đạt. Cosine chỉ quan tâm hướng, không quan tâm độ dài vector, nên một câu ngắn và một đoạn dài cùng chủ đề vẫn có thể đạt điểm cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả chiếc điện thoại vừa mua"
- Câu B: "Tôi cần trả lại máy đã mua tuần trước"
- Tại sao tương đồng: cùng ý định (yêu cầu trả hàng), cùng trường từ vựng (đổi trả / trả lại, điện thoại / máy). Đo thực tế: **0.6617**.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách bảo hành điện thoại"
- Câu B: "Công thức nấu phở bò gia truyền"
- Tại sao khác: không chung chủ đề, không chung từ vựng, không chung ngữ cảnh sử dụng. Đo thực tế: **0.1810**.

**Tại sao độ tương tự cosine được ưu tiên hơn khoảng cách Euclid cho text embeddings?**
> Vì độ dài vector embedding phản ánh chủ yếu **độ dài / tần suất từ** của văn bản chứ không phải nội dung. Khoảng cách Euclid sẽ coi một đoạn 500 chữ và một câu 10 chữ cùng chủ đề là "xa nhau" chỉ vì chuẩn vector khác nhau, còn cosine chuẩn hóa điều đó đi và chỉ so hướng. Ngoài ra khi vector đã được chuẩn hóa (như `MockEmbedder` và `LocalEmbedder` ở lab này đều làm), cosine tương đương tích vô hướng nên tính rất nhanh — đó là lý do `EmbeddingStore.search()` chỉ cần `_dot()`.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: bước nhảy (step) = `chunk_size - overlap` = 500 − 50 = **450**.
> `số chunk = ceil((10000 − 50) / 450) = ceil(9950 / 450) = ceil(22.11) = ` **23 chunks**.
> Kiểm chứng bằng code trong repo: `len(FixedSizeChunker(500, 50).chunk("a" * 10000))` → **23**.

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> step giảm còn 400 → `ceil((10000 − 100) / 400) = ceil(24.75) =` **25 chunks** (tăng 2 chunk, tức chi phí lưu trữ và embedding tăng ~9%). Đổi lại, mỗi ranh giới chunk được "che" bởi 100 ký tự trùng lặp, nên một câu bị cắt đôi ở chunk *n* vẫn xuất hiện trọn vẹn ở đầu chunk *n+1*. Trong corpus chính sách của nhóm tôi, điều này quan trọng vì các mệnh đề dạng "trong vòng 15 ngày đầu nhập lại máy, trừ phí 15%" mà bị cắt ngang thì cả hai nửa đều vô dụng cho việc trả lời.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+`: lookbehind giữ lại dấu câu ở cuối câu trước, phần `\s+` mới bị "ăn" làm ranh giới. Sau đó strip từng câu, loại chuỗi rỗng, rồi gom theo `max_sentences_per_chunk`. Edge case xử lý: text rỗng hoặc chỉ có khoảng trắng trả `[]`; dấu câu cuối văn bản sinh ra một mảnh rỗng ở cuối và bị lọc bỏ.
> **Hạn chế đã biết:** với tiếng Việt regex này cắt nhầm ở "TP. Hồ Chí Minh", "Điều 5.1", "500.000đ". Corpus của nhóm có "1800.2097" và "*Cập nhật từ 08/06/2022" nên lỗi này có thật, không phải giả định.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` có **ba base case**: text rỗng → `[]`; text đã vừa `chunk_size` → `[text]`; hết separator (hoặc gặp separator rỗng `""`) → cắt cứng theo ký tự. Trường hợp còn lại: tách theo separator đầu danh sách rồi **gom ngược lại** các mảnh liền kề vào một buffer cho tới sát `chunk_size` — bước gom này mới là điều làm cho recursive khác với "tách rồi thôi". Mảnh nào tự nó vẫn quá to thì đệ quy xuống separator kế tiếp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu in-memory bằng `list[dict]`, mỗi record gồm `{index, id, content, metadata, embedding}`. **Cố ý không dùng dict theo `id`**, vì test nạp hai lần cùng bộ `doc0/doc1` và kỳ vọng size = 5 chứ không phải 3 — dict sẽ ghi đè. `search` gọi `_search_records`, tính `_dot()` giữa embedding của query và từng record rồi sắp giảm dần. Dùng tích vô hướng thay vì cosine đầy đủ là hợp lệ vì cả `MockEmbedder` lẫn `LocalEmbedder` đều trả vector đã chuẩn hóa.
> **Một quyết định tôi chủ động sửa so với khung đề:** khung đề đặt `self._use_chroma = True` ngay khi `import chromadb` thành công, trong khi phần tạo collection còn là TODO — máy nào cài sẵn chromadb sẽ vỡ toàn bộ store. Tôi để `_use_chroma = False` kèm chú thích, vì ChromaDB là phần bonus.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc trước, tìm sau** (pre-filter): thu hẹp danh sách record theo metadata rồi mới tính similarity trên tập đã lọc. Làm ngược lại (tìm top-k rồi lọc) sẽ trả về ít hơn `top_k` kết quả khi tài liệu phù hợp không lọt top-k ban đầu. Nhánh `metadata_filter=None`/rỗng bỏ qua lọc hoàn toàn để `search_with_filter` khớp `search` — đúng yêu cầu của test.
> `delete_document` lọc bỏ mọi record có `metadata['doc_id']` trùng, trả `True` nếu số lượng giảm. Việc này chỉ chạy được vì `add_documents` **tự điền** `metadata.setdefault("doc_id", doc.id)` — test tạo `Document(..., {})` với metadata rỗng nên nếu không tự điền thì hàm xóa luôn trả `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Ba bước tách bạch: `store.search()` → `_build_context()` → `build_prompt()` → `llm_fn`. Ngữ cảnh được đánh số `[1] [2] [3]` kèm `doc_id` và score, và prompt yêu cầu mô hình **chỉ dùng thông tin trong ngữ cảnh, nói rõ khi không đủ dữ liệu, và trích dẫn `[n]` cho mỗi ý**. Đánh số như vậy để chấm được tiêu chí Source Traceability trong `docs/EVALUATION.md`: nhìn câu trả lời là truy ngược ra chunk nào đã cấp thông tin. Tôi tách `build_prompt` thành method riêng để thử nghiệm prompt ở Giai đoạn 2 mà không phải sửa `answer`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ .venv/bin/python -m pytest tests/ -q
..........................................                               [100%]
42 passed in 0.02s
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

Môi trường: Python **3.11.15** (đúng `.python-version`), pytest **9.1.1** + python-dotenv **1.2.2** (đúng pin trong `requirements.txt`).

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Đo bằng `compute_similarity()` với embedder `AITeamVN/Vietnamese_Embedding` (1024 chiều). Dự đoán được ghi **trước khi** chạy.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|:---:|
| 1 | Tôi muốn đổi trả chiếc điện thoại vừa mua | Tôi cần trả lại máy đã mua tuần trước | cao | **0.6617** | ✅ |
| 2 | Chính sách giao hàng của cửa hàng | Quy định vận chuyển đơn hàng tới khách | cao | **0.5531** | ⚠️ thấp hơn tôi tưởng |
| 3 | Đổi trả trong vòng 15 ngày đầu | Đổi trả trong vòng 30 ngày đầu | cao | **0.8898** | ✅ |
| 4 | Khoảng cách dưới 10km | Khoảng cách xa hơn 10km | cao (dù nghĩa NGƯỢC nhau) | **0.8622** | ✅ |
| 5 | Chính sách bảo hành điện thoại | Công thức nấu phở bò gia truyền | thấp | **0.1810** | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Bất ngờ nhất là **thứ hạng bị đảo ngược so với trực giác**: hai cặp mà tôi cố tình dựng để "khác nghĩa" — cặp 3 (khác con số) và cặp 4 (ngược chiều so sánh) — lại đạt điểm **cao hơn hẳn** hai cặp diễn đạt lại thật sự cùng ý (0.89 và 0.86 so với 0.66 và 0.55). Nói cách khác, embedding coi "15 ngày" ≈ "30 ngày" giống nhau hơn là coi "đổi trả" ≈ "trả lại".

Điều này nói rằng embedding mã hóa **hình thức bề mặt và trường chủ đề**, chứ không mã hóa giá trị số hay chiều của phép so sánh. Cặp 3 và 4 giống nhau tới ~95% ký tự nên vector gần như trùng; còn cặp 1 và 2 dùng từ vựng khác hẳn ("giao hàng" vs "vận chuyển", "đổi trả" vs "trả lại") nên bị đẩy xa dù cùng ý.

Hệ quả trực tiếp trong bài này: retrieval **không thể** dùng cosine để phân biệt điều kiện "≤10km" với ">10km" — và đó đúng là cách câu hỏi số 3 trong benchmark bị trượt (top-1 và top-2 đều trả về mệnh đề ngược chiều). Muốn sửa thì phải thêm tín hiệu từ vựng (BM25 hybrid) hoặc một reranker đọc cặp (query, chunk) cùng lúc, chứ tinh chỉnh chunking bao nhiêu cũng không giải quyết được.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Chạy bằng `HF_HOME=./.hf-cache .venv/bin/python scripts/run_benchmark.py --show-top`, chiến lược `policy_contextual` (`PolicySectionChunker` + tiền tố ngữ cảnh), top-3.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Score | Liên quan? | Câu trả lời của Agent |
|---|---|---|---:|:---:|---|
| 1 | Điện thoại mua mới được đổi sang máy khác trong bao nhiêu ngày? | Di Động Việt — "trong thời gian 33 ngày hoặc 1 đổi 1 GBHMR…" | 0.525 | ⚠️ sai nhà bán lẻ; chunk gold ở hạng 3 | Có căn cứ nhưng dễ trộn số liệu 3 thương hiệu |
| 2 | Nhập lại máy trong 15 ngày đầu tại Hoàng Hà Mobile trừ bao nhiêu %? | HHM — "trong vòng 15 ngày đầu nhập lại máy, **trừ phí 15%** trên giá hiện tại" | 0.700 | ✅ hạng 1 | Đúng, trích được nguyên văn |
| 3 | Đơn hàng ở khoảng cách xa hơn 10km thì bao lâu được giao? | CellphoneS — "giao nhanh 1–2 giờ… bán kính **=< 10km**" | 0.532 | ⚠️ ngược chiều câu hỏi; chunk đúng ở hạng 3 | Sai nếu chỉ đọc hạng 1 |
| 4 | Máy chưa khui seal, chưa kích hoạt được đổi trả miễn phí bao lâu? | Di Động Việt — "máy khui seal nhưng chưa kích hoạt tính phí 5%…" | 0.652 | ✅ đúng tài liệu; câu gold "7 ngày đầu tiên" ở hạng 3 | Đúng |
| 5 | Khách muốn hủy đơn hàng đã đặt online phải làm gì? | CellphoneS — "1.2 phương thức hủy giao dịch: gọi tổng đài **1800.2097**…" | 0.439 | ✅ hạng 1 | Đúng, đủ cả 2 số tổng đài |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5** (Hit@3 = 1.00, MRR@3 = 0.87, Grounded@3 = 1.00)

Điểm tự chấm theo `docs/SCORING.md`: Q2/Q4/Q5 được 2 điểm; Q1 và Q3 chỉ 1 điểm vì chunk liên quan **không ở top-1** → **8/10**.

### Chạy bộ câu hỏi CHUNG của nhóm trên code của tôi

`docs/SCORING.md` yêu cầu 5 câu hỏi phải trùng với các thành viên cùng nhóm. Bộ câu hỏi chung của nhóm nằm ở nhánh `2a202601086-TranTuanAnh`, file `Bench.py` → `BENCHMARK_QUERIES` (5 câu, trên corpus Shopee/Tiki `data/k4_ecommerce` của nhóm). Tôi chuyển nguyên văn sang format harness của mình (`data/benchmark_tta_queries.json` — giữ nguyên `query`, `gold_answer`, `metadata_filter`; chỉ đổi tên trường và bổ sung `gold_keywords` để đo thêm Grounded@3) rồi chạy bằng **code của tôi**:

```bash
.venv/bin/python scripts/run_benchmark.py \
  --data-dir data/team_k4_corpus --benchmark data/benchmark_tta_queries.json
```

| # | Câu hỏi của nhóm | Top-1 doc_id | Score | Hit@3 | Grounded@3 |
|---|---|---|---:|:---:|:---:|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền…? | `shopee-return-refund-policy` | 0.518 | ✅ | ✅ |
| 2 | Nhà bán Tiki bị xử lý thế nào nếu gian lận? | `tiki-seller-rights-obligations` | 0.512 | ✅ | ✅ |
| 3 | Hạn mức Apple Pay trên Shopee là bao nhiêu? | `shopee-payment-methods` | 0.569 | ✅ | ✅ |
| 4 | Hàng hóa cấm đăng bán gồm những loại nào? | `shopee-marketplace-rules` | 0.541 | ✅ | ✅ |
| 5 | Thời gian xử lý khiếu nại vận chuyển tối đa? | `shopee-shipping-policy` | 0.579 | ✅ | ✅ |

**5/5 câu có chunk liên quan trong top-3.** So sánh 5 chiến lược của tôi trên cùng bộ câu hỏi này:

| Chiến lược | Hit@3 | MRR@3 | Grounded@3 |
|---|---:|---:|---:|
| `fixed_500_50` | 1.00 | 0.90 | 0.80 |
| `sentences_3` | 1.00 | **1.00** | **0.40** |
| `recursive_500` | 1.00 | 0.87 | 0.80 |
| `policy_sections` | 1.00 | 0.87 | 0.60 |
| **`policy_contextual`** | 1.00 | 0.90 | **1.00** |

Kết quả củng cố kết luận ở báo cáo nhóm: mọi chiến lược đều tìm **đúng tài liệu** (Hit@3 = 1.00), nhưng chỉ `policy_contextual` luôn lấy **đúng đoạn chứa dữ kiện** (Grounded@3 = 1.00). `sentences_3` có MRR cao nhất (1.00 — luôn xếp tài liệu đúng lên hạng 1) nhưng Grounded thấp nhất (0.40) — một minh họa rõ rằng **MRR và Grounded đo hai thứ khác nhau**, và nếu chỉ nhìn Hit@1/Hit@3 như `Bench.py` của nhóm thì không thấy được khác biệt này.

**Một lỗi tôi phát hiện trong bộ câu hỏi chung:** Q4 khai `target_doc_id = "k4-prohibited-products"`, nhưng corpus không có `doc_id` nào như vậy — id thật là `shopee-prohibited-products-policy`. Giữ nguyên thì Q4 luôn bị chấm 0 với mọi chiến lược, kéo Hit@3 của cả nhóm từ 1.00 xuống 0.80 một cách giả tạo:

| Bộ câu hỏi | Hit@3 (`policy_contextual`) |
|---|---:|
| Giữ nguyên `k4-prohibited-products` | 0.80 |
| Sửa thành `shopee-prohibited-products-policy` | **1.00** |

Đã báo lại cho nhóm để sửa `Bench.py`. Đây cũng là lý do tôi thêm `scripts/validate_metadata.py`: nếu `doc_id` trong bộ benchmark được đối chiếu tự động với corpus thì lỗi này lộ ra ngay.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> **Từ `Bench.py` của Trần Tuấn Anh:** bạn ấy đo **Hit@1** bên cạnh Hit@3 — một chỉ số tôi đã bỏ qua. Hit@1 quan trọng thật, vì trong RAG thực tế chunk hạng 1 chiếm phần lớn ngữ cảnh đưa vào prompt; Hit@3 = 1.00 mà chunk đúng nằm hạng 3 thì agent vẫn dễ trả lời sai. Cách bạn ấy viết câu hỏi cũng dài và tự nhiên hơn của tôi (*"…thời gian xử lý khiếu nại đối với hư hỏng/mất mát hàng hóa tối đa là bao nhiêu ngày?"* thay vì câu cụt lủn), sát với cách người dùng thật gõ vào ô tìm kiếm hơn.
>
> Ngược lại, chạy bộ câu hỏi của bạn ấy bằng harness của tôi cho thấy Hit@1/Hit@3 **chưa đủ**: cả 5 chiến lược đều Hit@3 = 1.00, nhìn vào thì tưởng chiến lược nào cũng như nhau, trong khi Grounded@3 dao động từ 0.40 đến 1.00. Kết hợp cả hai — Hit@1 của bạn ấy và Grounded@3 của tôi — mới đủ để kết luận.

> Việc so sánh 5 chiến lược trên **cùng** corpus cho thấy điều mà chạy riêng một chiến lược không bao giờ thấy được: `recursive_500` — chiến lược được coi là mặc định tốt nhất trong hầu hết tài liệu về RAG — lại có Grounded@3 **thấp nhất** trên corpus này (0.80). Lý do rất cụ thể: tài liệu của nhóm có nhiều bảng bị làm phẳng khi crawl, và recursive cắt theo đoạn văn nên tách mức phí khỏi tên nhóm sản phẩm. Bài học tôi rút ra là **đừng chọn chiến lược theo danh tiếng, hãy chọn theo cấu trúc thật của tài liệu** — và muốn biết cấu trúc thật thì phải mở file crawl ra đọc, chứ không đọc mỗi số liệu tổng hợp.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
