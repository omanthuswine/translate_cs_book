# Việc của Người B: hệ thống và ứng dụng

Bạn sở hữu `pipeline/`, `app/`, `bench/`. Mọi thứ **xung quanh** việc dịch là việc của bạn:
đọc PDF, gọi mô hình, ghép lại PDF, giao diện, tốc độ, không làm máy người dùng bị đơ.
Bạn dùng của A: module `terms` (chỉ gọi `new_chapter`, `prepare`, `finalize`) và file mô hình GGUF.

Bắt đầu: chạy `pytest` và `python -m pipeline.run --text "..." --fake` để thấy luồng chạy hiện tại.

## Tuần 1 (17–22/11): kiểm chứng

- [ ] Cài llama.cpp (hoặc LM Studio), tải TranslateGemma 4B dạng GGUF Q4_K_M, đo tốc độ chỉ dùng CPU:
      token/giây, RAM, % CPU. Ghi vào `bench/ket_qua.csv`. Cần khoảng 10–15 token/giây để dịch kịp tốc độ đọc
- [ ] Viết `pipeline/translate.py: translate()` gọi llama.cpp server; dịch thử 10 câu, so với bản A chạy trên Kaggle
      để chắc khuôn câu lệnh đúng
- [ ] Cài BabelDOC, dịch thử một chương, ghi lỗi tiếng Việt: mất dấu, sai font, chữ tràn khung
- [ ] Cho BabelDOC gọi mô hình trên máy qua địa chỉ localhost kiểu API OpenAI

**Mốc 22/11:** BabelDOC có dùng được với tiếng Việt không; laptop có đủ nhanh không.

## Tuần 2 (23–29/11): pipeline chạy trọn

- [ ] `pipeline/chapters.py: split_chapters()` đọc mục lục PDF
- [ ] `python -m pipeline.run --pdf sach.pdf`: PDF → chương → dịch từng đoạn → PDF song ngữ, dùng mô hình gốc
- [ ] Lưu tiến độ theo trang để chạy tiếp được khi bị ngắt

**Mốc 29/11:** dịch trọn một chương từ đầu đến cuối.

## Tuần 3 (30/11–6/12): dịch theo nhu cầu

- [ ] Mở trang nào dịch trang đó trước, dịch sẵn 3–5 trang tiếp theo (`pages_ahead` trong `config.toml`)
- [ ] Chế độ Tự động / Nhẹ / Nhanh: đọc cấu hình máy bằng `psutil`, nghỉ giữa các trang khi máy bận hoặc chạy pin
- [ ] `page_has_text()`: phát hiện trang scan và báo cho người dùng
- [ ] Thay mô hình gốc bằng bản tinh chỉnh của A (chỉ đổi `config.toml`)

## Tuần 4 (7–13/12): giao diện và đo hiệu năng

- [ ] `app/app.py` bằng Gradio: chọn sách, chọn chương, xem song ngữ, chọn chế độ
- [ ] Đo: thời gian ra trang đầu, có dịch kịp tốc độ đọc không, CPU/RAM khi vừa dịch vừa mở trình duyệt

## Tuần 5 (14–20/12): đóng gói và báo cáo

- [ ] Hướng dẫn cài đặt vài bước, video demo dịch trọn một chương
- [ ] Viết phần kiến trúc hệ thống và hiệu năng (`report/`)
