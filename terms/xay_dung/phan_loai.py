"""Xep nhom tung thuat ngu theo cach nguoi Viet that su viet (chu so huu: A).

Doc cache/thuat_ngu/dem_cach_dung.json (dem_cach_dung.py). Nguyen tac (do nhom chot, xem terms/xay_dung/README.md):

1. Cach dich tieng Viet phai lay tu NGUON UY TIN va DOI CHIEU NHIEU NGUON: chi dung khi co it nhat 2 ho nguon doc lap
   cung dung, trong do it nhat 1 ho hang 1 (bang v4, D2L ban nguoi dich, Machine Learning co ban, VNOI,
   bang thuat ngu Microsoft).
2. Ty le viet tieng Anh trong van ban ky thuat tieng Viet: duoi 20% -> dich; tu 80% -> giu tieng Anh;
   LUNG CHUNG -> "Anh (Việt)". Ap dung ca cho bang v4 ("ngăn xếp (stack)" -> "stack (ngăn xếp)").
3. Tu da nghia (cach viet tieng Viet la tu thong dung nhu "chú ý"; hoac tu tieng Anh don, thong dung) thi so dem
   khong noi duoc nghia nao, nen chen THEO NGU CANH (tu_dong = "ngữ cảnh", xem terms.core) thay vi luon/khong bao gio.
4. Muon doi quyet dinh cua bang v4 thi can do tin cay cao (du lieu nhieu, xa nguong, it nhat 2 nguon dong y).

Ket qua: cache/thuat_ngu/phan_loai.json
Chay (tu goc repo): python -m terms.xay_dung.phan_loai
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from wordfreq import zipf_frequency

from terms.xay_dung.dem_cach_dung import tach

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cache" / "thuat_ngu"

TRONG_SO = {"d2l": 1.0, "vnoi": 1.0, "mlcb": 1.0, "wiki": 0.5, "fineweb": 1.0}
TRAN = 200                 # moi nguon dong gop toi da 200 lan dem (sau trong so)
NGUONG = (0.2, 0.8)        # ty le viet tieng Anh: < 0.2 dich | < 0.8 Anh (Viet) | con lai giu tieng Anh
MIN_N = 8                  # it hon: thieu du lieu
SACH_DUNG_NHIEU = 20       # thieu du lieu tieng Viet nhung sach tieng Anh dung tu 20 lan: van giu (tin cay thap)
NGUONG_DOI_THUONG = 0.2    # muc doi thuong cua cach viet tieng Viet, xem muc_doi_thuong()
HANG_1 = {"v4", "d2l", "mlcb", "vnoi", "ms"}     # ms: bang thuat ngu Viet hoa cua Microsoft
_VH = CACHE / "viet_hoa.json"
VIET_HOA = json.loads(_VH.read_text(encoding="utf-8")) if _VH.exists() else {}   # tu -> ty le viet hoa trong sach


def ho_nguon(tag: str) -> str:
    """Nhan nguon -> ho nguon doc lap. Bang D2L va sach D2L cung mot nhom lam nen tinh la mot ho."""
    tag = tag.split(":", 1)[1] if tag.startswith(("ngoac:", "song_ngu:")) else tag
    return "wiki" if tag.startswith("wiki") else tag


def la_suy_ra(tag: str) -> bool:
    """Nhan nguon suy ra tu van ban (trich ngoac, gióng hàng), khong phai bang thuat ngu do nguoi soan."""
    return tag.startswith(("ngoac:", "song_ngu:"))


def loai_theo_ty_le(ty_le: float) -> str:
    return ("dịch", "Anh (Việt)", "giữ tiếng Anh")[sum(ty_le >= t for t in NGUONG)]


def _rut_gon(forms: dict[str, float]) -> dict[str, float]:
    """Bo cach viet DAI HON chua cach viet ngan ("sự quá khớp" da duoc dem trong "quá khớp") de khong dem hai lan."""
    tok = {f: tuple(tach(f)) for f in forms}
    keep = {}
    for f, c in forms.items():
        tf = " " + " ".join(tok[f]) + " "
        if not any(len(tok[g]) < len(tok[f]) and (" " + " ".join(tok[g]) + " ") in tf for g in forms):
            keep[f] = c
    return keep


def tru_nghia_thuong(r: dict, src: str, so_ky_tu: dict[str, int]) -> dict | None:
    """So dem trong ngu canh chuyen nganh cua nguon `src`, tru di so lan du kien gap theo nghia thuong.

    Chu tieng Anh trong van tieng Viet hau nhu luon mang nghia ky thuat; "chú ý", "mất mát" thi xuat hien day ca
    trong van doi thuong. Tru (so lan trong van thuong) x (do dai nguon / do dai van thuong).
    """
    d = r.get("dem", {}).get(src)
    if not d:
        return None
    chung = r.get("dem", {}).get("chung") or {}
    he_so = so_ky_tu[src] / so_ky_tu["chung"] if "chung" in so_ky_tu else 0
    tru = lambda c, c_chung: max(0.0, c - c_chung * he_so)
    return {"en": tru(d["en_nc"], chung.get("en_nc", 0)), "abbr": tru(d["abbr_nc"], chung.get("abbr_nc", 0)),
            "vi": {f: tru(c, chung.get("vi_nc", {}).get(f, 0)) for f, c in d["vi_nc"].items()}}


def muc_doi_thuong(r: dict, form: str, so_ky_tu: dict[str, int]) -> float | None:
    """Tan suat trong van thuong / tan suat trong van ky thuat. Do tren du lieu: thuat ngu that < 0.08
    (quá khớp 0.03, bảng băm 0, thuật toán 0.06); tu thong dung >= 0.3 (chú ý 1.31, mất mát 0.81, tinh chỉnh 0.30)."""
    chars_kt = sum(v for k, v in so_ky_tu.items() if k != "chung")
    kt = sum((r["dem"].get(s) or {}).get("vi", {}).get(form, 0) for s in so_ky_tu if s != "chung") / chars_kt
    thuong = (r["dem"].get("chung") or {}).get("vi", {}).get(form, 0) / so_ky_tu["chung"]
    return thuong / kt if kt else None


def tong_hop(r: dict, so_ky_tu: dict[str, int], trung: set[tuple]) -> dict:
    en = vi = abbr = 0.0
    forms: Counter = Counter()
    theo_nguon: dict[str, dict] = {}                  # nguon -> so dem da tru, de xet ho tro va dong y
    tung_nguon = {}                                   # nguon -> (so lan, loai)
    for src, w in TRONG_SO.items():
        d = tru_nghia_thuong(r, src, so_ky_tu)
        if not d:
            continue
        d["vi"] = {f: c for f, c in d["vi"].items() if tuple(tach(f)) not in trung}
        theo_nguon[src] = d
        e = d["en"] + d["abbr"]
        v = sum(_rut_gon(d["vi"]).values())
        if e + v:
            tung_nguon[src] = (e + v, loai_theo_ty_le(e / (e + v)))
        scale = min(1.0, TRAN / (w * (e + v))) * w if e + v else 0
        en += e * scale
        vi += v * scale
        abbr += d["abbr"] * scale
        for f, c in d["vi"].items():
            forms[f] += c * scale
    return {"en": en, "vi": vi, "abbr": abbr, "forms": forms, "theo_nguon": theo_nguon, "tung_nguon": tung_nguon}


def ung_cu_vien(r: dict, trung: set[tuple]) -> dict[str, list[str]]:
    """Cach dich ung vien -> nhan nguon. Bo cach trung chu tieng Anh/viet tat, va manh cat hut chi lay tu ngoac
    ma nam trong mot cach dich co trong bang ("tích chập" nam trong "mạng nơ-ron tích chập")."""
    chu = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    bien_the_en = {chu(r["en"])} | ({chu(r["abbr"])} if r["abbr"] else set())
    # Bo cach trung chu tieng Anh, ke ca bien the chi khac gach noi/dau cach ("back-end" cho "backend")
    # va chu viet tat ma bang thuat ngu ghi o cot tieng Viet ("GC", "FK", "ML" cua Microsoft): khong phai cach dich
    cands = {f: tags for f, tags in r["vi"].items()
             if tuple(tach(f)) not in trung and not (f.isascii() and chu(f) in bien_the_en)
             and not re.fullmatch(r"[A-Z0-9][A-Z0-9./+-]*", f)}
    bang = [" " + " ".join(tach(f)) + " " for f, tags in cands.items() if any(not la_suy_ra(t) for t in tags)]
    out = {}
    for f, tags in cands.items():
        chi_ngoac = all(la_suy_ra(t) for t in tags)
        tf = " " + " ".join(tach(f)) + " "
        if chi_ngoac and any(tf != b and tf in b for b in bang):
            continue
        out[f] = tags
    return out


def ung_ho(r: dict, form: str, tags: list[str]) -> tuple[list[str], list[str]]:
    """(ho nguon ung ho, ho nguon co bang chung ro rang).

    Bang chung ro rang: bang thuat ngu cua ho do ghi cach dich nay, hoac tac gia ho do tu chu thich trong ngoac.
    Ung ho them: van ban cua ho do dung cach dich nay CUNG BAI voi chu tieng Anh tu 2 lan tro len (vi_cb).
    """
    ro = {ho_nguon(t) for t in tags}
    them = {src for src in TRONG_SO if ((r["dem"].get(src) or {}).get("vi_cb", {}).get(form, 0) >= 2)}
    return sorted(ro | them), sorted(ro)


def chon_cach_viet(r: dict, s: dict, trung: set[tuple]) -> tuple[str | None, list[str], bool]:
    """(cach dich, cac ho nguon ung ho, du dieu kien doi chieu khong: >= 2 ho, trong do >= 1 ho hang 1)."""
    cands = ung_cu_vien(r, trung)
    if not cands:
        return None, [], False
    uh = {f: ung_ho(r, f, tags)[0] for f, tags in cands.items()}
    du = lambda f: len(uh[f]) >= 2 and bool(HANG_1 & set(uh[f]))
    best = max(uh, key=lambda f: (du(f), len(uh[f]), s["forms"].get(f, 0)))
    return best, uh[best], du(best)


def _tach_v4(cu: dict) -> tuple[str | None, str | None]:
    """(cach viet tieng Viet, viet tat) tu muc bang v4."""
    ngoai = re.sub(r"\s*\([^)]*\)\s*$", "", cu["lan_dau"]).strip()
    trong = re.search(r"\(([^()]+)\)\s*$", cu["lan_dau"])
    kind = cu["cach_xu_ly"]
    # "trọng số attention" (Anh (Việt) khong co ngoac): ca cum la cach viet cua v4
    vi = {"Anh (Việt)": trong.group(1) if trong else (None if cu["lan_dau"].isascii() else cu["lan_dau"]),
          "Việt (Anh)": ngoai, "dịch": ngoai, "giữ tiếng Anh": None}[kind]
    abbr = cu["lan_sau"] if kind == "Việt (Anh)" and cu["lan_sau"].isascii() and cu["lan_sau"] != ngoai else None
    return vi, abbr


def cach_viet(kind: str, en: str, vi: str | None, abbr: str | None) -> tuple[str, str]:
    if kind == "giữ tiếng Anh" or not vi:
        return en, en
    if kind == "Anh (Việt)":
        dau = abbr or en
        return f"{dau} ({vi})", dau
    if kind == "Việt (Anh)":
        return f"{vi} ({abbr or en})", abbr or vi
    return vi, vi


def xep(r: dict, v4: dict, so_ky_tu: dict[str, int]) -> dict:
    en, abbr = r["en"], r["abbr"]
    trung = {tuple(tach(en))} | ({tuple(tach(abbr))} if abbr else set())
    s = tong_hop(r, so_ky_tu, trung)
    n = s["en"] + s["vi"]
    vi, vi_ho, vi_du = chon_cach_viet(r, s, trung)
    cu = v4.get(en.lower())
    doi_thuong = muc_doi_thuong(r, vi, so_ky_tu) if vi else None
    mot_tu = len(en.split()) == 1
    # Tu tieng Anh don, thong dung (attention, loss, stack): mot chu, khong gach noi ("self-attention", "B-tree"
    # wordfreq tach thanh tu thuong), khong phai viet tat ("CNN" khong phai kenh tin tuc trong sach KHMT)
    tu_thuong_en = (mot_tu and "-" not in en and not en.isupper() and zipf_frequency(en, "en") >= 4.0)
    da_nghia = (doi_thuong is not None and doi_thuong >= NGUONG_DOI_THUONG) or tu_thuong_en
    out = {"en": en, "abbr": abbr, "linh_vuc": r["linh_vuc"], "nguon": r["nguon"], "v4": cu["cach_xu_ly"] if cu else None,
           "n": round(n, 1), "ty_le_en": round(s["en"] / n, 2) if n else None, "vi_de_xuat": vi, "vi_ung_ho": vi_ho,
           "vi_du_nguon": vi_du, "muc_doi_thuong": None if doi_thuong is None else round(doi_thuong, 2),
           "da_nghia": da_nghia}

    # 0. Loc thuat ngu MOI khong dang dua vao bang (bang v4 khong bi loc)
    if not cu:
        z = zipf_frequency(en, "en")
        sach = set(r.get("dem_en_sach", {}))
        if mot_tu and z >= 4.0:
            return {**out, "bo": "từ tiếng Anh thông dụng (user, error, message): mô hình tự dịch được"}
        if mot_tu and en.endswith("s") and zipf_frequency(en[:-1], "en") > z:
            return {**out, "bo": "dạng số nhiều lẻ (structures, attackers)"}
        if mot_tu and en.islower() and z == 0 and sach and sach <= {"ostep", "cybok"}:
            return {**out, "bo": "mảnh chữ PDF vỡ (cate, cally)"}
        if not mot_tu and VIET_HOA.get(en.lower(), 0) >= 0.7:
            return {**out, "bo": "tên riêng nhiều chữ (sách viết hoa từng chữ)"}

    # 1. Ket luan tu so lieu (neu do duoc)
    kind = tin_cay = None
    ly_do = []
    if n >= MIN_N and not (doi_thuong is not None and doi_thuong >= NGUONG_DOI_THUONG):
        ty_le = s["en"] / n
        kind = loai_theo_ty_le(ty_le)
        dong_y = [src for src, (m, k) in s["tung_nguon"].items() if m >= 10 and k == kind]
        margin = min(abs(ty_le - t) for t in NGUONG)
        tin_cay = "cao" if n >= 30 and margin >= 0.1 and len(dong_y) >= 2 and not tu_thuong_en else "vừa"
        ly_do.append(f"{ty_le:.0%} viết tiếng Anh, nguồn đồng ý: {', '.join(dong_y) or 'không có'}")
        if not vi_du:
            # Khong co cach dich tieng Viet dang tin de so: "100% viet tieng Anh" chi vi khong co gi khac de dem
            # ("personal information" -> nguoi Viet viet "thông tin cá nhân" nhung bang khong co cach dich do).
            tin_cay = "thấp"
            ly_do.append("chưa có cách dịch đủ 2 nguồn uy tín để so, chưa chứng minh được")
    elif n >= MIN_N:
        ly_do.append(f"'{vi}' cũng là từ thông dụng (mức đời thường {doi_thuong:.2f}), số đếm không tin được")
    else:
        ly_do.append("ít dữ liệu tiếng Việt")
    if tu_thuong_en:
        ly_do.append("từ tiếng Anh đơn, thông dụng")

    # 2. Quyet dinh cuoi
    if cu:
        vi_cu, abbr_cu = _tach_v4(cu)
        abbr = abbr or abbr_cu
        theo_chinh_sach = "Anh (Việt)" if cu["cach_xu_ly"] == "Việt (Anh)" else cu["cach_xu_ly"]
        if kind and tin_cay == "cao" and kind != theo_chinh_sach:
            final, quyet = kind, "đổi theo số liệu"
        else:
            final = theo_chinh_sach
            quyet = "giữ v4" + (" (Việt (Anh) -> Anh (Việt) theo nguyên tắc lưng chừng)" if final != cu["cach_xu_ly"] else "")
        # Cach dich: giu cua v4, tru khi cach moi co bang chung RO RANG tu >= 2 ho hang 1 (bang thuat ngu / tac gia tu
        # chu thich), cach cua v4 chi co toi da 1 ho ung ho, va hai cach khong phai cum nay nam trong cum kia.
        vi_dung = vi_cu
        if vi_cu and vi and vi != vi_cu and vi_du:
            ro_moi = set(ung_ho(r, vi, r["vi"].get(vi, []))[1]) & HANG_1
            uh_cu = ung_ho(r, vi_cu, r["vi"].get(vi_cu, []))[0]
            a, b = " " + " ".join(tach(vi)) + " ", " " + " ".join(tach(vi_cu)) + " "
            if len(ro_moi) >= 2 and len(uh_cu) <= 1 and a not in b and b not in a:
                vi_dung = vi
                ly_do.append(f"cách dịch đổi từ '{vi_cu}' (bằng chứng rõ: {', '.join(sorted(ro_moi))})")
            else:
                out["vi_goi_y"] = vi                              # ghi lai de nguoi doc bao cao can nhac
        elif not vi_cu:
            vi_dung = vi if vi_du else None
        tin_cay = tin_cay or "thấp"
    else:
        if kind and (kind == "giữ tiếng Anh" or vi_du):
            final, quyet = kind, "theo số liệu"
        elif vi and vi_du:                                          # da nghia hoac it du lieu: lung chung
            final, quyet, tin_cay = "Anh (Việt)", "lưng chừng: ghi cả hai", "thấp"
        elif sum(r.get("dem_en_sach", {}).values()) >= SACH_DUNG_NHIEU or kind:
            final, quyet, tin_cay = "giữ tiếng Anh", "chưa có cách dịch đủ nguồn, giữ tiếng Anh", "thấp"
        else:
            return {**out, "bo": "không phổ biến (thiếu dữ liệu)"}
        vi_dung = vi if vi_du else None
        if final == "giữ tiếng Anh" and mot_tu and VIET_HOA.get(en.lower(), 0) >= 0.6:
            return {**out, "bo": "tên riêng (sách hay viết hoa: Linux, Java), mô hình vốn để nguyên"}
    if final != "giữ tiếng Anh" and not vi_dung:
        final, tin_cay = "giữ tiếng Anh", "thấp"
        ly_do.append("không có cách dịch tiếng Việt dùng được")

    dung_viet_tat = bool(abbr) and (s["abbr"] >= 0.5 * max(s["en"] - s["abbr"], 1) or bool(cu and _tach_v4(cu)[1]))
    # Viet tat chiem uu the ma co cach dich: "LSTM (bộ nhớ ngắn hạn dài)", sau do "LSTM" (khong ghi ten dai tieng Anh)
    if dung_viet_tat and vi_dung and final == "giữ tiếng Anh":
        final = "Anh (Việt)"
        ly_do.append(f"chủ yếu viết tắt {abbr}")
    if cu and final == cu["cach_xu_ly"] and (final == "giữ tiếng Anh" or vi_dung == _tach_v4(cu)[0]):
        lan_dau, lan_sau = cu["lan_dau"], cu["lan_sau"]          # giu nguyen cach trinh bay cua v4 ("Transformer")
    else:
        lan_dau, lan_sau = cach_viet(final, en, vi_dung, abbr if dung_viet_tat else None)

    # 3. Co chen tu dong khong: "có" | "không" | "ngữ cảnh" (chi chen khi doan van dang noi ve chu de do)
    if cu and final in (cu["cach_xu_ly"], "Anh (Việt)") and quyet.startswith("giữ v4"):
        tu_dong = "có" if cu["tu_dong"] else "không"
        if not cu["tu_dong"] and final != "dịch":
            tu_dong = "ngữ cảnh"                                  # v4 de "không" vi da nghia: attention, kernel, loss
    elif tin_cay == "cao" and (vi_du or final == "giữ tiếng Anh") and (not mot_tu or zipf_frequency(en, "en") < 3.5):
        tu_dong = "có"
    else:
        tu_dong = "không"
    # Chen theo ngu canh khi CHU TIENG ANH da nghia (attention, loss, accuracy co nghia doi thuong); chu tieng Viet
    # thong dung ("học chủ động") chi lam so dem kem tin cay, khong lam "active learning" thanh da nghia trong sach.
    if tu_thuong_en and tu_dong == "có":
        tu_dong = "ngữ cảnh"
    # Ten rieng, viet tat, chu co so (SQL, NVIDIA, USB 3.0) mo hinh tu giu duoc: chen ma chi them rui ro roi ma
    if not cu and final == "giữ tiếng Anh" and (any(c.isdigit() for c in en) or en.isupper()
                                                or VIET_HOA.get(en.split()[0].lower(), 0) >= 0.5):
        tu_dong = "không"
    return {**out, "cach_xu_ly": final, "tin_cay": tin_cay, "quyet_dinh": quyet, "ly_do": "; ".join(ly_do),
            "vi": vi_dung, "lan_dau": lan_dau, "lan_sau": lan_sau, "tu_dong": tu_dong}


def main() -> None:
    import terms
    v4 = {t.source.lower(): {"cach_xu_ly": t.cach_xu_ly, "lan_dau": t.lan_dau, "lan_sau": t.lan_sau,
                             "tu_dong": t.tu_dong} for t in terms.load_glossary()}
    data = json.loads((CACHE / "dem_cach_dung.json").read_text(encoding="utf-8"))
    res = [xep(r, v4, data["so_ky_tu"]) for r in data["thuat_ngu"]]
    (CACHE / "phan_loai.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    giu = [x for x in res if "bo" not in x]
    print(f"{len(res)} thuat ngu: giu {len(giu)}, bo {len(res) - len(giu)}")
    print("  ly do bo:", dict(Counter(x["bo"] for x in res if "bo" in x)))
    print("  cach xu ly:", dict(Counter(x["cach_xu_ly"] for x in giu)))
    print("  do tin cay:", dict(Counter(x["tin_cay"] for x in giu)), "| tu_dong:", dict(Counter(x["tu_dong"] for x in giu)))
    tu_v4 = [x for x in giu if x["v4"]]
    print(f"  bang v4: {len(tu_v4)} muc, doi cach xu ly {sum(x['cach_xu_ly'] != x['v4'] for x in tu_v4)} "
          f"(trong do Việt (Anh) -> Anh (Việt): {sum(x['v4'] == 'Việt (Anh)' and x['cach_xu_ly'] == 'Anh (Việt)' for x in tu_v4)})")


if __name__ == "__main__":
    main()
