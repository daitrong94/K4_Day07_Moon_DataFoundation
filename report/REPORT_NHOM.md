# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm K4  
**Thành viên:** Trần Tuấn Anh, Nguyễn Xuân Đức, Hoàng Trọng Đại, Phó Hiếu Anh  
**Ngày:** 08/03/2026  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung xây dựng kho dữ liệu chính sách Thương mại điện tử toàn diện bao gồm: Chính sách đổi trả/hoàn tiền, Quy định đăng bán & xử lý vi phạm của người bán, Phương thức thanh toán, Danh mục hàng hóa bị cấm/hạn chế, Chính sách vận chuyển và Bảo mật thông tin trên Shopee và Tiki.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền Shopee | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 / 2026-03-11 | 6,197 | `customer_role: both`, `category: returns` |
| 2 | Quyền và nghĩa vụ của Nhà Bán và Tiki | https://hocvien.tiki.vn/faq/quyen-va-nghia-vu-cua-nha-ban-va-tiki/ | 2026-08-03 / not-stated | 3,331 | `customer_role: seller`, `category: seller-terms` |
| 3 | Các phương thức thanh toán trên Shopee | https://help.shopee.vn/portal/4/article/79198 | 2026-08-03 / not-stated | 2,471 | `customer_role: buyer`, `category: payment` |
| 4 | Danh mục hàng hóa cấm đăng bán | https://help.shopee.vn/portal/4/article/77244 | 2026-08-03 / 2026.1 | 3,591 | `customer_role: seller`, `category: prohibited` |
| 5 | Chính sách vận chuyển Shopee | https://help.shopee.vn/portal/4/article/77250 | 2026-08-03 / 2026.1 | 2,920 | `customer_role: both`, `category: shipping` |
| 6 | Quy chế hoạt động sàn TMĐT | https://help.shopee.vn/portal/4/article/77245 | 2026-08-03 / 2026.1 | 4,727 | `customer_role: both`, `category: rules` |
| 7 | Chính sách bảo mật Shopee | https://help.shopee.vn/portal/4/article/77248 | 2026-08-03 / 2026.1 | 2,312 | `customer_role: buyer`, `category: privacy` |
| 8 | Chính sách bảo mật Tiki | https://tiki.vn/bao-mat-thong-tin-ca-nhan | 2026-08-03 / not-stated | 2,420 | `customer_role: buyer`, `category: privacy` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | `string` | `buyer`, `seller`, `both` | Phân loại vai trò người dùng (người mua / người bán), hỗ trợ pre-filtering chính xác theo nhóm đối tượng. |
| `category` | `string` | `returns`, `payment`, `seller-terms` | Phân vùng chủ đề chức năng chính sách, tránh nhiễu thông tin giữa các mảng chính sách khác nhau. |
| `source_url` | `string` | `https://help.shopee.vn/...` | Truy vết nguồn gốc chính thống và kiểm tra tính xác thực của câu trả lời. |
| `retrieved_at` | `string` | `2026-08-03` | Theo dõi ngày thu thập tài liệu để kiểm soát tính cập nhật. |
| `document_version`| `string` | `2026.1` | Quản lý các phiên bản cập nhật chính sách của sàn. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên các tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `returns-policy.md` | FixedSizeChunker (`fixed_size`) | 31 | 199.5 | Tương đối, có thể cắt đứt giữa câu. |
| `returns-policy.md` | SentenceChunker (`by_sentences`) | 12 | 480.2 | Tốt, giữ nguyên vẹn câu. |
| `returns-policy.md` | RecursiveChunker (`recursive`) | 28 | 195.4 | Cực kỳ tốt, giữ trọn vẹn ngữ cảnh đoạn và câu. |

### Chiến lược của từng thành viên

**Thành viên 1 — Trần Tuấn Anh**
- **Loại chiến lược:** `RecursiveChunker` + `Metadata Filtering`
- **Mô tả & lý do chọn cho chủ đề này:** Ưu tiên giữ cấu trúc tiêu đề (`\n\n`, `\n`) và đoạn văn bản hoàn chỉnh của các điều khoản chính sách. Kết hợp với bộ lọc metadata `customer_role` giúp loại bỏ toàn bộ các tài liệu dành cho đối tượng không liên quan trước khi tính độ tương đồng vector.
- **Code snippet (Bench.py integration):**
```python
# Gọi tìm kiếm kết hợp pre-filtering metadata theo customer_role
if meta_filter:
    results = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter)
else:
    results = store.search(query, top_k=3)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trần Tuấn Anh | RecursiveChunker + Metadata Filter | 9/10 | Giữ tính toàn vẹn của điều khoản, lọc bớt nhiễu theo vai trò người dùng (`buyer`/`seller`). | Cần thiết lập schema metadata chuẩn từ đầu. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược `RecursiveChunker` kết hợp tiền lọc metadata (`search_with_filter`) là tối ưu nhất cho văn bản chính sách TMĐT. Việc dùng `RecursiveChunker` giúp tôn trọng các ranh giới xuống dòng và tiêu đề mục trong tài liệu, trong khi lọc theo `customer_role` giúp phân tách hoàn toàn quy định cho người mua và người bán, làm tăng vượt trội độ chính xác truy xuất Top-1.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền đối với đơn hàng giao thành công thông thường là bao nhiêu ngày? | 15 ngày kể từ khi đơn hàng được giao thành công (riêng thực phẩm tươi sống/đông lạnh là 24 giờ). | `shopee-return-refund-policy::chunk_...` |
| 2 | Nhà bán trên Tiki bị xử lý như thế nào nếu thực hiện các hành vi gian lận như tự đặt đơn hoặc lôi kéo khách giao dịch ngoài sàn? | Nhà Bán bị ngưng hợp tác kinh doanh vĩnh viễn, thu hồi giá trị khuyến mãi lạm dụng, hủy đơn/nhận xét gian lận, và phong tỏa sao kê trong 90 ngày. | `tiki-seller-rights-obligations::chunk_...` |
| 3 | Shopee hỗ trợ những phương thức thanh toán chính nào và hạn mức điều kiện đối với Apple Pay là bao nhiêu? | Shopee hỗ trợ 9 hình thức thanh toán chính. Đối với Apple Pay, hạn mức giao dịch quy định từ 10.000 VNĐ đến 25.000.000 VNĐ. | `shopee-payment-methods::chunk_...` |
| 4 | Các loại hàng hóa cấm đăng bán hoặc kinh doanh trên sàn giao dịch thương mại điện tử bao gồm những loại nào? | Bao gồm vũ khí, chất cháy nổ, hàng giả/hàng nhái, ma túy/chất kích thích, động vật hoang dã, thuốc lá/thuốc lá điện tử, và hàng hóa bị cấm theo quy định pháp luật. | `k4-prohibited-products::chunk_...` |
| 5 | Chính sách vận chuyển Shopee quy định thời gian xử lý khiếu nại đối với hư hỏng/mất mát hàng hóa tối đa là bao nhiêu ngày? | Thời gian xử lý khiếu nại tối đa là 10 ngày làm việc kể từ khi nhận đủ thông tin và bằng chứng hợp lệ. | `shopee-shipping-policy::chunk_...` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền... | RecursiveChunker | Có (Hit@3 = YES) | Truy xuất trúng chunk quy định thời hạn 15 ngày trong Top-3. |
| 2 | Nhà bán trên Tiki bị xử lý như thế nào... | RecursiveChunker + Metadata Filter (`seller`) | Có (Hit@1 = PASSED) | Nhờ lọc `customer_role: seller`, Top-1 chính xác tuyệt đối. |
| 3 | Shopee hỗ trợ phương thức thanh toán nào... | RecursiveChunker + Metadata Filter (`buyer`) | Có (Hit@1 = PASSED) | Nhờ lọc `customer_role: buyer`, Top-1 trả về đúng bảng thanh toán. |
| 4 | Các loại hàng hóa cấm đăng bán... | RecursiveChunker | Có | Chunk chứa danh mục hàng cấm nằm trong bộ kết quả. |
| 5 | Thời gian xử lý khiếu nại vận chuyển... | RecursiveChunker | Có (Hit@3 = YES) | Truy xuất thành công điều khoản 10 ngày làm việc. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata giúp ích cực kỳ rõ rệt ở Câu 2 (`customer_role: seller`) và Câu 3 (`customer_role: buyer`). Nhờ việc tiền lọc metadata, kho lưu trữ đã khoanh vùng chính xác tập tài liệu liên quan trước khi tính điểm vector, giúp nâng tỷ lệ chính xác Top-1 đạt **100% (2/2 câu áp dụng filter)**.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. Phân tách ngữ cảnh chính xác bằng `RecursiveChunker` hiệu quả hơn rõ rệt so với cắt cứng `FixedSizeChunker` đối với văn bản pháp lý / chính sách.
2. Metadata Filtering (`customer_role`, `category`) giúp giải quyết bài toán nhiễu dữ liệu khi kho thông tin mở rộng.
3. Sự khác biệt giữa `MockEmbedder` (dùng để unit test) và mô hình nhúng ngữ nghĩa thật (`LocalEmbedder` / `OpenAIEmbedder`).

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu, nhưng nếu chỉ tìm kiếm bằng Semantic Search thuần túy không có Metadata Filtering thì các câu hỏi dành riêng cho đối tượng Người bán (Seller) rất dễ bị lẫn sang quy định của Người mua (Buyer). Việc chuẩn hóa schema metadata ngay từ khâu Ingest dữ liệu quyết định 50% sự thành công của hệ thống RAG.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung thêm trường metadata `section_title` (tiêu đề mục) cho từng chunk trong quá trình chunking đệ quy để có thể lọc hoặc tăng trọng số tìm kiếm theo tiêu đề bài viết.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |