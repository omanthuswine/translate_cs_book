"""Tach sach PDF thanh chuong (chu so huu: B)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chapter:
    title: str
    first_page: int   # tinh tu 1
    last_page: int    # tinh ca trang nay


def split_chapters(pdf_path: str) -> list[Chapter]:
    """Doc muc luc (bookmark) cua PDF, tra ve danh sach chuong.

    TODO (B, tuan 2):
    - Dung PyMuPDF: fitz.open(pdf_path).get_toc() -> [[level, title, page], ...], lay level 1.
    - Sach khong co muc luc: tra ve mot chuong gom ca cuon, de giao dien cho nguoi dung nhap khoang trang.
    """
    raise NotImplementedError("Viec tuan 2 cua B")


def page_has_text(pdf_path: str, page_no: int, min_chars: int = 30) -> bool:
    """Trang co lop chu khong (False = anh scan, bao cho nguoi dung).

    TODO (B, tuan 3).
    """
    raise NotImplementedError("Viec tuan 3 cua B")
