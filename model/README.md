# model/ (chủ sở hữu: A)

Notebook chạy trên Kaggle (GPU T4 miễn phí). File mô hình lớn để trên Drive chung, không đưa vào Git.

- `notebooks/thu-translategemma.ipynb`: dịch thử nhiều cuốn sách bằng TranslateGemma 4B/12B, xuất Excel so sánh.
  Cần secret `HF_TOKEN` trên Kaggle và chấp nhận điều khoản Gemma trên Hugging Face.
- `notebooks/thi-nghiem-chen-thuat-ngu.ipynb` (tuần 1): dịch lại 270 đoạn có thuật ngữ của bộ thử bằng 4B, có và
  không chèn thuật ngữ, chấm như lúc lập mốc; thử thêm việc mô hình giữ dạng "overfitting (quá khớp)" và mã giữ chỗ.
  Chạy được trên Kaggle (cần một dataset chứa thư mục `terms/` và `eval/`) hoặc trên máy có GPU NVIDIA từ 6 GB
  (cách cài ở đầu notebook). Kết quả: `eval/thi_nghiem_chen_thuat_ngu.md`.
- `thi_nghiem_v5.py`: thí nghiệm 2, bảng v5 so với v4 (chạy trên máy có GPU: `python -m model.thi_nghiem_v5`).
- `thi_nghiem_thu_lai.py`: thí nghiệm 3, dịch lại đoạn bị rơi mã giữ chỗ (`python -m model.thi_nghiem_thu_lai`).
  Kết quả cả hai: `eval/thi_nghiem_v5_va_dich_lai.md`. Hai script dùng chung bộ nhớ đệm bản dịch
  `out/thi_nghiem_chen/cache_dich.json` (câu đã dịch thì không dịch lại).
- Sẽ thêm: tạo dữ liệu tinh chỉnh (tuần 2), LoRA và xuất GGUF (tuần 3).

Mẹo: chạy cả bộ bằng **Save Version → Save & Run All** để mất mạng cũng không bị ngắt.
