# Lab 7 — Phó Hiếu Anh (2A202601312)

Bài làm cá nhân, đóng gói **tự chạy được**. Thư mục này chỉ thêm mới; **không sửa bất kỳ file nào có sẵn ở repo nhóm**.

## Chạy thử

```bash
cd 2A202601312_PhoHieuAnh
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest tests/ -v          # 70/70 pass (42 của lab + 28 tự viết)
.venv/bin/python scripts/validate_metadata.py data/k4_ecommerce
.venv/bin/python main.py "Hủy đơn hàng online thế nào?"
```

Mặc định dùng mock embedder nên chạy được ngay. Muốn có số liệu retrieval thật:

```bash
.venv/bin/pip install -r requirements-local.txt
cp .env.example .env   # rồi đặt EMBEDDING_PROVIDER=local
.venv/bin/python scripts/run_benchmark.py
```

Embedder dùng trong báo cáo: `AITeamVN/Vietnamese_Embedding` (1024 chiều).

## Kết quả

Corpus: 9 chính sách TMĐT công khai của CellphoneS / Di Động Việt / Hoàng Hà Mobile (88.065 ký tự), crawl bằng `scripts/fetch_public_pages.py` (tôn trọng `robots.txt`) rồi làm sạch bằng `scripts/clean_crawled.py`.

| Chiến lược chia nhỏ | Hit@3 | MRR@3 | Grounded@3 |
|---|---:|---:|---:|
| `fixed_500_50` | 0.80 | 0.60 | 1.00 |
| `sentences_3` | 0.80 | 0.67 | 1.00 |
| `recursive_500` | 0.80 | 0.60 | 0.80 |
| `policy_sections` | 0.80 | 0.80 | 0.80 |
| **`policy_contextual`** | **1.00** | **0.87** | **1.00** |
| `policy_contextual_hybrid` | 1.00 | 0.87 | 1.00 |

**Chiến lược nộp bài: `policy_contextual`.** Bản hybrid (BM25 + RRF) cho kết quả *bằng đúng* baseline nên không chọn — chi tiết vì sao ở dưới.

Chi tiết phân tích: [`report/REPORT_NHOM.md`](report/REPORT_NHOM.md) và [`report/REPORT_CANHAN.md`](report/REPORT_CANHAN.md).

## Phần tôi viết thêm

| File | Nội dung |
|---|---|
| `src/chunking.py`, `src/store.py`, `src/agent.py` | 13 TODO của Giai đoạn 1 |
| `src/custom_chunking.py` | `PolicySectionChunker` (cắt theo điều khoản) + tiền tố ngữ cảnh cho mỗi chunk |
| `scripts/clean_crawled.py` | Bóc menu/footer bằng tiền tố–hậu tố chung giữa các trang cùng host |
| `scripts/validate_metadata.py` | Ép metadata schema (enum, regex, `doc_id` trùng, `sources.csv` khớp 1-1) |
| `scripts/run_benchmark.py` | Đo Hit@3 / MRR@3 / Grounded@3, A/B lọc metadata |
| `src/hybrid.py` + `tests/test_hybrid.py` | Hybrid BM25 + RRF (stdlib), 28 unit test — xem mục cuối |
| `data/k4_ecommerce/metadata_schema.json` | Schema máy đọc được cho corpus |
| `data/k4_ecommerce/benchmark.json` | 5 câu hỏi đánh giá + gold answer |

`src/embeddings.py` chỉ sửa một chỗ: thêm cờ `LOCAL_TRUST_REMOTE_CODE` (mặc định tắt) vì vài model mạnh yêu cầu `trust_remote_code=True` — tức chạy code tải từ HF Hub, nên phải bật thủ công.

`ingest.py` thêm tham số tùy chọn `chunk_builder` (mặc định giữ nguyên hành vi cũ) để dùng được bản chunk có gắn ngữ cảnh.

## Kiểm chứng chéo trên corpus của nhóm

Chạy cùng harness trên bộ tài liệu Shopee/Tiki ở gốc repo, để kiểm tra chiến lược có tổng quát hóa không:

```bash
.venv/bin/python scripts/run_benchmark.py \
  --data-dir ../data/k4_ecommerce \
  --benchmark data/benchmark_team_corpus.json
```

`policy_contextual` là chiến lược duy nhất đạt tối đa cả ba chỉ số trên **cả hai** corpus. Phân tích đầy đủ ở mục *"Kiểm chứng chéo"* trong `report/REPORT_NHOM.md`.

Chạy tiếp với **bộ 5 câu hỏi chung của nhóm** (lấy từ `Bench.py` nhánh `2a202601086-TranTuanAnh`):

```bash
.venv/bin/python scripts/run_benchmark.py \
  --data-dir ../data/k4_ecommerce \
  --benchmark data/benchmark_tta_queries.json
```

> ⚠️ **Một lỗi trong `Bench.py` cần nhóm xác nhận:** query #4 khai `target_doc_id = "k4-prohibited-products"`, nhưng corpus không có `doc_id` nào như vậy — id thật là `shopee-prohibited-products-policy`. Giữ nguyên thì Q4 luôn bị chấm 0 với mọi chiến lược, kéo Hit@3 từ 1.00 xuống 0.80 một cách giả tạo. `data/benchmark_tta_queries.json` đã sửa và ghi rõ chỗ sửa trong trường `corrections`.

## Hybrid BM25 + RRF: một kết quả âm có ích

Nhóm nên đọc mục này khi đánh giá, vì nó là phần tốn công nhất mà lại **không cải thiện điểm số**.

| Vòng | Thiết kế | Corpus A | Corpus B |
|---|---|:---:|:---:|
| — | `policy_contextual` (baseline) | 1.00 / 0.87 / 1.00 | 1.00 / 0.90 / 1.00 |
| v1 | RRF ngang quyền dense–BM25 | **0.80 / 0.80** / 1.00 | **0.80 / 0.80** / 1.00 |
| v2 | + cổng chặn theo tần suất tài liệu | 0.80 / 0.80 / 1.00 | 0.80 / 0.80 / 1.00 |
| v3 | + cổng chỉ mở cho token chứa chữ số | **1.00 / 0.87 / 1.00** | **1.00 / 0.90 / 1.00** |

- **v1 làm tệ đi.** Câu hỏi *"…đổi **sang** máy khác…"*: âm tiết `sang` chỉ có ở 5/279 chunk nên "hiếm" theo mọi ngưỡng thống kê, BM25 đẩy nó lên cao — nhưng đó là **hư từ**. Tách âm tiết tiếng Việt khiến hư từ trông y hệt thuật ngữ chuyên ngành.
- **v3 chỉ hòa, không thắng.** Ca lỗi mà hybrid được kỳ vọng sẽ cứu (hỏi `>10km` nhưng trả về `≤10km`) nằm ngoài tầm BM25: corpus có 3 chunk chứa `10km` và **cả chunk đúng lẫn hai chunk sai đều chứa nó**. Token phân biệt là toán tử `=<` vs `>`, thứ mà cả embedding lẫn BM25 đều không mã hóa.

**Kết luận:** một kỹ thuật được benchmark quốc tế chứng minh +7,4% NDCG vẫn có thể vô ích trên corpus khác ngôn ngữ và khác dạng lỗi. Hướng còn lại là cross-encoder reranker — chưa làm.
