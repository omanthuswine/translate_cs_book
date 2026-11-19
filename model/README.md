# model/ (chủ sở hữu: A)

Notebook chạy trên Kaggle (GPU T4 miễn phí). File mô hình lớn để trên Drive chung, không đưa vào Git.

- `notebooks/thu-translategemma.ipynb`: dịch thử nhiều cuốn sách bằng TranslateGemma 4B/12B, xuất Excel so sánh.
  Cần secret `HF_TOKEN` trên Kaggle và chấp nhận điều khoản Gemma trên Hugging Face.
- `notebooks/thi-nghiem-chen-thuat-ngu.ipynb` (tuần 1): dịch lại 270 đoạn có thuật ngữ của bộ thử bằng 4B, có và
  không chèn thuật ngữ, chấm như lúc lập mốc; thử thêm việc mô hình giữ dạng "overfitting (quá khớp)" và mã giữ chỗ.
  Cần thêm một dataset Kaggle chứa thư mục `terms/` và `eval/` của repo (nén zip rồi tải lên).
- Sẽ thêm: tạo dữ liệu tinh chỉnh (tuần 2), LoRA và xuất GGUF (tuần 3).

Mẹo: chạy cả bộ bằng **Save Version → Save & Run All** để mất mạng cũng không bị ngắt.
