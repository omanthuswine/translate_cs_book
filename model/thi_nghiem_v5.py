"""Thi nghiem 2: bang thuat ngu v5 va cac cai tien sau thi nghiem 1 (chu so huu: A).

Cung 270 doan, cung mo hinh (TranslateGemma 4B, nen 4-bit bitsandbytes, khong lay mau) nhu
model/notebooks/thi-nghiem-chen-thuat-ngu.ipynb, dung chung bo nho dem ban dich voi lan 1 (cau trung thi khong dich lai).

Nhanh:
- khong_chen:   dich thuong (moc).
- chen_ma_v4:   ket qua tot nhat lan 1: bang v4, moi cach viet qua ma giu cho (PROTECT_ALL_FORMS).
- v5:           bang v5 (terms/glossary_cs_vi_v5.csv): chen theo ngu canh, bot ma thua, + don ban dich.
- v5_bo_nghia:  nhu v5, nhung ma dung truoc danh tu ("the [T1] behavior") thi chen thang tieng Viet.
Moi nhanh deu cham hai kieu: chi dat lai ma, va dat lai ma + don ban dich (finalize day du).

Chay tren may co GPU NVIDIA (tu goc repo, da `hf auth login`):  python -m model.thi_nghiem_v5
Ket qua: out/thi_nghiem_v5/ (log.txt, thi_nghiem_v5.xlsx, ket_qua_moi.csv).
"""
from __future__ import annotations

import gc
import json
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "eval")]
import cham_thuat_ngu as C  # noqa: E402
import terms  # noqa: E402
import terms.core as TC  # noqa: E402

OUT = ROOT / "out" / "thi_nghiem_v5"
CACHE = ROOT / "out" / "thi_nghiem_chen" / "cache_dich.json"      # dung chung voi lan 1
V4, V5 = ROOT / "terms" / "glossary_cs_vi.csv", ROOT / "terms" / "glossary_cs_vi_v5.csv"
MODEL_ID, BATCH = "google/translategemma-4b-it", 4
NHANH = {"khong_chen": None, "chen_ma_v4": (V4, True, "ma"), "v5": (V5, True, "ma"),
         "v5_bo_nghia": (V5, True, "chen_thang")}

OUT.mkdir(parents=True, exist_ok=True)
_log = open(OUT / "log.txt", "a", encoding="utf-8")


def ghi(*a) -> None:
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    _log.write(s + "\n")
    _log.flush()


def chon_doan() -> pd.DataFrame:
    data = C.doc_bang(str(ROOT / "eval" / "data" / "so_sanh_ban_dich_danh_gia.xlsx"))
    seg = data[(data.loai_doan == "văn xuôi") & data.source.apply(lambda s: bool(C.tim_thuat_ngu(s)))]
    seg = seg.sort_values("id").reset_index(drop=True)
    seg["chuong"] = (seg.groupby("book").page.diff().fillna(99).abs() > 2).cumsum()
    return seg


def dau_vao(seg: pd.DataFrame) -> list[dict]:
    goc = (TC.GLOSSARY_PATH, TC.PROTECT_ALL_FORMS, TC.VI_TRI_BO_NGHIA)
    rows = []
    try:
        for name, cfg in NHANH.items():
            if cfg:
                TC.GLOSSARY_PATH, TC.PROTECT_ALL_FORMS, TC.VI_TRI_BO_NGHIA = cfg
            for _, g in seg.groupby("chuong", sort=True):
                st = terms.new_chapter()
                for r in g.itertuples():
                    if cfg is None:
                        info = {"placeholders": {}, "nguon": r.source,
                                "dau_muc": terms.prepare(r.source, terms.new_chapter())[1]["dau_muc"]}
                        rows.append({"nhanh": name, "id": r.id, "text_in": r.source, "info": info})
                    else:
                        text_in, info = terms.prepare(r.source, st)
                        rows.append({"nhanh": name, "id": r.id, "text_in": text_in, "info": info})
    finally:
        TC.GLOSSARY_PATH, TC.PROTECT_ALL_FORMS, TC.VI_TRI_BO_NGHIA = goc
    return rows


def dich(todo: list[str], cache: dict) -> None:
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    processor.tokenizer.padding_side = "left"
    model = AutoModelForImageTextToText.from_pretrained(MODEL_ID, device_map="auto", quantization_config=quant)
    model.eval()
    t0, n_tok = time.time(), 0
    try:
        for start in range(0, len(todo), BATCH):
            batch = todo[start:start + BATCH]
            prompts = [processor.apply_chat_template(
                [{"role": "user", "content": [{"type": "text", "source_lang_code": "en", "target_lang_code": "vi",
                                               "text": t}]}], tokenize=False, add_generation_prompt=True)
                for t in batch]
            enc = processor.tokenizer(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
            with torch.inference_mode():
                gen = model.generate(**enc, max_new_tokens=min(1024, int(enc["input_ids"].shape[1] * 2) + 64),
                                     do_sample=False)
            gen = gen[:, enc["input_ids"].shape[1]:]
            n_tok += int((gen != processor.tokenizer.pad_token_id).sum())
            for t, ids in zip(batch, gen):
                cache[t] = processor.tokenizer.decode(ids, skip_special_tokens=True).strip()
            done = start + len(batch)
            if (start // BATCH) % 10 == 0 or done == len(todo):
                CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
                ghi(f"  dich {done}/{len(todo)} cau, {(time.time() - t0) / 60:.1f} phut, "
                    f"{n_tok / (time.time() - t0):.1f} token/giay")
    finally:
        CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        del model
        gc.collect()
        torch.cuda.empty_cache()


def dat_lai(raw: str, info: dict) -> str:
    """Chi dat lai ma (ke ca bo chu lap), chua don ban dich."""
    for code, original in info.get("placeholders", {}).items():
        raw = TC._dat_lai(raw, code, original)
    return raw


def main() -> None:
    import re

    import sacrebleu

    seg = chon_doan()
    rows = dau_vao(seg)
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    todo = sorted({x["text_in"] for x in rows} - set(cache), key=len, reverse=True)
    ghi(f"{len(seg)} doan, {len(rows)} luot, {len(todo)} cau moi can dich (con lai da co trong bo nho dem)")
    if todo:
        dich(todo, cache)

    res = seg[["id", "book", "page", "chuong", "loai_doan", "source", "chatgpt"]].copy()
    ph = []
    for name in NHANH:
        by_id = {x["id"]: x for x in rows if x["nhanh"] == name}
        raw = res.id.map(lambda i: cache[by_id[i]["text_in"]])
        res[f"{name}_vao"] = res.id.map(lambda i: by_id[i]["text_in"])
        res[f"{name}_dat_lai"] = [dat_lai(r, by_id[i]["info"]) for r, i in zip(raw, res.id)]
        res[name] = [TC.don_ban_dich(o, by_id[i]["info"].get("nguon", ""), by_id[i]["info"].get("dau_muc", ""))
                     for o, i in zip(res[f"{name}_dat_lai"], res.id)]
        for i, x in by_id.items():
            for code, original in x["info"].get("placeholders", {}).items():
                ph.append({"nhanh": name, "id": i, "ma": code, "tu": original,
                           "con": bool(TC._placeholder_regex(code).search(cache[x["text_in"]]))})
    cols = [n for n in NHANH] + [f"{n}_dat_lai" for n in NHANH]
    tk = pd.concat([C.tong_ket(res, c) for c in cols + ["chatgpt"]], ignore_index=True)
    tk5 = pd.concat([C.tong_ket(res, c, C.THEO_DOI_V5) for c in list(NHANH) + ["chatgpt"]], ignore_index=True)

    def chrf(col):
        s = res.apply(lambda r: sacrebleu.sentence_chrf(str(r[col]), [str(r["chatgpt"])]).score, axis=1)
        return s.groupby(res.book).mean().round(1)

    chrf_tab = pd.DataFrame({c: chrf(c) for c in cols})
    loi = []                                            # loi mo hinh tu them, truoc va sau khi don
    for c in cols:
        loi.append({"cot": c,
                    "them_…": sum("…" in str(o) and "…" not in s and "..." not in s for o, s in zip(res[c], res.source)),
                    "them_html_md": sum(bool(re.search(r"<(sub|sup)>|\*\w", str(o))) and "<" not in s and "*" not in s
                                        for o, s in zip(res[c], res.source)),
                    "mat_so_thu_tu": sum(bool(re.match(r"\s*\d{1,2}[.)]\s", s)) and not re.match(r"\s*\d{1,2}[.)]", str(o))
                                         for o, s in zip(res[c], res.source))})
    loi = pd.DataFrame(loi)
    ph = pd.DataFrame(ph)
    giu_ma = ph.groupby("nhanh").con.agg(so_ma="count", giu=lambda s: round(s.mean() * 100, 1))

    with pd.ExcelWriter(OUT / "thi_nghiem_v5.xlsx", engine="openpyxl") as w:
        res.to_excel(w, sheet_name="so_sanh", index=False)
        tk.to_excel(w, sheet_name="tong_ket", index=False)
        tk5.to_excel(w, sheet_name="tong_ket_v5", index=False)
        chrf_tab.to_excel(w, sheet_name="chrF")
        loi.to_excel(w, sheet_name="loi_tu_them", index=False)
        giu_ma.to_excel(w, sheet_name="ma_giu_cho")
        ph.to_excel(w, sheet_name="ma_chi_tiet", index=False)
    pd.set_option("display.width", 220)
    ghi("\n=== Thuat ngu (cham nhu moc)\n" + tk[tk.bo != "tất cả"].to_string(index=False))
    ghi("\n=== Thuat ngu (cham theo bang v5)\n" + tk5.to_string(index=False))
    ghi("\n=== chrF so voi ChatGPT\n" + chrf_tab.to_string())
    ghi("\n=== Loi mo hinh tu them (so doan)\n" + loi.to_string(index=False))
    ghi("\n=== Ma giu cho duoc dat lai (%)\n" + giu_ma.to_string())

    lines = []
    n_v5 = len(TC.load_glossary(V5))
    for name, mo_ta in [("v5", f"bang v5 ({n_v5} muc): chen ma + ngu canh + bot ma thua + don ban dich"),
                        ("v5_bo_nghia", "nhu v5, ma o vi tri bo nghia thi chen thang tieng Viet")]:
        t = C.tong_ket(res, name).set_index("bo")
        lines.append([date.today().isoformat(), "TranslateGemma 4B", f"{len(res)} doan co thuat ngu (d2l + CLRS)",
                      "may ca nhan RTX 4050 Laptop GPU, nen 4-bit bitsandbytes, " + mo_ta,
                      chrf_tab[name].get("d2l-en", ""), chrf_tab[name].get("DSA", ""),
                      f'{t.loc["d2l", "sai_nghia"]}/{t.loc["d2l", "so_cap"]}',
                      f'{t.loc["dsa", "sai_tu_dong"]}/{t.loc["dsa", "so_cap"]}', f'{t.loc["tất cả", "nhat_quan"]:.0f}%', "",
                      f"cham tu dong eval/cham_thuat_ngu.py; chrF tinh tren 270 doan nay; ma giu cho dat lai "
                      f"{giu_ma.loc[name, 'giu']}%"])
    pd.DataFrame(lines).to_csv(OUT / "ket_qua_moi.csv", index=False, header=False)
    ghi("XONG ->", OUT)


if __name__ == "__main__":
    main()
