"""Gom thuat ngu ung vien (tieng Anh) va cach dich ung vien (tieng Viet) cho toan bo KHMT (chu so huu: A).

Nguon:
- Bang thuat ngu hien tai (terms/glossary_cs_vi.csv).
- Bang thuat ngu do nguoi soan cua nhom dich D2L tieng Viet (glossary.md, giong het o nhanh main va v0.15).
- Chi muc song ngu cua sach "Machine Learning cơ bản" (Vũ Hữu Tiệp), tac gia tu soan.
- Cac trang "Glossary of ..." cua Wikipedia tieng Anh theo tung linh vuc; cach dich ung vien lay tu ten bai
  Wikipedia tieng Viet tuong ung (langlinks).

Ket qua: cache/thuat_ngu/ung_vien.json, moi muc {"en", "abbr", "linh_vuc", "vi": {cach_viet: [nguon...]}, "nguon"}.

Chay (tu goc repo): python -m terms.xay_dung.ung_vien_en
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import terms

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cache" / "thuat_ngu"
UA = {"User-Agent": "cs-glossary-builder/0.1 (student project)"}

# Trang thuat ngu Wikipedia -> linh vuc ghi vao bang
TRANG = {
    "Glossary of computer science": "Khoa học máy tính",
    "Glossary of artificial intelligence": "Học máy",
    "Glossary of computer hardware terms": "Phần cứng",
    "Glossary of internet-related terms": "Mạng",
    "Glossary of computer graphics": "Đồ họa",
    "Glossary of Unified Modeling Language terms": "Công nghệ phần mềm",
    "Glossary of graph theory": "Đồ thị",
    "Glossary of machine vision": "Thị giác",
    "Glossary of probability and statistics": "Xác suất",
    "Glossary of linear algebra": "Toán",
}


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s).strip()


def _api(host: str, params: dict) -> dict:
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode({**params, "format": "json", "formatversion": 2})
    for lan in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception as err:                            # 429 (goi qua nhanh) hoac mang chap chon: cho roi thu lai
            if lan == 5:
                raise
            cho = 5 * 2 ** lan
            if isinstance(err, urllib.error.HTTPError) and err.headers.get("Retry-After", "").isdigit():
                cho = max(cho, int(err.headers["Retry-After"]))
            print(f"    API loi {err}, cho {cho}s roi thu lai", flush=True)
            time.sleep(cho)


def wikitext(title: str) -> str:
    path = CACHE / "nguon" / "wiki_glossary" / (re.sub(r"[^\w]+", "_", title) + ".txt")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_api("en.wikipedia.org", {"action": "parse", "page": title, "prop": "wikitext"})
                        ["parse"]["wikitext"], encoding="utf-8")
    return path.read_text(encoding="utf-8")


_TERM = re.compile(r"\{\{\s*term\s*\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}", re.I)
_BULLET = re.compile(r"^\*\s*(?:'''(.+?)'''|(\[\[[^\]]+\]\]))", re.M)   # trang ghi dang "* '''Term''' - ..."


def cac_muc(text: str) -> list[str]:
    found = _TERM.findall(text)
    return found or [a or b for a, b in _BULLET.findall(text)]
_LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")


def tach_term(raw: str) -> dict | None:
    """'[[abstract data type]] (ADT)' -> {"en": "abstract data type", "article": "abstract data type", "abbr": "ADT"}"""
    raw = re.sub(r"^\s*(?:term|1)\s*=\s*", "", raw.split("|content=")[0])
    raw = re.sub(r"\|\s*(?:id|multi|content)\s*=.*$", "", raw)
    m = _LINK.search(raw)
    article = m.group(1).strip() if m else None
    text = _LINK.sub(lambda x: x.group(2) or x.group(1), raw)
    text = re.sub(r"\{\{[^{}]*\}\}|'''?|<[^>]+>", "", text).split("|")[0]   # bo tham so template con sot
    abbr = None
    pm = re.search(r"\(([A-Z][A-Za-z0-9/&.-]{1,9})\)\s*$", text)
    if pm:
        # "Histogram (Color)": chu viet hoa thuong khong phai viet tat; viet tat phai co >= 2 chu hoa
        abbr = pm.group(1) if sum(c.isupper() for c in pm.group(1)) >= 2 else None
        text = text[:pm.start()]
    text = re.sub(r"\s*\([^)]*\)", "", text)              # "feature map (in CNN)" -> "feature map"
    text = re.sub(r"\s+", " ", text).strip(" ,;:")
    if not text or len(text) > 60 or not re.search(r"[A-Za-z]", text):
        return None
    return {"en": text, "article": article or text, "abbr": abbr}


def langlinks_vi(articles: list[str]) -> dict[str, str]:
    """Ten bai Wikipedia tieng Anh -> ten bai tieng Viet tuong ung (neu co)."""
    path = CACHE / "nguon" / "langlinks_vi.json"
    have = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    todo = [a for a in dict.fromkeys(articles) if a not in have]
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        r = _api("en.wikipedia.org", {"action": "query", "titles": "|".join(batch), "prop": "langlinks",
                                      "lllang": "vi", "redirects": 1, "lllimit": "max"})["query"]
        alias = {}                                          # ten da chuan hoa / chuyen huong -> ten goc
        for kind in ("normalized", "redirects"):
            for x in r.get(kind, []):
                alias[x["to"]] = alias.get(x["from"], x["from"])
        for p in r.get("pages", []):
            src = p["title"]
            while src in alias:
                src = alias[src]
            ll = p.get("langlinks") or []
            have[src] = nfc(ll[0]["title"]) if ll else ""
        for a in batch:
            have.setdefault(a, "")
        path.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8")   # luu dan
        print(f"    langlinks: {min(i + 50, len(todo))}/{len(todo)}", flush=True)
        time.sleep(2)
    return have


def bang_d2l() -> list[tuple[str, str]]:
    out = []
    for line in open(CACHE / "nguon" / "d2l-vi" / "glossary.md", encoding="utf-8"):
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m and not set(m.group(1)) <= set("-: ") and m.group(1).lower() != "english":
            out.append((nfc(m.group(1)), nfc(m.group(2))))
    return out


_CO_DAU = set("ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ")


def la_viet_tat_cua(abbr: str, en: str) -> bool:
    """Chu cai cua viet tat khop chu cai dau cac tu (bo tu chuc nang): RNN ~ recurrent neural network."""
    words = [w for w in re.split(r"[\s\-]+", en.lower()) if w and w not in {"of", "and", "the", "for", "in", "on", "to"}]
    letters = re.sub(r"[^a-z]", "", abbr.lower())
    return bool(words) and "".join(w[0] for w in words).startswith(letters[:len(words)]) and len(letters) <= len(words) + 1


def bang_mlcb() -> list[tuple[str, str]]:
    """Chi muc song ngu cua sach "Machine Learning cơ bản" (\\index{cực đại địa phương -- local maxima})."""
    out = []
    for p in sorted((CACHE / "nguon" / "ebookMLCB").rglob("*.tex")):
        for entry in re.findall(r"\\index\{([^{}]*--[^{}]*)\}", p.read_text(encoding="utf-8", errors="replace")):
            for part in entry.split("!"):                       # muc con: "K-means -- phân cụm!centroid -- tâm cụm"
                if "--" not in part:
                    continue
                if "\\" in part:                                # con lenh LaTeX (\ell_1): bo
                    continue
                # "die@điều kiện bậc hai": phan truoc @ la khoa sap xep cua makeindex
                a, b = (nfc(re.sub(r"\$([^$]*)\$", r"\1", x.split("@")[-1])).strip() for x in part.split("--", 1))
                viet = lambda s: any(c in _CO_DAU for c in s.lower())
                if viet(a) and not viet(b):
                    a, b = b, a                                 # dua ve (tieng Anh, tieng Viet)
                if a and b and not viet(a) and a.lower() != b.lower():
                    out.append((a, b[0].lower() + b[1:] if b[:1].isupper() and not b[:2].isupper() else b))
    return list(dict.fromkeys(out))


def bang_microsoft() -> list[tuple[str, str]]:
    """Bang thuat ngu Viet hoa cua Microsoft (Microsoft Terminology Collection, VIETNAMESE.tbx).

    Chi lay danh tu. Ten giao dien viet hoa tung chu ("Giao diện Người dùng Điện thoại") dua ve chu thuong,
    giu nguyen chu viet tat ("TCP/IP").
    """
    import xml.etree.ElementTree as ET

    path = CACHE / "nguon" / "microsoft" / "VIETNAMESE.tbx"
    if not path.exists():
        return []
    xml_ns = "{http://www.w3.org/XML/1998/namespace}lang"
    out = []
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag != "termEntry":
            continue
        en = vi = None
        for ls in el.findall("langSet"):
            tg = ls.find("ntig/termGrp")
            if tg is None:
                continue
            term = (tg.findtext("term") or "").strip()
            pos = next((n.text for n in tg.findall("termNote") if n.get("type") == "partOfSpeech"), "")
            if ls.get(xml_ns, "").startswith("en"):
                en = term if pos == "Noun" else None
            elif ls.get(xml_ns, "") == "vi":
                vi = term
        el.clear()
        if en and vi and len(en) <= 60 and en.lower() != vi.lower():
            vi = " ".join(w.lower() if w[:1].isupper() and w[1:].islower() else w for w in vi.split())
            out.append((nfc(en), nfc(vi)))
    return list(dict.fromkeys(out))


def gom() -> list[dict]:
    muc: dict[str, dict] = {}

    def them(en: str, vi: str | None, nguon: str, linh_vuc: str = "", abbr: str | None = None) -> None:
        # "natural language processing (NLP)" (bang D2L): bo ngoac, chu viet tat trong ngoac lam abbr
        m = re.search(r"\s*\(([^()]*)\)\s*$", en)
        if m:
            en = en[:m.start()].strip()
            # Chi la viet tat khi khop chu cai dau: "natural language processing (NLP)"; "subword (NLP)" la nhan linh vuc
            if m.group(1).isupper() and la_viet_tat_cua(m.group(1), en):
                abbr = abbr or m.group(1)
        if not en:
            return
        key = en.lower()
        m = muc.setdefault(key, {"en": en, "abbr": abbr, "linh_vuc": linh_vuc, "vi": {}, "nguon": []})
        m["abbr"] = m["abbr"] or abbr
        m["linh_vuc"] = m["linh_vuc"] or linh_vuc
        if nguon not in m["nguon"]:
            m["nguon"].append(nguon)
        if vi:
            m["vi"].setdefault(nfc(vi), [])
            if nguon not in m["vi"][nfc(vi)]:
                m["vi"][nfc(vi)].append(nguon)

    for t in terms.load_glossary():
        # Lay phan tieng Viet: "tập dữ liệu (dataset)" -> "tập dữ liệu"; "overfitting (quá khớp)" -> "quá khớp".
        ngoai = re.sub(r"\s*\([^)]*\)\s*$", "", t.lan_dau).strip()
        trong = re.search(r"\(([^()]+)\)\s*$", t.lan_dau)
        vi = {"Anh (Việt)": trong.group(1) if trong else None, "Việt (Anh)": ngoai,
              "dịch": ngoai, "giữ tiếng Anh": None}[t.cach_xu_ly]
        # Viet tat o lan sau ("mạng nơ-ron hồi tiếp (RNN)" -> lan sau "RNN") dem nhu cach viet tieng Anh
        abbr = t.lan_sau if t.lan_sau.isascii() and t.lan_sau.lower() != t.source.lower() and t.lan_sau.isupper() else None
        them(t.source, vi, "v4", t.linh_vuc, abbr)

    for en, vi in bang_d2l():
        for v in re.split(r"\s*(?:\(hoặc\s*|/|;)\s*", vi):     # "tích vô hướng (hoặc tích trong)"
            them(en, v.strip(" ()"), "d2l", "Học sâu")

    if (CACHE / "nguon" / "ebookMLCB").exists():
        for en, vi in bang_mlcb():
            them(en, vi, "mlcb", "Học máy")

    tu_wiki = []
    for title, linh_vuc in TRANG.items():
        found = [x for x in (tach_term(r) for r in cac_muc(wikitext(title))) if x]
        print(f"  {title}: {len(found)} muc", flush=True)
        tu_wiki += [(x, linh_vuc, title) for x in found]
    vi_of = langlinks_vi([x["article"] for x, _, _ in tu_wiki])
    for x, linh_vuc, title in tu_wiki:
        vi = vi_of.get(x["article"], "")
        vi = re.sub(r"\s*\([^)]*\)\s*$", "", vi)                 # "Đỉnh (lý thuyết đồ thị)" -> "Đỉnh"
        if vi and vi[0].isupper() and not vi[:2].isupper():
            vi = vi[0].lower() + vi[1:]
        them(x["en"], vi or None, "wiki:" + title.replace("Glossary of ", ""), linh_vuc, x["abbr"])
    return list(muc.values())


def them_microsoft(rows: list[dict], extra_keys: set[str] = frozenset()) -> int:
    """Gan cach dich cua Microsoft cho cac thuat ngu DA CO trong danh sach (khong them 15.000 muc giao dien phan mem).

    "hạt nhân, nhân" -> hai cach; "(việc) mật mã hóa" -> "mật mã hóa". Tra ve so thuat ngu duoc gan.
    """
    ms: dict[str, list[str]] = {}
    for en, vi in bang_microsoft():
        for v in re.split(r",\s*|;\s*", vi):
            v = re.sub(r"^\([^)]*\)\s*", "", v).strip()
            if v and v.lower() != en.lower():
                ms.setdefault(en.lower(), []).append(v)
    n = 0
    for r in rows:
        forms = ms.get(r["en"].lower())
        if not forms:
            continue
        n += 1
        for v in dict.fromkeys(forms):
            r["vi"].setdefault(v, [])
            if "ms" not in r["vi"][v]:
                r["vi"][v].append("ms")
        if "ms" not in r["nguon"]:
            r["nguon"].append("ms")
    return n


def main() -> None:
    rows = gom()
    out = CACHE / "ung_vien.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    co_vi = sum(1 for r in rows if r["vi"])
    print(f"{len(rows)} thuat ngu ung vien, {co_vi} co it nhat mot cach dich ung vien -> {out}")


if __name__ == "__main__":
    main()
