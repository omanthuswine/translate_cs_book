# Thí nghiệm 2 và 3: bảng thuật ngữ v5, dịch lại đoạn rơi mã (21/11/2026)

Tiếp theo [thi_nghiem_chen_thuat_ngu.md](thi_nghiem_chen_thuat_ngu.md). Cùng 270 đoạn, cùng mô hình (TranslateGemma 4B,
nén 4-bit, không lấy mẫu), chạy trên laptop RTX 4050.

**Trả lời ngắn:**

- Bảng v5 (976 mục) giữ nguyên mức đúng thuật ngữ của v4 trên 270 đoạn này. Tác dụng chính của nó là phủ toàn bộ khoa
  học máy tính cho sách khác.
- **Dịch lại riêng những đoạn bị rơi mã** đưa lỗi thuật ngữ từ **25/428 xuống 7/428**, bằng ChatGPT, và nâng độ nhất quán
  lên 96,7%. Chỉ 48/270 đoạn phải dịch lại.

## Cách làm

- `model/thi_nghiem_v5.py` (thí nghiệm 2):
  - `chen_ma_v4`: tốt nhất của lần 1.
  - `v5`: bảng v5, chèn theo ngữ cảnh, bớt mã thừa, dọn bản dịch.
  - `v5_bo_nghia`: như v5, nhưng mã đứng trước danh từ thì chèn thẳng chữ tiếng Việt.
- `model/thi_nghiem_thu_lai.py` (thí nghiệm 3): lấy bản `v5`. Đoạn nào bản dịch thiếu mã `[Tn]` thì dịch lại. Lúc chạy
  thật cũng biết được điều này, vì không cần bản mẫu.
  1. **Chèn thẳng:** mã bị rơi được thay bằng chính chữ nó đại diện ("the [T1] behavior" → "the tiệm cận behavior").
  2. **Tách câu:** nếu vẫn hỏng, cắt đoạn thành từng câu rồi dịch từng câu.
  3. **Chọn:** lấy bản ít "chỗ hỏng" nhất. Chỗ hỏng là mã còn thiếu, hoặc chữ đã chèn thẳng mà không còn trong bản dịch.
     Hòa thì giữ bản gốc.
- **Chấm hai kiểu:**
  - Kiểu mốc (`eval/cham_thuat_ngu.py`), để so với các dòng cũ trong `ket_qua.csv`.
  - Kiểu theo bảng v5 (`THEO_DOI_V5`): v5 cố ý viết "hidden state (trạng thái ẩn)" rồi "hidden state", nên kiểu mốc
    đếm nhầm là "khác".

## Kết quả

| | Không chèn | Chèn mã v4 | v5 | v5 bổ nghĩa | **v5 + dịch lại** | ChatGPT |
| --- | --- | --- | --- | --- | --- | --- |
| Sai thuật ngữ sách thuật toán (kiểu mốc) | 83/111 | 12/111 | 12/111 | 17/111 | **5/111** | 0/111 |
| Sai thuật ngữ, cả hai sách (theo bảng v5) | 99/428 | 25/428 | 25/428 | 29/428 | **7/428** | 7/428 |
| Nhất quán (theo bảng v5) | 77,6% | 90,9% | 92,3% | 92,8% | **96,7%** | 97,2% |
| chrF sách học sâu | 67,0 | 65,7 | 63,6 | 63,6 | 63,7 | – |
| chrF sách thuật toán | 53,8 | 58,4 | 58,4 | 58,4 | 58,6 | – |
| Mã được đặt lại | – | 92,5% (1.216) | 92,4% (1.062) | 94,0% (887) | – | – |

- **Dịch lại:** 48/270 đoạn (25% số ký tự).
  - Tổng chỗ hỏng: bản gốc 81, chèn thẳng 52, tách câu 34.
  - Bản được chọn: tách câu 19 đoạn, chèn thẳng 17, giữ bản gốc 12.
  - Làm lần lượt (chèn thẳng trước, chỉ tách câu khi còn hỏng) cho cùng kết quả và tốn 197 lần gọi mô hình thay vì 246.
  - Ước tính thời gian dịch một cuốn sách tăng khoảng 40%.
- **Chèn thẳng ở vị trí bổ nghĩa** (`v5_bo_nghia`) làm ngay từ đầu thì **kém hơn** (17/111). Chỉ nên dùng như cách dịch
  lại cho đoạn đã rơi mã.
- **Dọn bản dịch** (`finalize`) xóa hết lỗi mô hình tự thêm khi đoạn gốc không có:
  - dấu "…": 12 → 0 đoạn;
  - thẻ HTML / dấu `*`: 8 → 0;
  - số thứ tự đầu mục bị mất: 7 → 0.
- **chrF sách học sâu giảm** (65,7 → 63,6) vì v5 theo nguyên tắc "lưng chừng thì Anh (Việt)", nên viết khác bản ChatGPT
  dùng làm mẫu. Đây là khác cách viết, không phải sai nghĩa. Cần bộ đáp án sửa tay tuần 2 để đo đúng.
- **Bớt mã thừa** giảm số mã (1.216 → 1.062) nhưng không giảm tỷ lệ rơi mã.

## Lỗi còn lại (v5 + dịch lại)

- 4 lỗi là "asymptotic" trong "the asymptotic behavior", "asymptotic bounds": mã vẫn rơi sau cả hai cách dịch lại.
- Còn lại: 1 lỗi "recurrence", 2 lỗi diễn đạt ở sách học sâu.

## Đề xuất

1. **Đưa "dịch lại đoạn rơi mã" vào chương trình.** A đã viết `terms.retry_lost_terms` (chạy lại trên 270 đoạn cho
   đúng 5/111 và 7/428 như trên). B chỉ cần thêm một dòng trong `pipeline/run.py`, xem `terms/README.md`. Ba hàm cũ
   (`new_chapter`, `prepare`, `finalize`) không đổi.
2. **Thêm cụm ghép vào bảng** để sửa nốt "asymptotic": "asymptotic behavior" → "hành vi tiệm cận", "asymptotic bound" →
   "cận tiệm cận". Cần nhóm đồng ý, và nên kiểm tra trên sách khác vì lỗi được tìm ra trên chính bộ thử này.
3. **Sửa chữ vỡ từ PDF ở bước đọc PDF (việc của B):**
   - 82/185 đoạn CLRS có ký tự vỡ (`û` = fi, `ü` = fl: "ûnd", "üoors", "deûned").
   - Thay ký tự rồi kiểm tra bằng từ điển (`wordfreq`) sửa chắc chắn 133/138 lần.
   - 5 lần còn lại: tên riêng có dấu thật (Müller) và từ bị ngắt dòng ("difû- cult"), phải nối gạch nối trước.
   - Chữ vỡ còn làm bảng thuật ngữ tìm sót: "overûtting" không khớp "overfitting".
4. **Chưa cần LoRA.** Lỗi thuật ngữ đã ngang ChatGPT mà không phải huấn luyện.
