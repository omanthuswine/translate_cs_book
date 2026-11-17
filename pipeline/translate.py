"""Goi mo hinh dich mot doan van (chu so huu: B).

A dung chinh ham translate() nay cho lan danh gia cuoi, de so lieu khop voi san pham.
"""
from __future__ import annotations


def fake_translate(text: str) -> str:
    """Dich gia: tra nguyen van. Dung de chay pipeline va test khi chua co mo hinh."""
    return text


def translate(text: str, server_url: str = "http://localhost:8080", timeout: float = 120) -> str:
    """Dich mot doan tieng Anh sang tieng Viet bang TranslateGemma chay tren llama.cpp server.

    TODO (B, tuan 1):
    - Kiem tra llama.cpp co ap dung dung khuon cau lenh cua TranslateGemma khong
      (dich thu 10 cau, so voi ban A chay tren Kaggle).
    - Neu khong, tu dung chuoi cau lenh theo khuon cua mo hinh va goi endpoint sinh chu tho
      (POST {server_url}/completion), tat sampling (temperature 0).
    - Bat loi ket noi, het thoi gian; tra loi ro rang cho nguoi dung.
    """
    raise NotImplementedError("Chua noi voi llama.cpp - viec tuan 1 cua B. Dung --fake de chay thu.")
