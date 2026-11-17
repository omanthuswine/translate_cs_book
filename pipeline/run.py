"""Chay dich (chu so huu: B). Day la noi duy nhat goi module terms cua A.

Chay thu khong can mo hinh:
    python -m pipeline.run --text "Overfitting happens when ..." --fake
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable

import terms
from pipeline.translate import fake_translate, translate


def translate_chapter(segments: Iterable[str], translate_fn: Callable[[str], str]) -> list[str]:
    """Dich cac doan van cua mot chuong theo dung thu tu, qua ba buoc cua diem giao."""
    state = terms.new_chapter()
    out = []
    for segment in segments:
        text_in, info = terms.prepare(segment, state)
        result = translate_fn(text_in)
        out.append(terms.finalize(result, info))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Dich sach khoa hoc may tinh Anh -> Viet")
    p.add_argument("--text", help="dich mot doan van (chay thu)")
    p.add_argument("--pdf", help="duong dan sach PDF (chua lam - tuan 2)")
    p.add_argument("--fake", action="store_true", help="dich gia, khong goi mo hinh")
    p.add_argument("--server", default="http://localhost:8080")
    args = p.parse_args()

    fn = fake_translate if args.fake else (lambda t: translate(t, args.server))
    if args.text:
        print(translate_chapter([args.text], fn)[0])
    elif args.pdf:
        raise SystemExit("Dich ca file PDF la viec tuan 2 cua B (ghep BabelDOC).")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
