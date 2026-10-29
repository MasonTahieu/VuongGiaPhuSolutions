# Tóm tắt dự án – Thiết kế lại website Vương Gia Phú

*Cập nhật: 28/10/2026*

## 1. Mục tiêu

- **Thiết kế lại giao diện** website http://vuonggiaphu.com (Vuong Gia Phu Solutions Company Limited).
  - **Giữ nguyên:** toàn bộ nội dung, đường dẫn (URL) và SEO.
  - **Thay mới:** giao diện, bố cục và màu sắc.
- **Hai việc website phải làm được:**
  1. Khách tin tưởng: thấy một công ty thật, ở địa phương, đã đăng ký, hiểu rõ các hãng thiết bị.
  2. Khách liên hệ: ưu tiên gọi điện hoặc nhắn Zalo 0963.345.099, sau đó là email và fanpage Facebook.
- **Khách chính:** hộ gia đình và chủ công trình ở Đồng Xoài, Đồng Nai.
  - Mảng chính: nội thất và thiết bị.
  - Mảng phụ: công nghệ, phần mềm, AI cho doanh nghiệp.
- **Website không bán hàng online:** không giỏ hàng, không đặt hàng, không công bố giá.

## 2. Cấu trúc thư mục

| Thư mục / file | Vai trò |
|---|---|
| `site-goc/` | Bản gốc của website cũ (nguồn nội dung chuẩn, không sửa) |
| `site-moi/` | Website mới (20 trang + trang 404) – đây là bản sẽ đưa lên |
| `tools/build_pages.py` | Tạo 19 trang con từ nội dung bản gốc + khung trang chủ mới |
| `tools/check_pages.py` | Đối chiếu nội dung trang mới với bản gốc (phải chạy ra "OK") |
| `tools/audit.py` | Kiểm tra SEO, liên kết, dung lượng trang |
| `tools/serve.py` | Chạy web trên máy: `python tools/serve.py 8090` |
| `tools/subset_fonts.py` | Cắt gọn và tạo lại các file phông chữ |
| `PRODUCT.md` | Mô tả sản phẩm, khách hàng, định vị (dùng cho công cụ thiết kế) |
| `xem-thu-mau-nen/` | Ảnh so sánh các phương án màu (chỉ để tham khảo, có thể xoá) |

Mỗi lần sửa khung trang chủ (`site-moi/index.html`) hoặc CSS, chạy lại `build_pages.py` rồi `check_pages.py`.

## 3. Quyết định đã chốt

**Nội dung và cấu trúc**
- Nội dung, URL và SEO giữ nguyên như bản gốc. Văn bản chính sách bảo mật đang giữ nguyên văn (xem mục 5: đề xuất cập nhật).
- Bỏ dòng chú thích "Hình ảnh sản phẩm từ website chính thức của các hãng" ở mọi trang.
- Bỏ các nhãn chữ nhỏ đặt trên tiêu đề và các số trang trí; giữ số 01–05 của quy trình.
- Link Facebook https://www.facebook.com/NoiThatVuongGiaPhu có trong khối liên hệ và chân trang.
- Không thêm tính năng đặt hàng, bảng giá hay form thu thập thông tin.

**Thanh menu**
- Không có số điện thoại trên thanh menu.
- Bấm logo để về trang chủ; không có mục "Trang chủ".
- Thứ tự mục: Nội thất · Công nghệ · Thiết bị & Thương hiệu · Chính sách bảo mật · Liên hệ.

**Chữ và màu**
- **Phông chữ** (tự lưu trên site, không dùng Google Fonts):
  - Tiêu đề lớn: Plus Jakarta Sans.
  - Chữ thường: Be Vietnam Pro.
  - Tiêu đề mục: Playfair Display.
- **Chữ nhấn trong tiêu đề:** đứng, cùng phông với tiêu đề, không nghiêng, màu chuyển sắc nhẹ.
- **Nền:** "Đá greige", gồm nền trang `#f4f3f0`, dải nền các mục `#eae8e3`, viền `#dcd9d2`.
- **Màu nhấn:** đang **thử đỏ đô** (`#a33340` → `#7a1f2b`). Phương án đã chốt trước đó là xanh petrol (`#2a7a80` → `#17565d`). Chưa quyết định cuối cùng (xem mục 5).
- **Những phần đã chuyển sang đen hoặc trắng theo yêu cầu:**
  - Khối liên hệ cuối trang: trắng.
  - Thẻ dịch vụ khi bấm hoặc rê chuột: đen.
  - Số và chấm của quy trình 5 bước: đen.
  - Bảng "Dịch vụ & sản phẩm" ở đầu trang con: trắng.
  - Ô biểu tượng các mục trên trang Thiết bị & Thương hiệu: đen.
- **Logo:** giữ nguyên màu đồng đỏ.

**Bố cục**
- Trang Thiết bị dùng bố cục đầu trang chia đôi (chữ bên trái, ảnh ghép bên phải).
- Tiêu đề lớn ở trang con tối đa 50px, nằm gọn 2 dòng trên máy tính. Trang chủ giữ cỡ lớn.
- Logo các hãng đứng yên:
  - Máy tính: xếp lưới 8 + 7 hoặc 5 × 3.
  - Điện thoại: một hàng vuốt ngang.

**Kỹ thuật**
- Ảnh sản phẩm và ảnh công trình có bản nhỏ cho điện thoại; trình duyệt tự chọn bản phù hợp.
- Ảnh công trình bấm vào để xem lớn và phóng to.
- Các cảnh báo "nền kem" và "chữ chuyển sắc" của công cụ dò lỗi thiết kế được ghi nhận là lựa chọn cố ý.

## 4. Tiến độ (đã xong)

- [x] **Trang:** dựng lại toàn bộ 20 trang theo thiết kế mới (trang chủ, Công nghệ, Nội thất, Thiết bị & Thương hiệu, Chính sách bảo mật, 15 trang thương hiệu) và trang 404.
- [x] **Điện thoại:** chỉnh bố cục riêng cho màn hình điện thoại, và sửa lỗi trang trắng trên iPhone.
- [x] **Song ngữ:** chuyển đổi tiếng Việt / tiếng Anh hoạt động trên mọi trang.
- [x] **Các đợt rà soát thiết kế:**
  - audit, harden (tiếp cận bàn phím, nút VI/EN, độ tương phản), typeset (chữ tối thiểu 12px);
  - quieter (bỏ trang trí thừa), optimize (phông tự lưu, ảnh nhẹ hơn khoảng 40%), polish (chữ không lẻ dòng, độ dài dòng dễ đọc).
- [x] **Khối ảnh "Không gian đã hoàn thiện"** trên trang Nội thất: 9 ảnh (bếp, phòng ngủ, phòng khách, phòng tắm), đã chỉnh màu, làm nét, có trình xem ảnh phóng to.
- [x] **Thanh menu** mới theo yêu cầu.
- [x] **Màu:** đổi nền sang "Đá greige"; thử màu nhấn xanh petrol rồi đỏ đô.
- [x] **Pháp lý:**
  - Đối chiếu chính sách bảo mật với luật hiện hành.
  - Kiểm tra nghĩa vụ đăng ký website và tên miền.
  - Xác nhận tên miền vuonggiaphu.com **đã được khai báo** với VNNIC (do PA Việt Nam báo cáo).
- [x] **Xem thử từ xa:** chạy web tạm qua ngrok.

**Kết luận pháp lý:**
- Với tính năng hiện tại (không đặt hàng, không bảng giá), website **không cần giấy phép** và **không cần thông báo với Bộ Công Thương**.
- Tên miền .com đã khai báo xong.

## 5. Việc còn dở

**Cần làm trước khi đưa web mới lên chính thức**
1. **Bật HTTPS** cho vuonggiaphu.com (GitHub Pages → "Enforce HTTPS"). Hiện web chỉ chạy HTTP, trong khi chính sách bảo mật đang ghi có HTTPS.
2. **Cập nhật chính sách bảo mật** (cần bạn duyệt bản đối chiếu cũ / mới):
   - Thay Nghị định 13/2023 bằng **Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15** và **Nghị định 356/2025/NĐ-CP**.
   - Sửa Mục 6: bỏ "Google Fonts" và "Firebase Hosting" (không còn dùng).
   - Sửa Mục 4: câu "chủ động liên hệ được hiểu là đồng ý" (luật mới không chấp nhận đồng ý ngầm).
   - Ghi rõ thời hạn: phản hồi yêu cầu (2 ngày xác nhận; 10 / 15 / 20 ngày xử lý tuỳ loại) và báo cơ quan khi có sự cố trong 72 giờ.
3. **Chốt màu nhấn:** giữ đỏ đô hay quay lại xanh petrol. Các chỗ còn màu nhấn:
   - nút chính,
   - ô icon khối "Giải pháp Công nghệ",
   - dải kêu gọi liên hệ cuối trang,
   - nút gọi nổi,
   - icon chân trang,
   - icon các thẻ dịch vụ lúc chưa bấm.
4. **Quyết định các khối tối** (giữ đen ngả nâu `#1c1814` hay đổi sang đen than trung tính).
5. **Đưa `site-moi/` lên hosting thật**, thay cho bản đang chạy. Chưa có kho mã (repository) GitHub cho bản mới.
6. **Thử trên iPhone thật** các thay đổi gần đây (màu, khối ảnh, trình xem ảnh, thanh menu).

**Nên làm (không bắt buộc)**
- **Ảnh công trình** nên chụp lại hoặc chỉnh bằng Photoshop:
  - bếp chữ L còn dây đèn LED trên mặt bàn,
  - phòng tắm còn nhãn ATTAX,
  - dưới lavabo còn bao bì nilon.
- **Kiểm tra ngành nghề đăng ký kinh doanh** (mã số 3801317389) đã đủ các mảng trên web chưa: phần mềm, thiết kế thi công nội thất, điện mặt trời, bán thiết bị.
- **Chuẩn bị chứng từ** chứng minh "thiết bị chính hãng" (hợp đồng, hoá đơn với hãng hoặc nhà phân phối). Xin phép dùng ảnh, logo của các hãng nếu chưa là đại lý chính thức.
- **Tên miền:**
  - Cân nhắc chuyển chủ thể tên miền từ cá nhân (Tạ Văn Vương) sang công ty, qua PA Việt Nam.
  - Bật tự gia hạn; tên miền hết hạn **15/04/2027**.
- **SEO:** rút gọn 7 tiêu đề / mô tả hơi dài (trang chủ, Nội thất, Thiết bị, Aqara, Sơn Hà, Tân Á Đại Thành, Viglacera). Đây là nội dung gốc nên cần bạn đồng ý trước khi sửa.
- **Đặt lại (reset) authtoken ngrok**, vì token đã được chia sẻ trong cuộc trò chuyện.
- **Tài liệu thiết kế:** tạo file `DESIGN.md` ghi lại hệ thống thiết kế (màu, chữ, khoảng cách) để người sau dễ tiếp tục.
- **Dọn thư mục `xem-thu-mau-nen/`** khi không cần ảnh so sánh nữa.

## 6. Cách xem web

- **Trên máy:** chạy `python tools/serve.py 8090`, mở http://localhost:8090.
- **Từ xa (tạm thời):** qua ngrok, link https://barmaid-anaconda-blinked.ngrok-free.dev. Link chỉ chạy khi máy tính, server trên máy và ngrok đang bật.
- **Nếu trình duyệt còn hiện bản cũ:** nhấn Ctrl+F5.
