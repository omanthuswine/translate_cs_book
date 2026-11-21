"""Bot ma thua: thuat ngu nao mo hinh VON DA DICH DUNG thi thoi chen (chu so huu: A).

Thi nghiem 21/11: 57% so ma giu cho la cua thuat ngu mo hinh tu dich dung, va 43/91 ma bi roi la cua nhom nay.
Moi ma them vao la them mot cho co the roi, nen bo chen o nhung tu nay.

Do tren ban dich 4B KHONG chen (cot tg_4b cua bo thu 708 doan), chi dung cac doan van xuoi KHONG nam trong 270 doan
cua thi nghiem chen thuat ngu, de khong "hoc tu" bo cham. Mot thuat ngu duoc coi la mo hinh tu dich dung neu xuat
hien it nhat MIN_LAN lan va ban dich co dung cach viet cua bang (tieng Viet hoac tieng Anh) o it nhat TY_LE so doan.

Ket qua: terms/xay_dung/mo_hinh_tu_dich_dung.csv (en, so_doan, ty_le_dung). xay_bang_v5.py dat tu_dong = "không".
Chay (tu goc repo): python -m terms.xay_dung.bot_ma_thua [duong dan bang csv]
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MIN_LAN = 3
TY_LE = 0.9


def main() -> None:
    sys.path.insert(0, str(ROOT / "eval"))
    import cham_thuat_ngu as C
    from terms.core import _term_pattern, load_glossary
    from terms.xay_dung.dem_cach_dung import tach

    bang = load_glossary(sys.argv[1] if len(sys.argv) > 1 else ROOT / "terms" / "glossary_cs_vi_v5.csv")
    df = C.doc_bang(str(ROOT / "eval" / "data" / "so_sanh_ban_dich_danh_gia.xlsx"))
    prose = df[df.loai_doan == "văn xuôi"]
    giu_ngoai = prose[~prose.source.apply(lambda s: bool(C.tim_thuat_ngu(s)))]       # khong thuoc 270 doan bo cham
    out_tok = [" " + " ".join(tach(str(o))) + " " for o in giu_ngoai.tg_4b]
    rows = []
    for t in bang:
        # Chi xet tu ma lan dau va cac lan sau viet giong nhau (dịch, giữ tiếng Anh): bo chen cac tu "Anh (Việt)"
        # se mat luon chu thich o lan dau ("overfitting (quá khớp)") du mo hinh dich dung nghia.
        if not (t.tu_dong or t.ngu_canh) or t.lan_dau != t.lan_sau:
            continue
        rx = re.compile(rf"(?<![\w\-.])(?:{_term_pattern(t.source)})(?![\w\-(]|\.\w)")
        idx = [i for i, s in enumerate(giu_ngoai.source) if rx.search(s)]
        if len(idx) < MIN_LAN:
            continue
        cach_tok = " " + " ".join(tach(t.lan_sau)) + " "                 # dung cach viet cua bang
        dung = sum(cach_tok in out_tok[i] for i in idx)
        rows.append((t.source, len(idx), round(dung / len(idx), 2)))
    tu_dich_dung = [r for r in rows if r[2] >= TY_LE]
    path = Path(__file__).with_name("mo_hinh_tu_dich_dung.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["en", "so_doan", "ty_le_dung"])
        w.writerows(sorted(tu_dich_dung, key=lambda r: -r[1]))
    print(f"{len(giu_ngoai)} doan ngoai bo cham; {len(rows)} thuat ngu co tu {MIN_LAN} doan; "
          f"{len(tu_dich_dung)} mo hinh tu dich dung >= {TY_LE:.0%} -> {path}")
    for r in sorted(rows, key=lambda r: -r[1])[:30]:
        print(f"  {r[0]:28} {r[1]:3} doan, dung {r[2]:.0%}{'  -> bo chen' if r[2] >= TY_LE else ''}")


if __name__ == "__main__":
    main()
