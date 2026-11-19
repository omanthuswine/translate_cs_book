# terms/ (chủ sở hữu: A)

- `glossary_cs_vi.csv`: bảng thuật ngữ chương trình đọc. Cột: `source, cach_xu_ly, lan_dau, lan_sau, linh_vuc, tu_dong`.
- `thuat_ngu_khmt_v4.xlsx`: cùng bảng đó dạng Excel, có sheet `nguyen_tac` giải thích quy tắc và nguồn đối chiếu. Sửa ở đây rồi xuất lại CSV.
- `core.py`: ba hàm `new_chapter`, `prepare`, `finalize`. Bước dọn bản dịch ("…", markdown, số thứ tự) là TODO tuần 2.

Cách `prepare` xử lý một thuật ngữ tìm thấy (chỉ xét mục có `tu_dong = có`):

- Tìm không phân biệt hoa thường, cả số nhiều (stacks, matrices, leaves) và cách viết gạch nối/dấu cách
  (fine-tuning, fine tuning, finetuning); cụm dài được ưu tiên ("batch size" trước "batch").
  Từ viết tắt (GAN, NP, ReLU) khớp đúng hoa thường. Bỏ qua chỗ dính code: `nn.Dropout`, `softmax(x)`, `RNN-based`.
- Cách viết chỉ gồm chữ tiếng Anh (Quicksort, "overfitting" ở các lần sau, "RNN") được thay bằng mã giữ chỗ
  `[T1]`, `[T2]`… để mô hình không dịch mất; `finalize` đặt lại, kể cả khi mô hình đổi ngoặc hay thêm dấu cách.
- Cách viết có tiếng Việt ("ngăn xếp (stack)", "overfitting (quá khớp)") được chèn thẳng vào câu.
- "recurrent neural networks (RNNs)": ngoặc viết tắt sẵn có bị bỏ để không thành "(RNN) (RNNs)".

Bốn cách xử lý thuật ngữ:

| Cách xử lý | Lần đầu trong chương | Các lần sau |
| --- | --- | --- |
| giữ tiếng Anh | Quicksort | Quicksort |
| Anh (Việt) | overfitting (quá khớp) | overfitting |
| Việt (Anh) | ngăn xếp (stack) | ngăn xếp |
| dịch | thuật toán | thuật toán |
