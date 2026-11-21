# eval/ (chủ sở hữu: A)

- `data/so_sanh_ban_dich_danh_gia.xlsx`: 708 đoạn từ Dive into Deep Learning và Introduction to Algorithms,
  bản dịch của TranslateGemma 4B, 12B và ChatGPT, kèm điểm chrF và cảnh báo lỗi từng đoạn. Sheet `tong_hop` có số liệu tổng.
- `ket_qua.csv`: mỗi lần chấm thêm một dòng. Ba dòng đầu là mốc xuất phát.
- `cham_thuat_ngu.py`: chấm tự động 20 thuật ngữ theo dõi của mốc. Chạy thử trên bộ thử:
  `python eval/cham_thuat_ngu.py eval/data/so_sanh_ban_dich_danh_gia.xlsx tg_4b tg_12b chatgpt`
- `thi_nghiem_chen_thuat_ngu.md`: kết quả thí nghiệm chèn thuật ngữ tuần 1 và đề xuất cho mốc 22/11.
  Mọi bản dịch của thí nghiệm: `data/thi_nghiem_chen_thuat_ngu_2026-11-21.xlsx`.
- `thi_nghiem_v5_va_dich_lai.md`: thí nghiệm 2 (bảng v5) và 3 (dịch lại đoạn rơi mã). Bản dịch:
  `data/thi_nghiem_v5_2026-11-21.xlsx`, `data/thi_nghiem_dich_lai_2026-11-21.xlsx`.
- Sẽ thêm: `data/tap_dap_an.csv` (150 đoạn sửa tay, tuần 2).

Cách đếm "sai thuật ngữ": chỉ tính dịch sai nghĩa hoặc bỏ sót (vd *recurrent* → "hồi quy", *recurrence* → "đệ quy"),
không tính khác cách diễn đạt.

Mốc được đếm theo cặp (đoạn văn xuôi, thuật ngữ), chia hai bộ theo nhóm thuật ngữ: `d2l` 14 từ (317 cặp), `dsa` 6 từ
thuật toán (111 cặp). Bộ chấm tự động cho lại mốc như sau (có test giữ trong `tests/test_cham_thuat_ngu.py`):

| | Mốc (đếm tay) | Tự động |
| --- | --- | --- |
| 4B, `d2l` sai nghĩa | 6/317 | 6/317 |
| 4B, `dsa` sai nghĩa + bỏ sót | 82/111 | 83/111 |
| ChatGPT, `d2l` / `dsa` | 4/317, 0/111 | 4/317, 0/111 |
| Nhất quán 4B / 12B / ChatGPT | 78 / 75 / 98% | 77.6 / 75.0 / 98.1% |

Ở `d2l` các bản dịch "khác" thường là diễn đạt khác nên mốc chỉ tính sai nghĩa; ở `dsa` chúng thường là bỏ sót nên
mốc tính cả hai. Ghi vào `ket_qua.csv` theo đúng quy ước đó để so được với ba dòng đầu. 12B ở `d2l` ra 9 thay vì 8
vì bộ chấm tính *regularization* → "chuẩn hóa" (normalization) là sai nghĩa.
