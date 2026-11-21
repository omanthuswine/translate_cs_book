"""Tim them thuat ngu tu sach KHMT tieng Anh (cache/thuat_ngu/kho_en/) cho cac linh vuc con thieu (chu so huu: A).

Ba lop loc, khong can nguoi duyet:
1. Cum tu (1-4 tu) lap lai it nhat MIN_COUNT lan trong mot cuon sach, khong bat dau/ket thuc bang tu chuc nang.
2. Tu don phai xuat hien trong sach nhieu hon han tieng Anh doi thuong (Zipf trong sach - Zipf chung >= ZIPF_GAP,
   tuc gap khoang 30 lan) va khong qua thong dung (Zipf chung < ZIPF_MAX), hoac la tu viet tat.
3. Cum tu phai co bai Wikipedia rieng (khong phai trang dinh huong) MANG DUNG TEN cum tu do (cho phep khac so
   nhieu, hoa thuong). Wikipedia hay chuyen huong sang bai khac nghia ("callee" -> cuoc goi dien thoai,
   "repo" -> hop dong mua lai chung khoan) nen bai khac ten bi loai. Tu viet tat thi nhan neu chu cai dau cua
   ten bai khop ("RBAC" -> Role-based access control); khi do lay ten bai lam thuat ngu, tu viet tat lam abbr.
   Lay luon ten bai tieng Viet tuong ung lam cach dich ung vien.

Ket qua: cache/thuat_ngu/ung_vien_sach.json, moi muc {"en", "linh_vuc", "dem": {sach: so lan}, "wiki", "vi"}.
Chay (tu goc repo): python -m terms.xay_dung.tim_thuat_ngu_en
"""
from __future__ import annotations

import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

from terms.xay_dung.ung_vien_en import _api, nfc

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cache" / "thuat_ngu"
MIN_COUNT = 5
ZIPF_MAX = 4.8              # tu don thong dung hon muc nay (process, file, key...) qua da nghia, khong lay tu dong
ZIPF_GAP = 1.5
TOP_PER_BOOK = 2500         # so cum tu pho bien nhat moi sach dem di kiem tra tren Wikipedia

STOP = set("""a an the and or but if then else of to in on at by for with from into onto over under as is are was
were be been being am do does did done have has had having this that these those it its it's they them their there
here which who whom whose what when where why how all any each every some such no not only own same so than too very
can could may might must shall should will would one two three first second new also just more most other many much
few less least many well even still yet about above after again against below between both during further once out
off up down through until while before because nor our ours you your yours we us he him his she her hers i me my
mine let lets use used using uses see seen like e.g i.e etc via per thus hence however therefore section chapter
figure example examples note""".split())
# Khong cho "table", "time", "set", "number", "case" vao day: se mat page table, running time, instruction set,
# port number, base case. Cum vo nghia ("same time") da bi lop loc Wikipedia loai.
MID_OK = {"of", "and", "to", "in", "for", "on"}       # "denial of service", "divide and conquer"
DUOI_LINH_VUC = ("computer science", "computing", "programming", "operating systems", "networking")
_SENT = re.compile(r"[.!?;:()\[\]\"“”]|,\s")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9+#]*(?:[-'][A-Za-z0-9]+)*")


def ngrams(text: str):
    for sent in _SENT.split(text):
        toks = _WORD.findall(sent)
        low = [t.lower() for t in toks]
        for n in (1, 2, 3, 4):
            for i in range(len(toks) - n + 1):
                g = low[i:i + n]
                if g[0] in STOP or g[-1] in STOP or any(w in STOP and w not in MID_OK for w in g[1:-1]):
                    continue
                if n == 1 and (len(g[0]) < 3 or g[0].endswith("'s")):
                    continue
                yield " ".join(toks[i:i + n]) if n == 1 and toks[i].isupper() else " ".join(g)


def dem_sach() -> tuple[dict[str, Counter], Counter]:
    dem: dict[str, Counter] = defaultdict(Counter)
    tong_tu: Counter = Counter()
    nguyen: Counter = Counter()                       # tu giu nguyen hoa thuong, de biet tu nao la ten rieng
    cum_hoa: Counter = Counter()                      # cum 2-6 tu ma moi tu deu viet hoa chu dau (ten rieng)
    for p in sorted((CACHE / "kho_en").glob("*.jsonl")):
        for line in open(p, encoding="utf-8"):
            d = json.loads(line)
            dem[d["sach"]].update(ngrams(d["text"]))
            words = _WORD.findall(d["text"])
            tong_tu[d["sach"]] += len(words)
            nguyen.update(words)
            for sent in _SENT.split(d["text"]):
                toks = _WORD.findall(sent)
                for n in range(2, 7):
                    for i in range(len(toks) - n + 1):
                        g = toks[i:i + n]
                        if g[0][:1].isupper() and g[-1][:1].isupper():   # "National Institute of ... Technology"
                            cum_hoa[" ".join(g).lower()] += 1
    # Ty le viet hoa chu dau cua moi tu don: ten rieng (Linux, Java) gan 1, thuat ngu thuong (deadlock) gan 0
    hoa = {}
    for w, c in nguyen.items():
        if w[:1].islower():
            cap = nguyen.get(w[:1].upper() + w[1:], 0)
            hoa[w] = round(cap / (cap + c), 2)
        elif w[:1].isupper() and not w.isupper() and w.lower() not in nguyen:
            hoa[w.lower()] = 1.0
    tong_cum = Counter()
    for c in dem.values():
        tong_cum.update({g: n for g, n in c.items() if " " in g})
    for g, n in cum_hoa.items():
        if g in tong_cum:
            hoa[g] = round(min(1.0, n / tong_cum[g]), 2)
    (CACHE / "viet_hoa.json").write_text(json.dumps(hoa, ensure_ascii=False), encoding="utf-8")
    return dem, tong_tu


def la_ung_vien(g: str, n: int, tong_tu: int, zipf) -> bool:
    words = g.split()
    if len(words) == 1:
        w = words[0]
        if w.isupper() and 2 <= len(w) <= 6:                # tu viet tat: TCP, SQL
            return True
        if not w.isalpha():
            return False
        z_chung = zipf(w, "en")
        z_sach = math.log10(n / tong_tu * 1e9)               # cung thang do Zipf: log10(so lan / ty tu)
        return z_chung < ZIPF_MAX and z_sach - z_chung >= ZIPF_GAP
    return not all(w.isdigit() for w in words)


def wiki_info(titles: list[str]) -> dict[str, dict]:
    """Ten -> {"wiki": ten bai (sau chuyen huong) hoac "", "vi": ten bai tieng Viet hoac ""}. Luu dan vao cache."""
    path = CACHE / "nguon" / "wiki_info.json"
    have = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    todo = [t for t in dict.fromkeys(titles) if t not in have]
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        ask = {t[:1].upper() + t[1:]: t for t in batch}
        r = _api("en.wikipedia.org", {"action": "query", "titles": "|".join(ask), "redirects": 1,
                                      "prop": "langlinks|pageprops", "lllang": "vi", "lllimit": "max",
                                      "ppprop": "disambiguation"})["query"]
        alias = {}
        for kind in ("normalized", "redirects"):
            for x in r.get(kind, []):
                alias[x["to"]] = alias.get(x["from"], x["from"])
        for p in r.get("pages", []):
            src = p["title"]
            while src in alias:
                src = alias[src]
            ok = not p.get("missing") and not p.get("invalid") and "disambiguation" not in p.get("pageprops", {})
            ll = p.get("langlinks") or []
            have[ask.get(src, src)] = {"wiki": p["title"] if ok else "", "vi": nfc(ll[0]["title"]) if ok and ll else ""}
        for t in batch:
            have.setdefault(t, {"wiki": "", "vi": ""})
        path.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"    wikipedia: {min(i + 50, len(todo))}/{len(todo)}", flush=True)
        time.sleep(2)
    return have


def _chuan(s: str) -> str:
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).lower().replace("-", " ")
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in s.split())


def khop_tieu_de(term: str, title: str) -> str | None:
    """Cum tu va ten bai Wikipedia khop the nao.

    'dung': cung ten. 'viet_tat': cum tu la chu viet tat cua ten bai (RBAC). 'chua': ten bai chua nguyen cum tu
    nhieu tu ("syntax tree" -> Abstract syntax tree, "congestion control" -> TCP congestion control): van dung chu de
    nhung la khai niem hep hon, nen KHONG lay ten bai tieng Viet. None: khac nghia (callee -> Telephone call).
    """
    if _chuan(term) == _chuan(title):
        return "dung"
    if len(term.split()) >= 2 and f" {_chuan(term)} " in f" {_chuan(title)} ":
        return "chua"
    # "congestion control" -> Network congestion: chung tu chinh. Van la thuat ngu, nhung bai noi khai niem khac
    # (rong hon), nen cung khong lay ten tieng Viet.
    chinh = lambda s: {w for w in _chuan(s).split() if len(w) >= 4 and w not in STOP}
    if len(term.split()) >= 2 and chinh(term) & chinh(title):
        return "chua"
    words = re.findall(r"[A-Za-z]+", re.sub(r"\s*\([^)]*\)\s*$", "", title))
    if term.isupper() and len(words) >= 2:
        initials = "".join(w[0] for w in words if w.lower() not in {"of", "and", "the", "for", "in", "on", "to"})
        if initials.upper() == term.upper():
            return "viet_tat"
    return None


def main() -> None:
    from wordfreq import zipf_frequency

    from terms.xay_dung.kho_en import SACH
    dem, tong_tu = dem_sach()
    chon: dict[str, str] = {}                               # cum tu -> sach dung nhieu nhat
    for sach, c in dem.items():
        top = [(g, n) for g, n in c.most_common()
               if n >= MIN_COUNT and la_ung_vien(g, n, tong_tu[sach], zipf_frequency)]
        for g, _ in top[:TOP_PER_BOOK]:
            chon.setdefault(g, sach)
        print(f"  {sach}: {len(top)} cum tu qua loc 1-2, lay {min(len(top), TOP_PER_BOOK)}", flush=True)
    info = wiki_info(list(chon))
    # Trang dinh huong, khong co bai, hoac chuyen huong sang bai khac ten ("Deadlock", "garbage collection" ->
    # Waste collection): thu ten co duoi linh vuc, vd "Deadlock (computer science)"
    can_thu = [g for g in chon if dem[chon[g]][g] >= 10
               and (not info[g]["wiki"] or khop_tieu_de(g, info[g]["wiki"]) != "dung")]
    thu_lai = {f"{g} ({duoi})": g for g in can_thu for duoi in DUOI_LINH_VUC}
    info2 = wiki_info(list(thu_lai))
    da_sua = set()
    for t, g in thu_lai.items():
        if g not in da_sua and info2[t]["wiki"] and khop_tieu_de(g, info2[t]["wiki"]) == "dung":
            info[g] = info2[t]
            da_sua.add(g)
    rows, loai = [], Counter()
    for g, sach in chon.items():
        w = info.get(g, {})
        kieu = khop_tieu_de(g, w["wiki"]) if w.get("wiki") else None
        loai[kieu or ("khac ten" if w.get("wiki") else "khong co bai")] += 1
        if not kieu:
            continue
        en, abbr = (re.sub(r"\s*\([^)]*\)\s*$", "", w["wiki"]).lower(), g) if kieu == "viet_tat" else (g, None)
        vi = "" if kieu == "chua" else re.sub(r"\s*\([^)]*\)\s*$", "", w.get("vi", ""))
        rows.append({"en": en, "abbr": abbr, "linh_vuc": SACH[sach][0], "wiki": w["wiki"], "vi": vi,
                     "dem": {s: dem[s][g] for s in dem if dem[s][g]}})
    out = CACHE / "ung_vien_sach.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Phan loai {len(chon)} cum tu: {dict(loai)}")
    print(f"Giu {len(rows)} cum tu, {sum(bool(r['vi']) for r in rows)} co ban tieng Viet -> {out}")


if __name__ == "__main__":
    main()
