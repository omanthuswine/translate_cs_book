"""Dem cach nguoi Viet that su viet tung thuat ngu trong van ban ky thuat tieng Viet (chu so huu: A).

Voi moi thuat ngu ung vien va moi nguon (d2l, vnoi, wiki, fineweb), dem:
- en:    so lan viet tieng Anh (ca so nhieu)        - abbr: so lan viet ten viet tat (RNN, TCP)
- vi:    so lan viet bang tung cach dich ung vien    - en_vi: "overfitting (quá khớp)"   - vi_en: "quá khớp (overfitting)"
- docs:  so bai co nhac toi thuat ngu (bang bat ky cach viet nao)
- en_nc, abbr_nc, vi_nc: nhu tren nhung chi dem lan xuat hien trong ngu canh chuyen nganh (xem CUA_SO, NHOM)

Nguon "chung" (van ban doi thuong) chi dung de tru phan dung theo nghia thuong, xem phan_loai.tru_nghia_thuong.

Ket qua: cache/thuat_ngu/dem_cach_dung.json = {"so_ky_tu": {nguon: so ky tu}, "thuat_ngu": [...]}
Chay (tu goc repo): python -m terms.xay_dung.dem_cach_dung [--nguon d2l vnoi wiki fineweb chung]
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import time
import unicodedata
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cache" / "thuat_ngu"
MAX_LEN = 8
CUA_SO = 40         # ngu canh: so token hai ben mot lan xuat hien

# Nhom linh vuc de xet ngu canh. Mot lan xuat hien chi tinh "trong ngu canh chuyen nganh" neu trong CUA_SO token
# quanh no co mot thuat ngu khac cung nhom, hoac hai thuat ngu khac bat ky. Ap dung nhu nhau cho tieng Anh va tieng
# Viet. Vi du "tinh chỉnh" chi tinh khi gan do co "mô hình", "huấn luyện"... chu khong tinh "tinh chỉnh cài đặt".
from terms.core import NHOM_LINH_VUC as NHOM       # dung chung voi luc chen theo ngu canh khi dich
_TOK = re.compile(r"\w+(?:[-'’.+#]\w+)*\+*#?|[()]")   # giu "nơ-ron", "self-attention", "c++", "node.js"


_DAU_CU = {"oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa", "oè": "òe", "oé": "óe", "oẻ": "ỏe",
           "oẽ": "õe", "oẹ": "ọe", "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy"}
_DAU_CU_RE = re.compile(r"(?<!q)(o[àáảãạèéẻẽẹ]|u[ỳýỷỹỵ])(?![a-zàáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ])")


def chuan_dau(text: str) -> str:
    """Dua kieu dat dau cu ("khoá", "hoá", "thuý") ve kieu moi ("khóa", "hóa", "thúy") de dem chung."""
    return _DAU_CU_RE.sub(lambda m: _DAU_CU[m.group(1)], text)


def tach(text: str) -> list[str]:
    return _TOK.findall(chuan_dau(unicodedata.normalize("NFC", text).lower()))


def so_nhieu(words: list[str]) -> list[list[str]]:
    """'binary tree' -> ['binary tree', 'binary trees']; viet tat 'gpu' -> 'gpus'."""
    w = words[-1]
    tails = {w, w + "s"}
    if re.search(r"(s|x|z|ch|sh)$", w):
        tails.add(w + "es")
    if re.search(r"[^aeiou]y$", w):
        tails.add(w[:-1] + "ies")
    return [words[:-1] + [t] for t in sorted(tails)]


# --------------------------------------------------------------------------- danh sach ung vien

def _khoa(en: str) -> str:
    """Khoa gop: chu thuong, bo so nhieu don gian o tu cuoi."""
    words = en.lower().split()
    w = words[-1]
    if len(w) > 3 and w.endswith("ies"):
        w = w[:-3] + "y"
    elif len(w) > 3 and w.endswith("s") and not re.search(r"(ss|us|is)$", w):
        w = w[:-1]
    return " ".join(words[:-1] + [w])


def gop_ung_vien() -> list[dict]:
    """Gop ung_vien.json (bang v4, D2L, Wikipedia) va ung_vien_sach.json (tim tu sach)."""
    muc: dict[str, dict] = {}
    for r in json.loads((CACHE / "ung_vien.json").read_text(encoding="utf-8")):
        k = _khoa(r["en"])
        m = muc.setdefault(k, {"en": r["en"], "abbr": r["abbr"], "linh_vuc": r["linh_vuc"], "vi": {},
                                "nguon": [], "dem_en_sach": {}})
        m["abbr"] = m["abbr"] or r["abbr"]
        for v, src in r["vi"].items():
            m["vi"].setdefault(v, [])
            m["vi"][v] += [s for s in src if s not in m["vi"][v]]
        m["nguon"] += [s for s in r["nguon"] if s not in m["nguon"]]
    path = CACHE / "ung_vien_sach.json"
    for r in json.loads(path.read_text(encoding="utf-8")) if path.exists() else []:
        k = _khoa(r["en"])
        m = muc.setdefault(k, {"en": r["en"], "abbr": r.get("abbr"), "linh_vuc": r["linh_vuc"], "vi": {},
                                "nguon": [], "dem_en_sach": {}})
        m["abbr"] = m["abbr"] or r.get("abbr")
        for s, c in r["dem"].items():
            m["dem_en_sach"][s] = m["dem_en_sach"].get(s, 0) + c
        if "sach" not in m["nguon"]:
            m["nguon"].append("sach")
        if r["vi"]:
            m["vi"].setdefault(unicodedata.normalize("NFC", r["vi"]), []).append("wiki:langlink")
    from terms.xay_dung.ung_vien_en import them_microsoft
    n_ms = them_microsoft(list(muc.values()))
    print(f"  bang thuat ngu Microsoft: gan cach dich cho {n_ms} thuat ngu", flush=True)
    # Gióng hàng tren ban dich nguoi cua D2L (song_ngu_d2l.py): cach dich nguoi dich that su dung
    sn_path = CACHE / "song_ngu_d2l.json"
    for k, x in (json.loads(sn_path.read_text(encoding="utf-8")) if sn_path.exists() else {}).items():
        m = muc.get(_khoa(k))
        if not m:
            continue
        dung = [f for f, rate in x["vi"].items() if rate >= 0.3]
        if not dung:                                   # D2L khong dung cach dich nao co san: lay cum gióng hàng duoc
            dung = [g for g, dice, c in x["goi_y"] if dice >= 0.5 and c >= 3][:1]
        for f in dung:
            m["vi"].setdefault(unicodedata.normalize("NFC", f), [])
            if "song_ngu:d2l" not in m["vi"][f]:
                m["vi"][f].append("song_ngu:d2l")
    path = CACHE / "ngoac.json"                    # cach dich tac gia tu chu thich trong ngoac (lan dem truoc)
    for k, forms in (json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}).items():
        if k in muc:
            for form, _, kieu, src in forms:
                muc[k]["vi"].setdefault(unicodedata.normalize("NFC", form), [])
                tag = f"ngoac:{src}"
                if tag not in muc[k]["vi"][form]:
                    muc[k]["vi"][form].append(tag)
    rows = list(muc.values())
    for i, r in enumerate(rows):
        r["id"] = i
        r["vi"] = _gop_hoa_thuong(r["vi"])
    return rows


def _gop_hoa_thuong(vi: dict[str, list]) -> dict[str, list]:
    """"Học máy" (ten bai Wikipedia) va "học máy" la mot cach viet: gop lai, giu chu thuong dau."""
    out: dict[str, list] = {}
    by_key: dict[str, str] = {}
    for v, src in vi.items():
        if v[:1].isupper() and not v[:2].isupper():
            v = v[0].lower() + v[1:]
        k = " ".join(tach(v))
        v = by_key.setdefault(k, v)
        out.setdefault(v, [])
        out[v] += [s for s in src if s not in out[v]]
    return out


def chi_muc(rows: list[dict]) -> dict[tuple, list[tuple]]:
    """Cum token -> [(id thuat ngu, loai, cach viet)]. loai: en | abbr | vi."""
    idx: dict[tuple, list[tuple]] = defaultdict(list)
    for r in rows:
        en = tach(r["en"])
        if en:
            for f in so_nhieu(en):
                idx[tuple(f)].append((r["id"], "en", r["en"]))
        if r["abbr"]:
            for f in so_nhieu(tach(r["abbr"])):
                idx[tuple(f)].append((r["id"], "abbr", r["abbr"]))
        for v in r["vi"]:
            tv = tach(v)
            if tv and tv != en and len(tv) <= MAX_LEN:
                idx[tuple(tv)].append((r["id"], "vi", v))
    return idx


# --------------------------------------------------------------------------- dem song song

_IDX: dict = {}
_FIRST: dict = {}
_NHOM: list = []


def _init(idx: dict, nhom: list) -> None:
    global _IDX, _FIRST, _NHOM
    _IDX, _NHOM = idx, nhom
    _FIRST = defaultdict(set)
    for k in idx:
        _FIRST[k[0]].add(len(k))


def _co_ngu_canh(i: int, tid: int, moc: list[tuple[int, int]]) -> bool:
    """Trong CUA_SO token quanh vi tri i co thuat ngu khac cung nhom, hoac hai thuat ngu khac bat ky."""
    lo, hi = bisect.bisect_left(moc, (i - CUA_SO, -1)), bisect.bisect_right(moc, (i + CUA_SO, 10**9))
    khac = {t for _, t in moc[lo:hi] if t != tid}
    return len(khac) >= 2 or any(_NHOM[t] == _NHOM[tid] for t in khac)


def _dem_bai(text: str) -> dict:
    toks = tach(text)
    raw = []                                     # (bat dau, ket thuc, id, loai, cach viet)
    for i, t in enumerate(toks):
        for n in _FIRST.get(t, ()):
            for tid, loai, form in _IDX.get(tuple(toks[i:i + n]), ()):
                raw.append((i, i + n, tid, loai, form))
    # Chi tinh thuat ngu DAI NHAT o moi cho: "activation" nam trong "activation function" khong duoc dem rieng,
    # neu khong chu tieng Anh ngan bi dem du con cach dich tieng Viet thi khong ("giá trị kích hoạt").
    raw.sort(key=lambda m: (m[0], -m[1]))        # bat dau som truoc; cung cho bat dau thi cum dai truoc
    found = defaultdict(list)                    # vi tri bat dau -> [(ket thuc, id, loai, cach viet)]
    xa_nhat, span_truoc = -1, None               # diem ket thuc xa nhat cua cac cum (khac cho) da gap
    for s0, e0, tid, loai, form in raw:
        if (s0, e0) != span_truoc:               # sang mot cho moi
            if span_truoc is not None:
                xa_nhat = max(xa_nhat, span_truoc[1])
            span_truoc = (s0, e0)
        if xa_nhat >= e0:                        # mot cum truoc do (bat dau som hon hoac dai hon) da phu cho nay
            continue
        found[s0].append((e0, tid, loai, form))
    # Moc ngu canh: thuat ngu tieng Anh hoac cach viet tieng Viet tu hai tieng tro len (bo "cây", "lớp", "luồng"...)
    moc = sorted((i, tid) for i, ms in found.items() for end, tid, loai, _ in ms if loai != "vi" or end - i >= 2)
    out = defaultdict(lambda: {"en": 0, "abbr": 0, "vi": defaultdict(int), "en_vi": 0, "vi_en": 0,
                               "en_nc": 0, "abbr_nc": 0, "vi_nc": defaultdict(int)})
    for i, ms in found.items():
        for end, tid, loai, form in ms:
            o = out[tid]
            nc = _co_ngu_canh(i, tid, moc)
            if loai == "vi":
                o["vi"][form] += 1
                o["vi_nc"][form] += nc
            else:
                o[loai] += 1
                o[loai + "_nc"] += nc
            if end < len(toks) and toks[end] == "(":                     # "X ( Y )"
                for end2, tid2, loai2, _ in found.get(end + 1, ()):
                    if tid2 == tid and end2 < len(toks) and toks[end2] == ")" and (loai == "vi") != (loai2 == "vi"):
                        o["vi_en" if loai == "vi" else "en_vi"] += 1
            if loai != "vi":
                _ghi_ngoac(toks, i, end, o)
    # vi_cb: cach dich xuat hien CUNG BAI voi chu tieng Anh (hoac viet tat) cua chinh thuat ngu do: bang chung
    # tac gia dung cach dich nay cho khai niem nay, chu khong phai mot cum tu thong dung trung chu.
    return {tid: {"en": o["en"], "abbr": o["abbr"], "vi": dict(o["vi"]), "en_vi": o["en_vi"], "vi_en": o["vi_en"],
                  "en_nc": o["en_nc"], "abbr_nc": o["abbr_nc"], "vi_nc": dict(o["vi_nc"]),
                  "vi_cb": dict(o["vi"]) if o["en"] + o["abbr"] else {},
                  "truoc": dict(o.get("truoc", {})), "trong": dict(o.get("trong", {}))}
            for tid, o in out.items()}


def _ghi_ngoac(toks: list[str], i: int, end: int, o: dict) -> None:
    """Tac gia tu chu thich: "bảng băm (hash table)" hoac "deadlock (bế tắc)". Ghi lai phan tieng Viet canh do.

    truoc: cac duoi 1-6 token dung ngay truoc "( EN )"; trong: noi dung trong "EN ( ... )". Chon ranh gioi cum
    tu sau khi gop ca kho (chon_ngoac).
    """
    if i >= 1 and toks[i - 1] == "(" and end < len(toks) and toks[end] == ")":
        truoc = []
        for t in reversed(toks[max(0, i - 7):i - 1]):
            if t in "()" or not any(c.isalpha() for c in t):
                break
            truoc.insert(0, t)
            key = " ".join(truoc)
            o.setdefault("truoc", {})
            o["truoc"][key] = o["truoc"].get(key, 0) + 1
    if end < len(toks) and toks[end] == "(":
        try:
            close = toks.index(")", end + 1, min(len(toks), end + 10))
        except ValueError:
            return
        inside = toks[end + 1:close]
        if inside and all(any(c.isalpha() for c in t) for t in inside):
            key = " ".join(inside)
            o.setdefault("trong", {})
            o["trong"][key] = o["trong"].get(key, 0) + 1


def dem_nguon(nguon: str, idx: dict, nhom: list, procs: int = 8) -> tuple[dict[int, dict], int]:
    """(so dem moi thuat ngu, tong so ky tu cua nguon)."""
    path = CACHE / "kho" / f"{nguon}.jsonl"
    so_ky_tu = [0]

    def texts():
        for line in open(path, encoding="utf-8"):
            t = json.loads(line)["text"]
            so_ky_tu[0] += len(t)
            yield t

    tong: dict[int, dict] = {}
    t0, n = time.time(), 0
    with Pool(procs, initializer=_init, initargs=(idx, nhom)) as pool:
        for res in pool.imap_unordered(_dem_bai, texts(), chunksize=64):
            n += 1
            for tid, o in res.items():
                t = tong.setdefault(tid, {"en": 0, "abbr": 0, "vi": defaultdict(int), "en_vi": 0, "vi_en": 0,
                                          "en_nc": 0, "abbr_nc": 0, "vi_nc": defaultdict(int), "docs": 0,
                                          "vi_cb": defaultdict(int), "truoc": defaultdict(int),
                                          "trong": defaultdict(int)})
                t["docs"] += 1
                for k in ("en", "abbr", "en_vi", "vi_en", "en_nc", "abbr_nc"):
                    t[k] += o[k]
                for key in DICT_KEYS:
                    for f, c in o[key].items():
                        t[key][f] += c
    print(f"  {nguon}: {n} bai, {len(tong)} thuat ngu co mat, {(time.time() - t0) / 60:.1f} phut", flush=True)
    for t in tong.values():
        for key in DICT_KEYS:
            t[key] = dict(t[key])
    return tong, so_ky_tu[0]


DICT_KEYS = ("vi", "vi_nc", "vi_cb", "truoc", "trong")


# Tu chuc nang tieng Viet: cum tu dich khong bat dau bang cac tu nay ("các bảng băm" -> "bảng băm")
TU_CHUC_NANG = set("""các những một là và của cho với trong này đó được có để bằng khi thì như về theo ta chúng họ
nó sẽ đã đang cũng rất nhiều mỗi từ gọi hay hoặc còn vì nên nếu mà ra vào lên sau trước giữa trên dưới bởi tại
đây ấy kia cái con việc sự""".split())


def chon_ngoac(truoc: dict[str, int], trong: dict[str, int], min_lan: int = 2) -> list[tuple[str, int, str]]:
    """Tu cac lan "X (EN)" va "EN (X)" trong kho, chon cum tieng Viet X. Tra ve [(cum tu, so lan, kieu)].

    "trong": lay nguyen noi dung ngoac pho bien nhat. "truoc": bat dau tu tu cuoi pho bien nhat roi noi dan
    sang trai, chi noi khi cum dai hon van giu duoc it nhat 60% so lan (gap ranh gioi cum tu thi dung).
    """
    out = []
    trong = {f: c for f, c in trong.items() if la_cum_viet(f)}
    if trong:
        f, c = max(trong.items(), key=lambda x: x[1])
        if c >= min_lan and f.split()[0] not in TU_CHUC_NANG:
            out.append((f, c, "trong"))
    by_len = defaultdict(dict)
    for f, c in truoc.items():
        by_len[len(f.split())][f] = c
    if by_len.get(1):
        best, c = max(by_len[1].items(), key=lambda x: x[1])
        k = 1
        while by_len.get(k + 1):
            ext = {f: n for f, n in by_len[k + 1].items() if f.endswith(" " + best)}
            if not ext:
                break
            f2, c2 = max(ext.items(), key=lambda x: x[1])
            if c2 < 0.6 * c:
                break
            best, c, k = f2, c2, k + 1
        while best.split() and best.split()[0] in TU_CHUC_NANG:      # bo tu chuc nang o dau
            best = " ".join(best.split()[1:])
        if best and c >= min_lan and la_cum_viet(best):
            out.append((best, c, "truoc"))
    return out


_CO_DAU = set("ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ")


def la_cum_viet(f: str) -> bool:
    """Cum tieng Viet dung lam cach dich: tu 2 chu tro len, moi chu toi thieu 2 ky tu chi gom chu cai, co dau tieng
    Viet. Loai bien toan hoc va rac trong ngoac: "f_1", "i j", "e", "dtp"; loai manh cat hut mot chu: "trình"."""
    words = f.split()
    return (len(words) >= 2 and all(len(w) >= 2 and w.replace("-", "").isalpha() for w in words)
            and any(c in _CO_DAU for c in f))


def main() -> None:
    ap = argparse.ArgumentParser()
    # "chung" = van ban doi thuong, chi dung de tru phan dung theo nghia thuong (xem phan_loai.py)
    ap.add_argument("--nguon", nargs="+", default=["d2l", "vnoi", "mlcb", "wiki", "fineweb", "chung"])
    args = ap.parse_args()
    rows = gop_ung_vien()
    idx = chi_muc(rows)
    nhom = [NHOM.get(r["linh_vuc"], "khac") for r in rows]          # chi so = id thuat ngu
    print(f"{len(rows)} thuat ngu, {len(idx)} cach viet can dem", flush=True)
    so_ky_tu = {}
    for nguon in args.nguon:
        if not (CACHE / "kho" / f"{nguon}.jsonl").exists():
            print(f"  {nguon}: chua co, bo qua")
            continue
        tong, so_ky_tu[nguon] = dem_nguon(nguon, idx, nhom)
        for r in rows:
            r.setdefault("dem", {})[nguon] = tong.get(r["id"], {})
    out = CACHE / "dem_cach_dung.json"
    out.write_text(json.dumps({"so_ky_tu": so_ky_tu, "thuat_ngu": rows}, ensure_ascii=False, indent=0),
                   encoding="utf-8")
    print("->", out)
    # Cach dich tac gia tu chu thich trong ngoac: luu lai, lan chay sau dua vao lam cach dich ung vien va dem
    ngoac = {}
    for r in rows:
        for src in so_ky_tu:
            if src == "chung":
                continue
            d = r["dem"].get(src) or {}
            for form, c, kieu in chon_ngoac(d.get("truoc", {}), d.get("trong", {})):
                ngoac.setdefault(_khoa(r["en"]), []).append((form, c, kieu, src))
    (CACHE / "ngoac.json").write_text(json.dumps(ngoac, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"  cach dich trong ngoac: {len(ngoac)} thuat ngu -> {CACHE / 'ngoac.json'}")


if __name__ == "__main__":
    main()
