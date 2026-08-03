# Lab 7 — Phó Hiếu Anh (2A202601312)

Bài làm cá nhân, đóng gói **tự chạy được**. Thư mục này chỉ thêm mới; **không sửa bất kỳ file nào có sẵn ở repo nhóm**.

## Chạy thử

```bash
cd 2A202601312_PhoHieuAnh
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest tests/ -v          # 42/42 pass
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

Chi tiết phân tích: [`report/REPORT_NHOM.md`](report/REPORT_NHOM.md) và [`report/REPORT_CANHAN.md`](report/REPORT_CANHAN.md).

## Phần tôi viết thêm

| File | Nội dung |
|---|---|
| `src/chunking.py`, `src/store.py`, `src/agent.py` | 13 TODO của Giai đoạn 1 |
| `src/custom_chunking.py` | `PolicySectionChunker` (cắt theo điều khoản) + tiền tố ngữ cảnh cho mỗi chunk |
| `scripts/clean_crawled.py` | Bóc menu/footer bằng tiền tố–hậu tố chung giữa các trang cùng host |
| `scripts/validate_metadata.py` | Ép metadata schema (enum, regex, `doc_id` trùng, `sources.csv` khớp 1-1) |
| `scripts/run_benchmark.py` | Đo Hit@3 / MRR@3 / Grounded@3, A/B lọc metadata |
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
