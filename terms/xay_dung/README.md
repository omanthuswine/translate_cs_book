# terms/xay_dung/ — làm bảng thuật ngữ v5 từ dữ liệu (chủ sở hữu: A)

Mục tiêu: mở rộng bảng thuật ngữ ra toàn bộ khoa học máy tính và quyết định mỗi từ **dịch hay giữ tiếng Anh dựa trên
cách người Việt thật sự viết**, không cần duyệt tay từng mục. Kết quả: `terms/thuat_ngu_khmt_v5.xlsx` (đầy đủ, kèm căn
cứ từng mục) và `terms/glossary_cs_vi_v5.csv` (cho chương trình). Bảng đang dùng `terms/glossary_cs_vi.csv` (v4) chưa
bị thay; muốn thử v5 thì đặt biến môi trường `DICH_SACH_GLOSSARY=terms/glossary_cs_vi_v5.csv`.

## Nguyên tắc (nhóm chốt 21/11/2026)

1. **Nguồn uy tín, đối chiếu nhiều nguồn.** Một cách dịch chỉ được dùng khi có ít nhất 2 nguồn độc lập cùng dùng,
   trong đó ít nhất 1 nguồn hạng 1, và có bằng chứng ghép đôi (bảng ghi vậy, tác giả tự chú thích trong ngoặc, hoặc dùng
   cùng bài với chữ tiếng Anh).
2. **Theo tỷ lệ người Việt viết tiếng Anh** trong văn bản kỹ thuật tiếng Việt: dưới 20% → dịch; từ 80% → giữ tiếng Anh;
   lưng chừng → **Anh (Việt)**. Áp dụng cả cho mục cũ của v4 ("ngăn xếp (stack)" → "stack (ngăn xếp)").
3. **Từ thường hay từ chuyên ngành tùy ngữ cảnh**: từ tiếng Anh đa nghĩa (attention, loss, kernel, stack) có
   `tu_dong = ngữ cảnh`, chỉ chèn khi đoạn văn đang nói về mảng đó (xem `terms/core.py`).
4. Đổi quyết định của v4 chỉ khi độ tin cậy cao (nhiều dữ liệu, xa ngưỡng, ít nhất 2 nguồn cùng kết luận).
5. Khi số liệu chưa đủ hoặc nguồn dịch sai, **người duyệt** (Claude) tự đánh giá: `nhan_xet_claude.csv`, mỗi dòng có lý do.
6. **Luật an toàn**: mục mới do máy tự quyết (không có trong v4, người duyệt chưa xem) được ghi vào bảng nhưng
   `tu_dong = không`, tức là chưa chèn tự động. Duyệt mẫu thấy khoảng 20% mục loại này có vấn đề
   (vd deviation → "độ lệch chuẩn"). Chỉ mục v4 và mục người duyệt đã xem mới được chèn.

## Nguồn

| Hạng | Nguồn | Dùng để | Giấy phép |
| --- | --- | --- | --- |
| 1 | Bảng v4 của nhóm | cách dịch | — |
| 1 | D2L tiếng Việt **bản người dịch** (nhánh `v0.15` của `d2l-ai/d2l-vi`; nhánh `main`/`release` là dịch máy, không dùng): bảng thuật ngữ 459 mục + 4.438 cặp đoạn song ngữ | cách dịch, gióng hàng | xem repo |
| 1 | Machine Learning cơ bản (Vũ Hữu Tiệp): sách LaTeX, blog, chỉ mục song ngữ 299 cặp | cách dịch, cách viết | xem repo |
| 1 | VNOI Wiki | cách viết (thuật toán) | xem repo |
| 1 | Bảng thuật ngữ Việt hóa của Microsoft (Microsoft Terminology Collection, 15.147 danh từ) | cách dịch (mảng hệ thống) | Ms-PL |
| 2 | Wikipedia tiếng Việt (4.310 bài kỹ thuật), tên bài tiếng Việt tương ứng | cách viết, đối chiếu | CC BY-SA |
| 3 | FineWeb-2 tiếng Việt (40.997 bài kỹ thuật trên 17.290 trang web) | cách viết hằng ngày | ODC-By |
| — | FineWeb-2 bài không kỹ thuật (104.256 bài) | đo "mức đời thường" của từ | ODC-By |
| — | 7 sách KHMT tiếng Anh mở (D2L, Open Data Structures, OSTEP, Computer Networks: A Systems Approach, Crafting Interpreters, Database Design, CyBOK) | tìm thuật ngữ, đo độ phổ biến | xem từng sách |

Dữ liệu tải về nằm trong `cache/thuat_ngu/` (không đưa vào Git, không đóng gói vào app).

## Các bước (chạy từ gốc repo, theo thứ tự)

```bash
python -m terms.xay_dung.tai_kho_vi --nguon d2l vnoi mlcb wiki fineweb chung   # văn bản tiếng Việt
python -m terms.xay_dung.kho_en                                                 # văn bản tiếng Anh của 7 sách
python -m terms.xay_dung.ung_vien_en        # thuật ngữ ứng viên: v4, bảng D2L, chỉ mục ML cơ bản, Wikipedia
python -m terms.xay_dung.tim_thuat_ngu_en   # tìm thêm thuật ngữ trong sách, kiểm tra bằng Wikipedia
python -m terms.xay_dung.song_ngu_d2l       # gióng hàng trên D2L song ngữ (~8 phút)
python -m terms.xay_dung.dem_cach_dung      # đếm cách viết; chạy 2 lần (lần 2 đếm cả cách dịch trích từ ngoặc)
python -m terms.xay_dung.dem_cach_dung
python -m terms.xay_dung.phan_loai          # xếp nhóm theo số liệu
python -m terms.xay_dung.xay_bang_v5        # áp nhận xét người duyệt, xuất v5
python -m terms.xay_dung.bot_ma_thua        # đo từ mô hình tự dịch đúng, rồi chạy lại xay_bang_v5
python -m terms.xay_dung.xay_bang_v5
```

Nguồn sách và kho phải tải trước vào `cache/thuat_ngu/nguon/` và `cache/thuat_ngu/nguon_en/` (lệnh `git clone`/`curl`
ghi trong docstring từng script).

## Kỹ thuật dùng (và lỗi mỗi kỹ thuật sửa)

| Kỹ thuật | Sửa lỗi gì |
| --- | --- |
| Lọc bài kỹ thuật bằng từ khóa cả Anh lẫn Việt | Không thiên về cách viết nào khi chọn bài |
| Chỉ đếm trong ngữ cảnh chuyên ngành (cửa sổ 40 token có thuật ngữ cùng mảng) | "tinh chỉnh cài đặt điện thoại" không tính là fine-tuning |
| Trừ tần suất trong văn đời thường | "chú ý", "mất mát" xuất hiện khắp nơi |
| Mức đời thường (tần suất văn thường / văn kỹ thuật) ≥ 0,2 thì không tin số đếm | Thuật ngữ thật < 0,08, từ thông dụng ≥ 0,3 |
| Chỉ tính thuật ngữ dài nhất ở mỗi chỗ | "activation" bị đếm trong "activation function" |
| Chuẩn hóa dấu thanh kiểu cũ/mới | "khoá chính" và "khóa chính" là một |
| Trích cặp "X (EN)" / "EN (X)" tác giả tự chú thích | Cách dịch cho từ không có trong bảng nào |
| Gióng hàng trên song ngữ D2L (hệ số Dice) | Biết người dịch thật đã dịch mỗi từ thế nào |
| Lọc Wikipedia: tên bài phải trùng, thử thêm đuôi "(computer science)" | "callee" → cuộc gọi điện thoại, "garbage collection" → thu gom rác thải |
| Tỷ lệ viết hoa trong sách | Bỏ tên riêng (Linux, National Institute of ...) |
| wordfreq: tần suất tiếng Anh đời thường | Bỏ từ thông dụng (user, error), giữ từ chuyên ngành hiếm (mutex, semaphore) |
| Bớt mã thừa: đo trên 354 đoạn ngoài bộ chấm | Không chèn từ mô hình vốn dịch đúng (mỗi mã là một chỗ có thể rơi) |

## Tệp

- `tai_kho_vi.py`, `kho_en.py`: gom văn bản. `ung_vien_en.py`, `tim_thuat_ngu_en.py`: thuật ngữ ứng viên.
- `song_ngu_d2l.py`: gióng hàng. `dem_cach_dung.py`: đếm. `phan_loai.py`: xếp nhóm. `xay_bang_v5.py`: xuất bảng.
- `bot_ma_thua.py` → `mo_hinh_tu_dich_dung.csv`: từ không cần chèn.
- `nhan_xet_claude.csv`: nhận xét của người duyệt (sửa / bỏ, kèm lý do).
- `cho_xac_minh.csv`: thuật ngữ chưa đủ căn cứ, chưa vào bảng; dùng cho phiếu khảo sát tuần 3.
