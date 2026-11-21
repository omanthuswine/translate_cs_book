"""Gióng hàng thuat ngu tren ban dich NGUOI cua D2L (nhanh v0.15) (chu so huu: A).

Moi doan tieng Anh goc nam trong <!-- ... --> va ngay sau la doan tieng Viet nguoi dich viet, nen co ~6.500 cap
doan song song. Voi moi thuat ngu:
- giu_en: ty le cap doan ma ban tieng Viet van giu nguyen chu tieng Anh (nguoi dich chon giu tieng Anh).
- vi: ty le cap doan ma ban tieng Viet co tung cach dich ung vien.
- goi_y: cum tieng Viet (2-5 tieng) di cung thuat ngu nhieu nhat, do bang he so Dice
  2*|cap co ca hai| / (|cap co thuat ngu| + |cap co cum tu|): cum gan nhu chi xuat hien khi co thuat ngu thi
  nhieu kha nang la ban dich cua no. Ky thuat gióng hàng tu kinh dien cua dich may thong ke.

Ket qua: cache/thuat_ngu/song_ngu_d2l.json
Chay (tu goc repo, sau dem_cach_dung): python -m terms.xay_dung.song_ngu_d2l
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from terms.xay_dung.dem_cach_dung import TU_CHUC_NANG, gop_ung_vien, la_cum_viet, so_nhieu, tach
from terms.xay_dung.tai_kho_vi import lam_sach_md

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cache" / "thuat_ngu"
D2L = CACHE / "nguon" / "d2l-vi"
MIN_CAP = 3                 # thuat ngu xuat hien it hon 3 cap doan: khong ket luan
_CAP = re.compile(r"<!--\s*\n(.*?)\n\s*-->\s*\n(.*?)(?=\n\s*<!--|\Z)", re.S)


def cap_doan() -> list[tuple[list[str], list[str]]]:
    """Cac cap (token tieng Anh, token tieng Viet) tu cac tep *_vn.md."""
    pairs = []
    for p in sorted(D2L.rglob("*_vn.md")):
        for en, vi in _CAP.findall(p.read_text(encoding="utf-8", errors="replace")):
            if "=====" in en or not en.strip() or not vi.strip():
                continue
            vi = re.sub(r"<!--.*?-->", " ", vi, flags=re.S)
            te, tv = tach(lam_sach_md(en)), tach(lam_sach_md(vi))
            if len(te) >= 4 and len(tv) >= 4:
                pairs.append((te, tv))
    return pairs


def _co(toks: list[str], cum: tuple) -> bool:
    n = len(cum)
    return any(tuple(toks[i:i + n]) == cum for i in range(len(toks) - n + 1))


def main() -> None:
    pairs = cap_doan()
    print(f"{len(pairs)} cap doan song song", flush=True)
    vi_sets = [set() for _ in pairs]             # moi cap: tap cac cum 2-5 tieng phia tieng Viet
    for k, (_, tv) in enumerate(pairs):
        for n in range(2, 6):
            for i in range(len(tv) - n + 1):
                vi_sets[k].add(tuple(tv[i:i + n]))
    df = Counter(g for s in vi_sets for g in s)  # so cap co moi cum
    out = {}
    for r in gop_ung_vien():
        forms_en = [tuple(f) for f in so_nhieu(tach(r["en"]))]
        if r["abbr"]:
            forms_en += [tuple(f) for f in so_nhieu(tach(r["abbr"]))]
        idx = [k for k, (te, _) in enumerate(pairs) if any(_co(te, f) for f in forms_en)]
        if len(idx) < MIN_CAP:
            continue
        giu = sum(any(_co(pairs[k][1], f) for f in forms_en) for k in idx) / len(idx)
        vi = {f: round(sum(_co(pairs[k][1], tuple(tach(f))) for k in idx) / len(idx), 2)
              for f in r["vi"] if tach(f)}
        cung = Counter(g for k in idx for g in vi_sets[k])
        goi_y = []
        for g, c in cung.items():
            if c < 2 or g[0] in TU_CHUC_NANG or g[-1] in TU_CHUC_NANG or not la_cum_viet(" ".join(g)):
                continue
            dice = 2 * c / (len(idx) + df[g])
            if dice >= 0.3:
                goi_y.append((" ".join(g), round(dice, 2), c))
        goi_y.sort(key=lambda x: (-x[1], -len(x[0])))
        # bo cum la manh cua cum khac co Dice gan bang ("hồi tiếp" trong "mạng nơ-ron hồi tiếp")
        gon = []
        for g, d, c in goi_y:
            if not any(g in g2 and d <= d2 + 0.05 for g2, d2, _ in gon):
                gon.append((g, d, c))
        out[r["en"].lower()] = {"so_cap": len(idx), "giu_en": round(giu, 2), "vi": vi, "goi_y": gon[:3]}
    path = CACHE / "song_ngu_d2l.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(out)} thuat ngu co tu {MIN_CAP} cap doan tro len -> {path}")


if __name__ == "__main__":
    main()
