# Thí nghiệm chèn thuật ngữ (tuần 1, 21/11/2026)

**Câu hỏi của mốc 22/11:** chỉ chèn thuật ngữ trước khi dịch đã đủ, hay phải tinh chỉnh LoRA?

**Trả lời ngắn:** chèn thuật ngữ bằng mã giữ chỗ đưa tỷ lệ sai thuật ngữ ở sách thuật toán từ **75% xuống 11%**
và độ nhất quán từ **78% lên 92%**, câu văn gần như không kém đi. Đề xuất: **chưa làm LoRA**, dùng cách chèn mã và
vá các lỗi còn lại bằng code (mục "Đề xuất").

## Cách làm

- **Bộ thử:** 270 đoạn văn xuôi của bộ thử 708 đoạn có chứa ít nhất một trong 20 thuật ngữ theo dõi, phủ đủ
  317 + 111 lần đếm của mốc xuất phát.
- **Mô hình:** TranslateGemma 4B, nén 4-bit bitsandbytes (nf4), không lấy mẫu, cùng cấu hình lúc lập mốc trên Kaggle.
  Chạy trên laptop RTX 4050 6 GB, khoảng 30 token/giây.
- **Ba nhánh:**
  - `khong_chen`: dịch câu gốc.
  - `chen`: `terms.prepare` chèn thẳng cách viết tiếng Việt vào câu; từ tiếng Anh (Quicksort, RNN…) thay bằng mã `[T1]`.
  - `chen_ma`: mọi cách viết trong bảng, cả tiếng Việt, đều thay bằng mã; `finalize` dán chữ đúng vào sau khi dịch
    (`PROTECT_ALL_FORMS = True` trong `terms/core.py`).
- **Chấm:** `eval/cham_thuat_ngu.py`, cho lại đúng số liệu mốc; chrF so với bản ChatGPT, trung bình theo đoạn.
- Notebook: `model/notebooks/thi-nghiem-chen-thuat-ngu.ipynb`. Mọi bản dịch:
  `eval/data/thi_nghiem_chen_thuat_ngu_2026-11-21.xlsx` (sheet `so_sanh` đặt các bản cạnh nhau để đọc tay).

## Kết quả

| | Không chèn | Chèn thẳng (`chen`) | Chèn mã (`chen_ma`) | ChatGPT |
| --- | --- | --- | --- | --- |
| Sai thuật ngữ, sách thuật toán (`dsa`, sai nghĩa + bỏ sót) | 83/111 (**75%**) | 35/111 (32%) | 12/111 (**11%**) | 0/111 |
| Sai nghĩa, sách học sâu (`d2l`) | 6/317 | 1/317 | 1/317 | 4/317 |
| Nhất quán thuật ngữ | **78%** | 85% | **92%** | 98% |
| chrF, sách học sâu | 66,9 | 66,7 | 65,6 | – |
| chrF, sách thuật toán | 53,8 | 56,1 | 58,4 | – |
| Mã giữ chỗ được đặt lại | – | 95,3% (300 mã) | 92,5% (1.216 mã) | – |

- Nhánh `khong_chen` chạy lại cho đúng số của mốc (83/111, 6/317, 78%), nên lần chạy trên laptop so được với Kaggle.
- chrF ở đây tính trên 270 đoạn, không so thẳng với chrF 65,7 / 55,1 của mốc (tính trên 708 đoạn).

**Phép thử phụ 1: mô hình có giữ dạng "overfitting (quá khớp)" khi chèn thẳng không?** Không. Trên 135 dạng có ngoặc
(100 đoạn): giữ nguyên 36%, mất phần trong ngoặc 52%, đảo thứ tự 6%, khác dạng 4%, mất hẳn 2%. Mô hình còn hay viết lại
chữ đã chèn ("ký hiệu tiệm cận" → "ký hiệu gần đúng", "hệ thức truy hồi" → "công thức hồi quy").

**Phép thử phụ 2: dạng mã nào được giữ tốt nhất?** Trên cùng 40 đoạn (88 mã): `[T1]` 96,6%, `TERM1` 95,5%, `<T1>` 88,6%,
`{T1}` 87,5%. Giữ dạng `[T1]`.

## Lỗi còn lại của cách chèn mã

**Cả 12 lần sai ở sách thuật toán đều do mô hình làm rơi mã**, không lần nào do tìm sót thuật ngữ. Mã rơi thì thuật ngữ
biến mất khỏi câu. 56/269 đoạn rơi ít nhất một mã. Mã dễ rơi khi:

| Tình huống | Tỷ lệ rơi |
| --- | --- |
| Mã đứng riêng ("the [T1] is…") | 6,2% (53/856) |
| Mã làm tính từ trước danh từ ("the [T1] behavior", "our [T1] system"): tiếng Việt phải đảo trật tự mà mô hình không biết [T1] là gì | **11,2%** (38/340) |
| Đoạn có trên 8 mã | 10% (42/416) |

"asymptotic" chiếm 8/12 lỗi vì gần như luôn là tính từ. Lỗi phụ khác: chữ lặp khi mô hình tự thêm danh từ trước mã
("phương pháp phương pháp Master", "mạng mạng sâu"); câu gốc vỡ chữ từ PDF ("Let's ûnd" thay cho "find") làm mô hình
dịch lệch hoặc bịa câu.

## Đề xuất

1. **Mốc 22/11: chưa cần LoRA.** Mục tiêu thuật ngữ đạt được mà không huấn luyện. Kaggle đã hết giờ và LoRA trên GPU 6 GB
   rất chật; LoRA cũng không sửa được lỗi do PDF vỡ chữ hay từ đa nghĩa.
2. **Đổi mặc định sang chèn mã** (`PROTECT_ALL_FORMS = True`). Điểm giao với B không đổi.
3. **Việc của A, tuần 2:** thêm cụm ghép hay đứng ở vị trí tính từ vào bảng ("asymptotic behavior" → "hành vi tiệm cận"…);
   `finalize` bỏ chữ lặp trước mã, cùng các việc dọn bản dịch đã có trong kế hoạch; đặt `tu_dong = không` cho từ đa nghĩa
   như *feature* (có lúc là động từ).
4. **Cần bàn với B:** chữ PDF bị vỡ (`û` thay cho `fi`) nên sửa ở bước đọc PDF; khi `finalize` thấy mất mã thì cắt đoạn
   thành câu ngắn rồi dịch lại (cần thêm một hàm nhỏ ở điểm giao để báo mã bị mất).
5. Sau các bước trên, chạy lại thí nghiệm (khoảng 1 giờ) để đo. Chỉ khi mã vẫn rơi nhiều mới cân nhắc LoRA, nhắm riêng
   vào việc dạy mô hình giữ mã.
