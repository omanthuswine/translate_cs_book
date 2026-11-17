"""Module thuat ngu - ban khung (chu so huu: A).

Hien tai prepare() va finalize() tra nguyen van ban, de B ghep pipeline ngay tu tuan 1.
A thay phan TODO bang xu ly that; chu ky ham va kieu tra ve phai giu nguyen
(xem tests/test_contract.py).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

GLOSSARY_PATH = Path(__file__).with_name("glossary_cs_vi.csv")
GLOSSARY_COLUMNS = ("source", "cach_xu_ly", "lan_dau", "lan_sau", "linh_vuc", "tu_dong")


@dataclass(frozen=True)
class Term:
    source: str        # thuat ngu tieng Anh, vd "overfitting"
    cach_xu_ly: str    # "giữ tiếng Anh" | "Anh (Việt)" | "Việt (Anh)" | "dịch"
    lan_dau: str       # cach viet lan dau trong chuong, vd "overfitting (quá khớp)"
    lan_sau: str       # cach viet cac lan sau, vd "overfitting"
    linh_vuc: str
    tu_dong: bool      # False = tu da nghia, de mo hinh tu dich theo ngu canh


@dataclass
class ChapterState:
    """Trang thai cua mot chuong: nho thuat ngu nao da xuat hien de chi ghi ngoac o lan dau."""
    seen: set[str] = field(default_factory=set)


@lru_cache(maxsize=4)
def load_glossary(path: str | Path = GLOSSARY_PATH) -> tuple[Term, ...]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = set(GLOSSARY_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Bang thuat ngu thieu cot: {sorted(missing)}")
        return tuple(
            Term(r["source"], r["cach_xu_ly"], r["lan_dau"], r["lan_sau"], r["linh_vuc"], r["tu_dong"] == "có")
            for r in reader
        )


def new_chapter() -> ChapterState:
    return ChapterState()


def prepare(segment: str, state: ChapterState) -> tuple[str, dict]:
    """Truoc khi dua doan van cho mo hinh.

    Tra ve (van ban dua cho mo hinh, thong tin de finalize khoi phuc).

    TODO (A, tuan 1):
    - Tim thuat ngu trong `segment` (khong phan biet hoa thuong, ca so nhieu), uu tien cum dai truoc.
    - Tu "giữ tiếng Anh": thay bang ma giu cho, luu vao info de finalize dat lai.
    - Tu chen duoc (tu_dong = True): thay bang lan_dau neu chua co trong state.seen, nguoc lai lan_sau.
    - Cap nhat state.seen.
    """
    info: dict = {"placeholders": {}}
    return segment, info


def finalize(model_output: str, info: dict) -> str:
    """Sau khi mo hinh dich xong.

    TODO (A, tuan 1-2):
    - Dat lai cac tu duoc bao ve theo info["placeholders"].
    - Bo dau "…" mo hinh tu them, bo ky hieu markdown/HTML (*, <sub>), khoi phuc so thu tu dau muc.
    """
    text = model_output
    for code, original in info.get("placeholders", {}).items():
        text = text.replace(code, original)
    return text
