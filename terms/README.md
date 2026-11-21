# terms/ (chủ sở hữu: A)

- `glossary_cs_vi.csv`: bảng thuật ngữ chương trình đọc. Cột: `source, cach_xu_ly, lan_dau, lan_sau, linh_vuc, tu_dong`.
- `thuat_ngu_khmt_v4.xlsx`: cùng bảng đó dạng Excel, có sheet `nguyen_tac` giải thích quy tắc và nguồn đối chiếu. Sửa ở đây rồi xuất lại CSV.
- `core.py`: ba hàm `new_chapter`, `prepare`, `finalize`, và hàm tùy chọn `retry_lost_terms` (dịch lại khi mất mã).
- `thuat_ngu_khmt_v5.xlsx`, `glossary_cs_vi_v5.csv`: **bảng v5 (976 mục) đang chờ nhóm duyệt**, làm từ dữ liệu, xem
  `xay_dung/README.md`. Chưa thay bảng đang dùng; thử bằng biến môi trường `DICH_SACH_GLOSSARY=terms/glossary_cs_vi_v5.csv`.
  Cột `tu_dong` của v5 có thêm giá trị `ngữ cảnh`.

Cách `prepare` xử lý một thuật ngữ tìm thấy (chỉ xét mục có `tu_dong = có`):

- Tìm không phân biệt hoa thường, cả số nhiều (stacks, matrices, leaves) và cách viết gạch nối/dấu cách
  (fine-tuning, fine tuning, finetuning); cụm dài được ưu tiên ("batch size" trước "batch").
  Từ viết tắt (GAN, NP, ReLU) khớp đúng hoa thường. Bỏ qua chỗ dính code: `nn.Dropout`, `softmax(x)`, `RNN-based`.
- Mọi cách viết trong bảng (Quicksort, "ngăn xếp (stack)", "overfitting (quá khớp)") được thay bằng mã giữ chỗ
  `[T1]`, `[T2]`… để mô hình không dịch mất hay viết lại; `finalize` đặt lại, kể cả khi mô hình đổi ngoặc hay thêm
  dấu cách. Tắt `PROTECT_ALL_FORMS` thì cách viết có tiếng Việt được chèn thẳng vào câu (kém hơn: sai thuật ngữ CLRS
  32% so với 11%).
- "recurrent neural networks (RNNs)": ngoặc viết tắt sẵn có bị bỏ để không thành "(RNN) (RNNs)".
- `tu_dong = ngữ cảnh` (từ đa nghĩa: attention, loss, kernel): chỉ chèn khi đoạn có ít nhất 2 thuật ngữ khác cùng mảng,
  hoặc chương đã gặp ít nhất 8 lần thuật ngữ cùng mảng. "Pay attention to..." thì để mô hình dịch thường.
- Công tắc thử nghiệm: `VI_TRI_BO_NGHIA = "chen_thang"` (mã đứng trước danh từ thì chèn thẳng tiếng Việt; đã thử,
  kém hơn, không dùng).

**Dịch lại khi mất mã** (`retry_lost_terms`, tùy chọn). Mô hình đôi khi bỏ mất mã, nhất là mã đứng trước danh từ
("the [T1] behavior"), làm thuật ngữ biến khỏi câu. Hàm này dịch lại riêng đoạn đó: lần 1 viết thẳng chữ bị mất vào
câu, nếu vẫn hỏng thì dịch từng câu; lấy bản ít hỏng nhất. Thí nghiệm 21/11: sai thuật ngữ 25/428 → 7/428 (ChatGPT
7/428), dịch lại 48/270 đoạn, thời gian dịch tăng khoảng 40%. B dùng bằng cách thêm một dòng trong `pipeline/run.py`:

```python
text_in, info = terms.prepare(segment, state)
result = translate_fn(text_in)
result, info = terms.retry_lost_terms(result, info, translate_fn)   # thêm dòng này
out.append(terms.finalize(result, info))
```

`finalize` đặt lại mã giữ chỗ (bỏ chữ lặp: "một mạng [T1]" → "một mạng sâu"), rồi dọn những thứ mô hình tự thêm khi
đoạn gốc không có: dấu "…", thẻ HTML (`<sup>8</sup>`), dấu `*` in nghiêng; và trả lại số thứ tự đầu mục ("1.") bị mất.

Bốn cách xử lý thuật ngữ:

| Cách xử lý | Lần đầu trong chương | Các lần sau |
| --- | --- | --- |
| giữ tiếng Anh | Quicksort | Quicksort |
| Anh (Việt) | overfitting (quá khớp) | overfitting |
| Việt (Anh) | ngăn xếp (stack) | ngăn xếp |
| dịch | thuật toán | thuật toán |
