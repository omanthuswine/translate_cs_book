"""Thi nghiem 3: dich lai doan bi roi ma giu cho (chu so huu: A).

Sau thi nghiem 2, gan het loi thuat ngu con lai la do mo hinh bo mat ma giu cho ("the [T1] behavior" -> "hanh vi").
Luc chay that biet duoc ma nao bi roi (khong thay [Tn] trong ban dich), nen co the dich lai rieng doan do.
Chi dung thong tin co luc chay, khong nhin ban dich mau.

Doan goc: nhanh v5 cua model/thi_nghiem_v5.py (bang v5, moi cach viet qua ma, ngu canh, bot ma thua).
Cach dich lai (chi cho doan co ma roi):
- chen_thang: ma bi roi thay bang chinh chu no dai dien ("the tiem can behavior"), ma khac giu nguyen.
- tach_cau:   tach doan thanh tung cau, dich tung cau (cau ngan it roi ma hon), ghep lai.
- chon:       trong ban goc / chen_thang / tach_cau, lay ban it cho hong nhat (ma roi + chu chen thang khong co
              trong ban dich); hoa thi giu ban goc.

Chay (tu goc repo, da `hf auth login`):  python -m model.thi_nghiem_thu_lai
Ket qua: out/thi_nghiem_thu_lai/ (log.txt, thi_nghiem_thu_lai.xlsx).
"""
from __future__ import annotations

import json
import re
import time

import pandas as pd

from model import thi_nghiem_v5 as T5

C, TC = T5.C, T5.TC
OUT = T5.ROOT / "out" / "thi_nghiem_thu_lai"
OUT.mkdir(parents=True, exist_ok=True)
_log = open(OUT / "log.txt", "a", encoding="utf-8")
CAU = re.compile(r"(?<=[.!?:])\s+(?=[A-Z\[(“\"])")


def ghi(*a) -> None:
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    _log.write(s + "\n")
    _log.flush()


def ma_roi(raw: str, info: dict) -> list[str]:
    return [c for c in info.get("placeholders", {}) if not TC._placeholder_regex(c).search(raw)]


def so_hong(raw: str, info: dict, chen: list[str]) -> int:
    """Cho hong: ma roi + chu da chen thang ma khong con trong ban dich."""
    low = raw.lower()
    return len(ma_roi(raw, info)) + sum(c.lower() not in low for c in chen)


def xong(raw: str, info: dict) -> str:
    return TC.don_ban_dich(T5.dat_lai(raw, info), info.get("nguon", ""), info.get("dau_muc", ""))


def main() -> None:
    import sacrebleu

    seg = T5.chon_doan()
    rows = {x["id"]: x for x in T5.dau_vao(seg) if x["nhanh"] == "v5"}
    cache = json.loads(T5.CACHE.read_text(encoding="utf-8"))
    thieu = sorted({x["text_in"] for x in rows.values()} - set(cache), key=len, reverse=True)
    if thieu:                                            # bang v5 doi sau lan chay truoc
        ghi(f"dich {len(thieu)} doan v5 chua co trong bo nho dem")
        T5.dich(thieu, cache)
    viec = {}
    for i, x in rows.items():
        roi = ma_roi(cache[x["text_in"]], x["info"])
        if not roi:
            continue
        ph = x["info"]["placeholders"]
        t1 = x["text_in"]
        for c in roi:
            t1 = t1.replace(c, ph[c])
        info1 = {**x["info"], "placeholders": {c: v for c, v in ph.items() if c not in roi}}
        cau = [c for c in CAU.split(x["text_in"]) if c.strip()]
        viec[i] = {"roi": roi, "t1": t1, "info1": info1, "chen": [ph[c] for c in roi], "cau": cau}
    can = {v["t1"] for v in viec.values()} | {c for v in viec.values() for c in v["cau"]}
    todo = sorted(can - set(cache), key=len, reverse=True)
    ghi(f"{len(rows)} doan, {len(viec)} doan co ma roi, {len(todo)} cau moi can dich")
    if todo:
        T5.dich(todo, cache)

    res = seg[["id", "book", "page", "chuong", "loai_doan", "source", "chatgpt"]].copy()
    cot = {k: [] for k in ["v5", "chen_thang", "tach_cau", "chon", "chon_tu"]}
    chi_tiet = []
    for i in res.id:
        x = rows[i]
        goc = cache[x["text_in"]]
        cot["v5"].append(xong(goc, x["info"]))
        if i not in viec:
            for k in ["chen_thang", "tach_cau", "chon"]:
                cot[k].append(cot["v5"][-1])
            cot["chon_tu"].append("")
            continue
        v = viec[i]
        r1 = cache[v["t1"]]
        r2 = " ".join(cache[c] for c in v["cau"])
        ung = [("goc", so_hong(goc, x["info"], []), xong(goc, x["info"])),
               ("chen_thang", so_hong(r1, v["info1"], v["chen"]), xong(r1, v["info1"])),
               ("tach_cau", so_hong(r2, x["info"], []), xong(r2, x["info"]))]
        cot["chen_thang"].append(ung[1][2])
        cot["tach_cau"].append(ung[2][2])
        best = min(ung, key=lambda u: u[1])                 # min giu thu tu: hoa thi lay ban goc
        cot["chon"].append(best[2])
        cot["chon_tu"].append(best[0])
        chi_tiet.append({"id": i, "ma_roi": " ".join(v["roi"]), "chu": " | ".join(v["chen"]),
                         "hong_goc": ung[0][1], "hong_chen_thang": ung[1][1], "hong_tach_cau": ung[2][1],
                         "chon": best[0], "so_cau": len(v["cau"])})
    for k, vals in cot.items():
        res[k] = vals

    bang = []
    for k in ["v5", "chen_thang", "tach_cau", "chon"]:
        t = C.tong_ket(res, k).set_index("bo")
        t5 = C.tong_ket(res, k, C.THEO_DOI_V5).set_index("bo")
        ch = res.apply(lambda r: sacrebleu.sentence_chrf(str(r[k]), [str(r["chatgpt"])]).score, axis=1)
        ch = ch.groupby(res.book).mean().round(1)
        bang.append({"cot": k, "CLRS_sai_moc": f'{t.loc["dsa", "sai_tu_dong"]}/{t.loc["dsa", "so_cap"]}',
                     "sai_v5": f'{t5.loc["tất cả", "sai_tu_dong"]}/{t5.loc["tất cả", "so_cap"]}',
                     "nhat_quan_v5": round(t5.loc["tất cả", "nhat_quan"], 1),
                     "chrF_d2l": ch.get("d2l-en"), "chrF_DSA": ch.get("DSA")})
    bang = pd.DataFrame(bang)
    chi_tiet = pd.DataFrame(chi_tiet)
    with pd.ExcelWriter(OUT / "thi_nghiem_thu_lai.xlsx", engine="openpyxl") as w:
        res.to_excel(w, sheet_name="so_sanh", index=False)
        bang.to_excel(w, sheet_name="tong_ket", index=False)
        chi_tiet.to_excel(w, sheet_name="doan_dich_lai", index=False)
    pd.set_option("display.width", 200)
    ghi("\n=== Ket qua (270 doan; doan khong roi ma giu ban v5)\n" + bang.to_string(index=False))
    ghi("\n=== Cho hong tren cac doan dich lai\n" + chi_tiet[["hong_goc", "hong_chen_thang", "hong_tach_cau"]]
        .sum().to_string() + "\nchon: " + chi_tiet.chon.value_counts().to_dict().__repr__())
    ghi("XONG ->", OUT)


if __name__ == "__main__":
    main()
