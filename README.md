# Dịch sách khoa học máy tính Anh → Việt

Công cụ miễn phí chạy trên máy cá nhân: mở sách PDF tiếng Anh, dịch sang tiếng Việt theo từng chương,
giữ nguyên bố cục và công thức, dùng thuật ngữ chuyên ngành nhất quán.

- **Mô hình dịch:** TranslateGemma 4B (Google), nén 4-bit, chạy bằng llama.cpp, không cần GPU rời.
- **Giữ bố cục PDF:** thư viện BabelDOC.
- **Thuật ngữ:** bảng 484 thuật ngữ trong `terms/glossary_cs_vi.csv`.

Kế hoạch đầy đủ (mục tiêu, lịch 5 tuần, rủi ro): xem tài liệu kế hoạch chung của nhóm.
Danh sách việc của từng người: [`docs/viec_nguoi_A.md`](docs/viec_nguoi_A.md), [`docs/viec_nguoi_B.md`](docs/viec_nguoi_B.md).

## Ai sở hữu thư mục nào

Mỗi thư mục chỉ một người sửa. Người kia chỉ đọc; muốn đổi gì thì báo chủ thư mục.

| Thư mục | Chủ | Nội dung |
| --- | --- | --- |
| `terms/` | A | Bảng thuật ngữ và module xử lý thuật ngữ (chèn, bảo vệ, dọn bản dịch) |
| `model/` | A | Notebook Kaggle: thí nghiệm, tạo dữ liệu, tinh chỉnh LoRA, xuất GGUF |
| `eval/` | A | Bộ thử, tập đáp án, kết quả đánh giá chất lượng |
| `pipeline/` | B | Đọc PDF, tách chương, gọi mô hình, ghép BabelDOC, lưu tiến độ |
| `app/` | B | Giao diện người dùng, chế độ Tự động / Nhẹ / Nhanh |
| `bench/` | B | Đo tốc độ, CPU, RAM trên laptop |
| `report/` | Chung | Báo cáo và slide (mỗi người viết phần của mình) |
| `tests/` | Chung | Kiểm tra hai bên vẫn khớp nhau ở điểm giao |

## Điểm giao giữa A và B

Toàn bộ việc dịch một đoạn văn đi qua ba bước, ở `pipeline/run.py`:

```python
state = terms.new_chapter()                    # A: gọi khi sang chương mới
text_in, info = terms.prepare(segment, state)  # A: chèn thuật ngữ, bảo vệ từ giữ tiếng Anh
result = translate(text_in)                    # B: gọi mô hình qua llama.cpp
text_out = terms.finalize(result, info)        # A: đặt lại từ được bảo vệ, dọn rác
```

Đổi tên hàm, tham số hoặc các cột của `glossary_cs_vi.csv` thì phải báo người kia và sửa `tests/test_contract.py`.

## Cài đặt

Cần Python 3.10–3.13.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp config.example.toml config.toml # rồi sửa đường dẫn mô hình
pytest                             # kiểm tra điểm giao
```

Chạy thử pipeline trên một đoạn văn, chưa cần mô hình (dịch giả, trả nguyên văn):

```bash
python -m pipeline.run --text "Overfitting happens when a model memorizes the training set." --fake
```

## File lớn không đưa vào Git

Mô hình `.gguf`, sách `.pdf`, kết quả chạy Kaggle để trong thư mục Drive chung.
Đặt tên có ngày, ví dụ `tg4b-lora-2026-12-04.gguf`. `.gitignore` đã chặn các loại file này.
