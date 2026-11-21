"""Chuyen cac sach KHMT tieng Anh mo ve van ban thuan, theo linh vuc (chu so huu: A).

Dung de: dem do pho bien cua thuat ngu ung vien, va tim them thuat ngu cho cac linh vuc con thieu.
Sach (tai bang tay vao cache/thuat_ngu/nguon_en/, xem terms/xay_dung/README.md):
  d2l-en (hoc sau), ods (cau truc du lieu), ostep (he dieu hanh), book = Computer Networks: A Systems Approach
  (mang), craftinginterpreters (ngon ngu lap trinh, trinh bien dich), dbdesign (co so du lieu), cybok (bao mat).

Ket qua: cache/thuat_ngu/kho_en/<sach>.jsonl, moi dong {"sach", "linh_vuc", "text"} (mot dong mot chuong/tep).
Chay (tu goc repo): python -m terms.xay_dung.kho_en
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cache" / "thuat_ngu" / "nguon_en"
OUT = ROOT / "cache" / "thuat_ngu" / "kho_en"

SACH = {  # thu muc: (linh vuc, kieu tep)
    "d2l-en": ("Học sâu", "md"),
    "ods": ("Cấu trúc dữ liệu", "tex"),
    "ostep": ("Hệ điều hành", "pdf"),
    "book": ("Mạng", "rst"),
    "craftinginterpreters": ("Ngôn ngữ lập trình", "md"),
    "dbdesign": ("Cơ sở dữ liệu", "xhtml"),
    "cybok": ("Bảo mật", "pdf"),
}


def _md(t: str) -> str:
    t = re.sub(r"```.*?```|~~~.*?~~~", " ", t, flags=re.S)
    t = re.sub(r"\$\$.*?\$\$|\$[^$\n]+\$|<[^>]+>|:\w+:`[^`]*`|`[^`]*`", " ", t, flags=re.S)
    return re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)


def _rst(t: str) -> str:
    t = re.sub(r"^\.\. [^\n]*(?:\n(?:[ \t]+[^\n]*|\s*))*", " ", t, flags=re.M)     # directive + khoi thut le
    t = re.sub(r"::\s*\n(?:\s*\n)?(?:[ \t]+[^\n]*\n|\s*\n)+", ".\n", t)              # khoi code sau "::"
    return re.sub(r":\w+:`([^`<]*)(?:<[^>]*>)?`|`+([^`]*)`+_?", r"\1\2", t)


def _tex(t: str) -> str:
    t = re.sub(r"(?<!\\)%.*", "", t)
    t = re.sub(r"\\begin\{(code|lstlisting|verbatim|tabular|figure|equation\*?|align\*?)\}.*?\\end\{\1\}", " ", t, flags=re.S)
    t = re.sub(r"\$\$.*?\$\$|\$[^$]*\$|\\\[.*?\\\]", " ", t, flags=re.S)
    t = re.sub(r"\\(?:emph|textit|textbf|texttt|index|chapter|section|subsection|paragraph)\*?\{([^{}]*)\}", r"\1", t)
    return re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?|[{}]", " ", t)


def _xhtml(t: str) -> list[str]:
    t = re.sub(r"<(script|style|pre|code)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    parts = re.split(r"<h1[^>]*>", t)                                               # moi chuong mot dong
    return [html.unescape(re.sub(r"<[^>]+>", " ", p)) for p in parts]


def _pdf(path: Path) -> list[str]:
    import fitz                                                                     # PyMuPDF
    with fitz.open(path) as doc:
        pages = [p.get_text() for p in doc]
    if len(pages) > 60:                                                             # sach dai: gop 20 trang mot dong
        return ["\n".join(pages[i:i + 20]) for i in range(0, len(pages), 20)]
    return ["\n".join(pages)]


def lam_sach(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    t = re.sub(r"-\n(?=[a-z])", "", t)                                              # noi tu bi ngat dong
    return re.sub(r"\s+", " ", t).strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for sach, (linh_vuc, kieu) in SACH.items():
        base = SRC / sach
        if not base.exists():
            print(f"  {sach}: chua co trong {base}, bo qua")
            continue
        docs: list[str] = []
        for p in sorted(base.rglob(f"*.{kieu}")):
            if ".git" in p.parts:
                continue
            if kieu == "pdf":
                docs += _pdf(p)
                continue
            raw = p.read_text(encoding="utf-8", errors="replace")
            docs += _xhtml(raw) if kieu == "xhtml" else [{"md": _md, "rst": _rst, "tex": _tex}[kieu](raw)]
        docs = [d for d in (lam_sach(x) for x in docs) if len(d) >= 300]
        with open(OUT / f"{sach}.jsonl", "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps({"sach": sach, "linh_vuc": linh_vuc, "text": d}, ensure_ascii=False) + "\n")
        n_words = sum(len(d.split()) for d in docs)
        print(f"  {sach:22} {linh_vuc:20} {len(docs):4} doan, {n_words / 1000:6.0f} nghin tu")


if __name__ == "__main__":
    main()
