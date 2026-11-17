# Quy ước làm việc

## Nhánh và gộp code

- `main` luôn chạy được: `pytest` phải xanh.
- Mỗi việc một nhánh, đặt tên theo người và việc: `a/chen-thuat-ngu`, `b/tach-chuong`.
- Xong việc thì mở Pull Request vào `main`. PR chỉ sửa thư mục mình sở hữu thì tự gộp được;
  PR đụng thư mục của người kia (hoặc `tests/test_contract.py`) phải để người kia duyệt.

## Họp

15 phút vào thứ Tư và Chủ nhật. Mỗi người nói: đã xong gì, đang vướng gì, có cần đổi điểm giao không.
Buổi Chủ nhật kiểm tra mốc của tuần.

## Ghi số liệu ngay khi có

Mỗi lần chạy thí nghiệm hoặc đo tốc độ, thêm một dòng vào:

- `eval/ket_qua.csv` (A): chất lượng dịch
- `bench/ket_qua.csv` (B): tốc độ và tài nguyên

Tuần 5 chỉ việc lấy ra vẽ bảng, không phải chạy lại.

## Commit

Viết bằng tiếng Việt, câu ngắn nói đã làm gì: `Thêm bảo vệ từ giữ tiếng Anh bằng mã giữ chỗ`.
