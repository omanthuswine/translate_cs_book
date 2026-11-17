# terms/ (chủ sở hữu: A)

- `glossary_cs_vi.csv`: bảng thuật ngữ chương trình đọc. Cột: `source, cach_xu_ly, lan_dau, lan_sau, linh_vuc, tu_dong`.
- `thuat_ngu_khmt_v4.xlsx`: cùng bảng đó dạng Excel, có sheet `nguyen_tac` giải thích quy tắc và nguồn đối chiếu. Sửa ở đây rồi xuất lại CSV.
- `core.py`: ba hàm `new_chapter`, `prepare`, `finalize`. Bản hiện tại trả nguyên văn bản; phần TODO là việc tuần 1–2 của A.

Bốn cách xử lý thuật ngữ:

| Cách xử lý | Lần đầu trong chương | Các lần sau |
| --- | --- | --- |
| giữ tiếng Anh | Quicksort | Quicksort |
| Anh (Việt) | overfitting (quá khớp) | overfitting |
| Việt (Anh) | ngăn xếp (stack) | ngăn xếp |
| dịch | thuật toán | thuật toán |
