# Việc của Người A: mô hình và chất lượng dịch

Bạn sở hữu `terms/`, `model/`, `eval/`. Mọi thứ làm thay đổi **chữ được dịch ra** là việc của bạn.
Bạn giao cho B: module thuật ngữ (`terms/core.py`) và file mô hình GGUF.

Mốc xuất phát cần vượt qua (chi tiết trong `eval/ket_qua.csv`): bản 4B dịch sai 82/111 lần (74%) thuật ngữ
ở sách thuật toán, thuật ngữ nhất quán 78% so với 98% của ChatGPT.

## Tuần 1 (17–22/11): kiểm chứng

- [ ] Đọc `terms/thuat_ngu_khmt_v4.xlsx`, duyệt 100 thuật ngữ có "Số lần trong bộ thử" cao nhất
- [ ] Thí nghiệm chèn thuật ngữ trên Kaggle: khoảng 200 đoạn có thuật ngữ từ `eval/data/so_sanh_ban_dich_danh_gia.xlsx`,
      dịch bằng 4B có và không chèn, so tỷ lệ sai. Notebook mẫu: `model/notebooks/thu-translategemma.ipynb`
- [ ] Kiểm tra mô hình có giữ nguyên dạng "overfitting (quá khớp)" và mã giữ chỗ không
- [ ] Viết `prepare` và `finalize` thật trong `terms/core.py` (xem các TODO), giữ `pytest` xanh
- [ ] Ghi kết quả vào `eval/ket_qua.csv`

**Mốc 22/11:** kết luận có cần tinh chỉnh LoRA không.

## Tuần 2 (23–29/11): nền móng

- [ ] Nếu cần LoRA: tạo 3.000–5.000 cặp câu bằng bản 12B có chèn thuật ngữ, lọc câu sai thuật ngữ
- [ ] Tập đáp án 150 đoạn: lấy bản ChatGPT, sửa tay cho đúng, lưu `eval/data/tap_dap_an.csv`
- [ ] Hoàn thiện `finalize`: bỏ "…" tự thêm, bỏ `*` và `<sub>`, khôi phục số thứ tự "1.", "2."

## Tuần 3 (30/11–6/12): mô hình

- [ ] Tinh chỉnh LoRA trên Kaggle, chấm trên tập đáp án, lặp 1–2 lần
- [ ] Gộp LoRA, xuất GGUF Q4_K_M, để lên Drive chung và báo B tên file
- [ ] Soạn phiếu khảo sát cho khoảng 80 thuật ngữ nhóm "Anh (Việt)" và "Việt (Anh)"

## Tuần 4 (7–13/12): đánh giá cuối

- [ ] Chấm cuối qua hàm `pipeline.translate.translate` của B: sai thuật ngữ, nhất quán, chrF, giữ code
- [ ] Gửi khảo sát cho 5–10 bạn, cập nhật bảng thuật ngữ

## Tuần 5 (14–20/12): báo cáo

- [ ] Viết phần bảng thuật ngữ, dữ liệu, mô hình, đánh giá chất lượng (`report/`)
