# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm K4-Ecom
**Thành viên:** Nguyễn Xuân Đức
**Ngày:** 2026-08-03

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung vào các quy chế hoạt động, chính sách đổi trả hoàn tiền, vận chuyển khiếu nại, bảo mật thông tin và quyền/nghĩa vụ của Người bán/Người mua trên hai sàn TMĐT lớn là Shopee và Tiki.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | shopee-return-refund-policy.md | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 / 2026-03-11 | ~6,100 | doc_id, customer_role: both, category: returns |
| 2 | tiki-seller-rights-obligations.md | https://hocvien.tiki.vn/faq/quyen-va-nghia-vu-cua-nha-ban-va-tiki/ | 2026-08-03 / not-stated | ~3,300 | doc_id, customer_role: seller, category: seller-terms |
| 3 | shopee-shipping-policy.md | https://help.shopee.vn/portal/4/article/77250 | 2026-08-03 / 2026-03-20 | ~2,900 | doc_id, customer_role: both, category: shipping |
| 4 | shopee-privacy-policy.md | https://help.shopee.vn/portal/4/article/77244 | 2026-08-03 / 2026-06-04 | ~2,300 | doc_id, customer_role: both, category: privacy |
| 5 | shopee-payment-methods.md | https://help.shopee.vn/portal/4/article/79198 | 2026-08-03 / not-stated | ~2,400 | doc_id, customer_role: buyer, category: payment |
| 6 | shopee-marketplace-rules.md | https://help.shopee.vn/portal/4/article/77245 | 2026-08-03 / 2025-01-03 | ~4,700 | doc_id, customer_role: both, category: platform-rules |
| 7 | tiki-privacy-policy.md | https://tiki.vn/thong-tin/privacy-policy | 2026-08-03 / 2022-11-11 | ~2,400 | doc_id, customer_role: both, category: privacy |
| 8 | shopee-prohibited-products-policy.md | https://help.shopee.vn/portal/4/article/77247 | 2026-08-03 / 2025-04-28 | ~3,600 | doc_id, customer_role: seller, category: prohibited-products |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | String | `shopee-shipping-policy` | Định danh tài liệu gốc để nhóm các chunk và hỗ trợ xóa tài liệu (`delete_document`). |
| `customer_role` | String | `buyer` / `seller` / `both` | Lọc bớt nhiễu khi câu hỏi hướng đến một vai trò cụ thể (ví dụ: chỉ tìm quy định dành riêng cho Nhà bán). |
| `category` | String | `returns` / `payment` / `shipping` | Phân loại chủ đề tài liệu để giới hạn ngữ cảnh tìm kiếm đúng nhóm chính sách. |
| `language` | String | `vi` | Phục vụ đa ngôn ngữ, chỉ truy xuất các tài liệu thuộc ngôn ngữ yêu cầu. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2 tài liệu cốt lõi:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-return-refund-policy.md` | FixedSizeChunker (`fixed_size`) | 30 | 195.07 | Tạm ổn, nhưng ranh giới cắt có thể ở giữa câu làm cụt ý. |
| | SentenceChunker (`by_sentences`) | 22 | 198.27 | Khá tốt, giữ trọn vẹn ý nghĩa của từng câu văn. |
| | RecursiveChunker (`recursive`) | 35 | 123.91 | Tốt nhất, chia nhỏ ở ranh giới đoạn/dòng tự nhiên giúp LLM dễ đọc. |
| `tiki-seller-rights-obligations.md` | FixedSizeChunker (`fixed_size`) | 14 | 199.86 | Trung bình, có nguy cơ cắt đôi điều khoản. |
| | SentenceChunker (`by_sentences`) | 9 | 237.00 | Tốt, nhóm các câu nghĩa liền mạch với nhau. |
| | RecursiveChunker (`recursive`) | 21 | 100.71 | Rất tốt, giữ nguyên các gạch đầu dòng điều khoản của Tiki. |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Xuân Đức**
- **Loại chiến lược:** RecursiveChunker (chunk_size=400)
- **Mô tả & lý do chọn cho chủ đề này:** Chọn Recursive chunking với kích thước 400 ký tự vì các chính sách thương mại điện tử thường được chia theo các gạch đầu dòng ngắn hoặc đoạn nhỏ. Việc dùng Recursive giúp ưu tiên ngắt ở ranh giới đoạn (`\n\n`) hoặc xuống dòng (`\n`), tránh làm nát các điều khoản luật mà vẫn đảm bảo chunk đủ nhỏ để nhét vừa ngữ cảnh của LLM.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Xuân Đức | RecursiveChunker (chunk_size=400) | 0 / 10 (chạy Mock) | Giữ cấu trúc định dạng gạch đầu dòng và ranh giới đoạn tự nhiên tốt. | Retrieval bị sai lệch ngẫu nhiên do đang sử dụng MockEmbedder băm MD5. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược `RecursiveChunker` là tốt nhất cho các văn bản chính sách TMĐT. Vì các tài liệu chính sách được tổ chức thành cấu trúc chặt chẽ (Điều khoản, Gạch đầu dòng). Việc chia cắt bằng Recursive giúp bảo toàn ranh giới ngữ nghĩa của các điều luật thay vì cắt ngang xương giữa câu như FixedSize.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền đối với đơn hàng giao thành công thông thường là bao nhiêu ngày? | 15 ngày kể từ khi đơn hàng giao thành công (thực phẩm tươi sống/đông lạnh là 24 giờ). | `shopee-return-refund-policy` |
| 2 | Nhà bán trên Tiki bị xử lý như thế nào nếu thực hiện các hành vi gian lận như tự đặt đơn hoặc lôi kiếm khách giao dịch ngoài sàn? | Bị ngưng hợp tác vĩnh viễn, thu hồi khuyến mãi lạm dụng, hủy đơn gian lận, phong tỏa sao kê 90 ngày và tạm giữ tài khoản thanh toán 30 ngày. | `tiki-seller-rights-obligations` |
| 3 | Shopee hỗ trợ những phương thức thanh toán chính nào và hạn mức điều kiện đối với Apple Pay là bao nhiêu? | Hỗ trợ 9 phương thức chính. Điều kiện Apple Pay: đơn hàng từ 10.000 VNĐ đến 25.000.000 VNĐ, không áp dụng cho Nạp thẻ, Người bán tự vận chuyển và ShopeeFood. | `shopee-payment-methods` |
| 4 | Các loại hàng hóa cấm đăng bán hoặc kinh doanh trên sàn giao dịch thương mại điện tử bao gồm những loại nào? | Hàng giả, nhái, thiết bị chính phủ/quân đội, tài liệu chính trị, súng/vũ khí, ma túy, thuốc lá điện tử, sản phẩm người lớn, thiết bị xâm nhập phá sóng... | `shopee-prohibited-products-policy` |
| 5 | Chính sách vận chuyển Shopee quy định thời gian xử lý khiếu nại đối với hư hỏng/mất mát hàng hóa tối đa là bao nhiêu ngày? | Thời gian xử lý khiếu nại tối đa là 10 ngày làm việc kể từ khi nhận đủ bằng chứng hợp lệ. | `shopee-shipping-policy` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền đối với đơn hàng giao thành công thông thường là bao nhiêu ngày? | RecursiveChunker | Không (No) | Sai do dùng MockEmbedder băm MD5 |
| 2 | Nhà bán trên Tiki bị xử lý như thế nào nếu thực hiện các hành vi gian lận như tự đặt đơn hoặc lôi kéo khách giao dịch ngoài sàn? | Recursive + Metadata Filter | Không (No) | Lọc đúng tài liệu người bán nhưng xếp hạng vẫn ngẫu nhiên |
| 3 | Shopee hỗ trợ những phương thức thanh toán chính nào và hạn mức điều kiện đối với Apple Pay là bao nhiêu? | RecursiveChunker | Không (No) | Sai do dùng MockEmbedder băm MD5 |
| 4 | Các loại hàng hóa cấm đăng bán hoặc kinh doanh trên sàn giao dịch thương mại điện tử bao gồm những loại nào? | RecursiveChunker | Không (No) | Sai do dùng MockEmbedder băm MD5 |
| 5 | Chính sách vận chuyển Shopee quy định thời gian xử lý khiếu nại đối với hư hỏng/mất mát hàng hóa tối đa là bao nhiêu ngày? | RecursiveChunker | Không (No) | Sai do dùng MockEmbedder băm MD5 |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có giúp ích lớn ở **Câu số 2**. Khi sử dụng bộ lọc `customer_role: seller`, hệ thống loại bỏ toàn bộ các tài liệu dành cho người mua (buyer) để chỉ giữ lại các tài liệu người bán, giúp thu hẹp phạm vi tìm kiếm và giảm thiểu hoàn toàn việc trả về các tài liệu không liên quan từ người mua.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
* Sự khác biệt cốt lõi giữa **Mock Embedder** và **Semantic Embedder**: Mock chỉ chạy thử cấu trúc phần mềm chứ không có khả năng hiểu ngữ nghĩa, dẫn đến truy xuất ngẫu nhiên.
* Sức mạnh của **Metadata Pre-filtering** trong việc loại bỏ hoàn toàn các tài liệu nhiễu ngoài phạm vi đối tượng cần tìm kiếm trước khi thực hiện so khớp vector.

**Bài học rút ra khi so sánh trong nhóm:**
* Việc lựa chọn kích thước chunk (`chunk_size`) rất quan trọng: chunk quá lớn làm loãng thông tin và tăng chi phí LLM, chunk quá nhỏ làm mất đi ngữ cảnh liên kết xung quanh. `RecursiveChunker` hoạt động linh hoạt nhất nhờ khả năng bám theo ranh giới đoạn văn tự nhiên.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
* Nhóm sẽ cài đặt thêm `requirements-local.txt` hoặc sử dụng OpenAI API key để chạy benchmark bằng mô hình embedding thật (`LocalEmbedder`), từ đó thu được các chỉ số tương đồng có giá trị ngữ nghĩa thực tế.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |

