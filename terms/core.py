"""Module thuat ngu (chu so huu: A).

B goi ba ham quanh moi lan dich mot doan van (chu ky ham giu nguyen, xem tests/test_contract.py):

    state = new_chapter()
    text_in, info = prepare(segment, state)
    text_out = finalize(model_output, info)

Tuy chon, giua buoc dich va finalize: model_output, info = retry_lost_terms(model_output, info, translate_fn)
de dich lai doan bi mo hinh lam roi ma giu cho.

Voi moi thuat ngu tim thay trong doan van (cot tu_dong: "có" luon chen, "ngữ cảnh" chen khi doan van dang noi ve
mang cua thuat ngu, "không" de mo hinh tu dich):
- Chon cach viet: lan_dau neu thuat ngu chua gap trong chuong, nguoc lai lan_sau.
- Cach viet chi gom chu tieng Anh (Quicksort, RNN, "overfitting" o cac lan sau) phai giu nguyen,
  nen thay bang ma giu cho [T1], [T2]... de mo hinh khong dich mat; finalize dat lai.
- Cach viet co tieng Viet ("ngăn xếp (stack)", "overfitting (quá khớp)") cung qua ma giu cho (mac dinh,
  PROTECT_ALL_FORMS), hoac chen thang vao cau neu tat PROTECT_ALL_FORMS.
finalize con don ban dich: bo chu lap khi dat lai ("một mạng [T1]" -> "một mạng sâu"), bo "…" va the HTML/markdown
mo hinh tu them, tra lai so thu tu dau muc bi mat.
"""
from __future__ import annotations

import csv
import os
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

# Bang thuat ngu: mac dinh glossary_cs_vi.csv; bien moi truong DICH_SACH_GLOSSARY de thu bang khac (vd v5).
GLOSSARY_PATH = Path(os.environ.get("DICH_SACH_GLOSSARY") or Path(__file__).with_name("glossary_cs_vi.csv"))
GLOSSARY_COLUMNS = ("source", "cach_xu_ly", "lan_dau", "lan_sau", "linh_vuc", "tu_dong")

# Ma giu cho thay tu phai giu tieng Anh: [T1], [T2], ...
PLACEHOLDER = "[T{}]"
# True: moi cach viet trong bang, ca tieng Viet, deu thay bang ma giu cho (mo hinh khong viet lai duoc).
# Thi nghiem 21/11: sai thuat ngu CLRS 75% -> 11% (chen thang: 32%), xem eval/thi_nghiem_chen_thuat_ngu.md;
# thi nghiem 2 lap lai ket qua nay. False: cach viet co tieng Viet duoc chen thang vao cau.
PROTECT_ALL_FORMS = True
# Ma dung truoc mot danh tu ("the [T1] behavior") roi gap doi ma dung rieng (11% so voi 6%), vi tieng Viet phai
# dao trat tu. "chen_thang": o vi tri do chen thang tieng Viet thay vi ma. Dang thu nghiem.
VI_TRI_BO_NGHIA = "ma"
# Thuat ngu "ngữ cảnh" chi chen khi doan van co it nhat NGU_CANH_DOAN thuat ngu khac cung mang,
# hoac chuong dang doc da gap it nhat NGU_CANH_CHUONG lan thuat ngu cung mang.
NGU_CANH_DOAN = 2
NGU_CANH_CHUONG = 8

NHOM_LINH_VUC = {
    "Học máy": "ml", "Học sâu": "ml", "NLP": "ml", "Thị giác": "ml", "Học tăng cường": "ml", "Tối ưu": "ml",
    "Xác suất": "ml", "Thuật toán": "algo", "Cấu trúc dữ liệu": "algo", "Đồ thị": "algo", "Toán": "algo",
    "Hệ điều hành": "sys", "Hệ thống": "sys", "Phần cứng": "sys", "Mạng": "net", "Bảo mật": "sec",
    "Cơ sở dữ liệu": "db", "Lập trình": "prog", "Ngôn ngữ lập trình": "prog", "Công nghệ phần mềm": "prog",
    "Đồ họa": "gfx",
}


@dataclass(frozen=True)
class Term:
    source: str        # thuat ngu tieng Anh, vd "overfitting"
    cach_xu_ly: str    # "giữ tiếng Anh" | "Anh (Việt)" | "Việt (Anh)" | "dịch"
    lan_dau: str       # cach viet lan dau trong chuong, vd "overfitting (quá khớp)"
    lan_sau: str       # cach viet cac lan sau, vd "overfitting"
    linh_vuc: str
    tu_dong: bool      # True: luon chen. False: de mo hinh tu dich (tru khi ngu_canh)
    ngu_canh: bool = False   # True ("ngữ cảnh"): tu da nghia, chi chen khi doan van dang noi ve mang cua no


@dataclass
class ChapterState:
    """Trang thai cua mot chuong: thuat ngu da gap (chi ghi ngoac o lan dau) va so lan gap moi mang (chu de chuong)."""
    seen: set[str] = field(default_factory=set)
    nhom: Counter = field(default_factory=Counter)


def load_glossary(path: str | Path | None = None) -> tuple[Term, ...]:
    return _load(str(path or GLOSSARY_PATH))


@lru_cache(maxsize=4)
def _load(path: str) -> tuple[Term, ...]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = set(GLOSSARY_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Bang thuat ngu thieu cot: {sorted(missing)}")
        return tuple(
            Term(r["source"], r["cach_xu_ly"], r["lan_dau"], r["lan_sau"], r["linh_vuc"],
                 r["tu_dong"] == "có", r["tu_dong"] == "ngữ cảnh")
            for r in reader
        )


def new_chapter() -> ChapterState:
    return ChapterState()


# ---------------------------------------------------------------------------
# Tim thuat ngu trong cau tieng Anh
# ---------------------------------------------------------------------------

def _is_acronym(word: str) -> bool:
    """Tu co tu 2 chu hoa (GAN, ReLU, NP, KL) thi so khop dung hoa thuong, tranh dinh "np", "gan"."""
    return sum(c.isupper() for c in word) >= 2


def _escape(text: str) -> str:
    """re.escape, nhung dau nhay ' khop ca ' va ’ (Dijkstra's / Dijkstra’s)."""
    return "['’]".join(re.escape(part) for part in text.split("'"))


def _plural_forms(word: str) -> tuple[str, tuple[str, ...]]:
    """Tach tu cuoi cua thuat ngu thanh (goc, cac duoi) de khop ca so it va so nhieu."""
    if _is_acronym(word):
        return word, ("s", "")                           # GPU, GPUs
    lower = word.lower()
    for end, tails in (("ix", ("ices", "ixes", "ix")),   # matrix, matrices
                       ("ex", ("ices", "exes", "ex")),   # vertex, vertices
                       ("is", ("is", "es")),             # analysis, analyses
                       ("um", ("ums", "um", "a")),       # minimum, minima
                       ("us", ("uses", "ora", "us")),    # corpus, corpora
                       ("f", ("ves", "fs", "f"))):       # leaf, leaves
        if lower.endswith(end):
            return word[:-len(end)], tails
    if re.search(r"[^aeiou]y$", lower):
        return word[:-1], ("ies", "y")                   # query, queries
    if re.search(r"(s|x|z|ch|sh)$", lower):
        return word, ("es", "")                          # batch, batches
    return word, ("s", "")


def _term_pattern(source: str) -> str:
    """Mau regex cho mot thuat ngu.

    Cach chu bang dau cach khop mot hay nhieu dau cach/gach noi; cach bang gach noi khop
    gach noi, dau cach hoac viet lien (fine-tuning, fine tuning, finetuning).
    """
    tokens = re.split(r"(\s+|-)", source.strip())
    words, seps = tokens[0::2], tokens[1::2]
    parts = []
    for i, word in enumerate(words):
        if i == len(words) - 1:
            stem, tails = _plural_forms(word)
            pat = _escape(stem) + "(?:" + "|".join(re.escape(t) for t in tails) + ")"
        else:
            pat = _escape(word)
        parts.append(pat if _is_acronym(word) else f"(?i:{pat})")
        if i < len(seps):
            parts.append(r"[\s\-]?" if seps[i] == "-" else r"[\s\-]+")
    return "".join(parts)


def _norm(text: str) -> str:
    """Chuan hoa de so ten viet tat: "RNNs" ~ "RNN"."""
    return re.sub(r"(?<=\w)s$", "", text.strip().casefold())


def _aliases(term: Term) -> frozenset[str]:
    """Cac cach goi cung mot thuat ngu, de nhan ra ngoac giai thich san co: "recurrent neural networks (RNNs)"."""
    names = {term.source, term.lan_sau}
    for chunk in (term.lan_dau, term.lan_sau):
        inside = re.search(r"\(([^()]+)\)\s*$", chunk)
        if inside:
            names.add(inside.group(1))
    return frozenset(_norm(n) for n in names)


def _matcher(path: str | Path | None = None) -> tuple[re.Pattern, tuple[Term, ...], tuple[frozenset[str], ...]]:
    return _build_matcher(str(path or GLOSSARY_PATH))


@lru_cache(maxsize=4)
def _build_matcher(path: str) -> tuple[re.Pattern, tuple[Term, ...], tuple[frozenset[str], ...]]:
    """Mot regex cho ca bang, cum dai dung truoc de "batch size" thang "batch"."""
    terms = tuple(sorted((t for t in load_glossary(path) if t.tu_dong or t.ngu_canh),
                         key=lambda t: len(t.source), reverse=True))
    alternatives = "|".join(f"(?P<t{i}>{_term_pattern(t.source)})" for i, t in enumerate(terms))
    # Khong khop khi dinh lien chu, gach noi, dau cham (nn.Dropout, RNN-based) hoac la loi goi ham (softmax(x)).
    pattern = re.compile(rf"(?<![\w\-.])(?:{alternatives})(?![\w\-(]|\.\w)")
    return pattern, terms, tuple(_aliases(t) for t in terms)


_PAREN_AFTER = re.compile(r"\s*\(\s*([^()]{1,60}?)\s*\)")
_SENTENCE_END = re.compile(r"[.!?][\"'”’)\]]*\s+$")
_DAU_MUC = re.compile(r"\s*(\d{1,2}[.)]|\(\w{1,3}\)|[•▪◦–])\s+")
# Tu chuc nang tieng Anh: thuat ngu dung truoc mot tu KHAC nhom nay la dang bo nghia cho danh tu ("the X behavior")
_TU_CHUC_NANG_EN = set("""a an the and or but of to in on at by for with from into as is are was were be been being
this that these those it its which who whom whose what when where how than then so not can could may might must will
would should do does did has have had via per if while such also only very more most other each both all any""".split())


def _at_sentence_start(before: str) -> bool:
    return not before.strip() or bool(_SENTENCE_END.search(before))


def _capitalize(text: str) -> str:
    return text[:1].upper() + text[1:]


def _use_placeholder(term: Term, text: str) -> bool:
    """Cach viet chi gom chu ASCII la tieng Anh can giu nguyen, nen dung ma giu cho."""
    return PROTECT_ALL_FORMS or term.cach_xu_ly == "giữ tiếng Anh" or text.isascii()


def _bo_nghia(segment: str, end: int) -> bool:
    """Thuat ngu dung ngay truoc mot tu noi dung viet thuong ("the asymptotic behavior")."""
    m = re.match(r"\s+([a-z][a-z\-]*)", segment[end:])
    return bool(m) and m.group(1) not in _TU_CHUC_NANG_EN


def prepare(segment: str, state: ChapterState) -> tuple[str, dict]:
    """Truoc khi dua doan van cho mo hinh.

    Tra ve (van ban dua cho mo hinh, info). info gom:
    - "placeholders": {ma giu cho: cach viet dat lai}, finalize dung.
    - "terms": thuat ngu da chen theo thu tu (cot source), de danh gia.
    - "nguon": doan van goc, "dau_muc": so thu tu / dau dong o dau doan ("1.", "•"), de finalize don ban dich.
    - "text_in": van ban dua cho mo hinh, de retry_lost_terms dich lai khi can.
    """
    pattern, terms, aliases = _matcher()

    # Luot 1: tim cac lan xuat hien (ke ca ngoac viet tat san co phia sau)
    found = []
    pos = 0
    while m := pattern.search(segment, pos):
        idx = int(m.lastgroup[1:])
        end = m.end()
        # "recurrent neural networks (RNNs)": ngoac sau la ten viet tat cua chinh thuat ngu -> bo,
        # vi cach viet ta chen da co ngoac rieng.
        paren = _PAREN_AFTER.match(segment, end)
        if paren and _norm(paren.group(1)) in aliases[idx]:
            end = paren.end()
        found.append((m.start(), m.end(), end, terms[idx]))
        pos = end

    # Ngu canh: so thuat ngu khac nhau cua moi mang trong doan
    nhom_doan = Counter()
    for t in {t.source: t for *_, t in found}.values():
        nhom_doan[NHOM_LINH_VUC.get(t.linh_vuc, "khac")] += 1

    def du_ngu_canh(t: Term) -> bool:
        g = NHOM_LINH_VUC.get(t.linh_vuc, "khac")
        return nhom_doan[g] - 1 >= NGU_CANH_DOAN or state.nhom[g] >= NGU_CANH_CHUONG

    # Luot 2: thay the
    placeholders: dict[str, str] = {}
    chen: list[str] = []
    pieces: list[str] = []
    pos, code_no = 0, 0
    for start, m_end, end, term in found:
        if term.ngu_canh and not term.tu_dong and not du_ngu_canh(term):
            continue                                     # "pay attention to": de mo hinh dich thuong
        text = term.lan_sau if term.source in state.seen else term.lan_dau
        state.seen.add(term.source)
        state.nhom[NHOM_LINH_VUC.get(term.linh_vuc, "khac")] += 1
        chen.append(term.source)

        if _use_placeholder(term, text) and not (VI_TRI_BO_NGHIA == "chen_thang" and not text.isascii()
                                                 and _bo_nghia(segment, end)):
            code_no += 1
            while PLACEHOLDER.format(code_no) in segment:   # tranh trung chu san co trong doan
                code_no += 1
            code = PLACEHOLDER.format(code_no)
            placeholders[code] = text
            text = code
        elif segment[start].isupper() and _at_sentence_start(segment[:start]):
            text = _capitalize(text)

        pieces.append(segment[pos:start])
        pieces.append(text)
        pos = end

    pieces.append(segment[pos:])
    dau_muc = _DAU_MUC.match(segment)
    text_in = "".join(pieces)
    return text_in, {"placeholders": placeholders, "terms": chen, "nguon": segment,
                     "dau_muc": dau_muc.group(1) if dau_muc else "", "text_in": text_in}


# ---------------------------------------------------------------------------
# Sau khi dich
# ---------------------------------------------------------------------------

def _placeholder_regex(code: str) -> re.Pattern:
    """Khop ma giu cho ca khi mo hinh doi ngoac hoac them dau cach: "[T1]", "[ T1 ]", "(T1)", "【T1】"."""
    no = re.fullmatch(re.escape(PLACEHOLDER).replace(r"\{\}", r"(\d+)"), code).group(1)
    return re.compile(rf"[\[(【{{<⟦]\s*T\s*{no}\s*[\])】}}>⟧]", re.IGNORECASE)


def _dat_lai(text: str, code: str, original: str) -> str:
    """Dat lai mot ma giu cho. Bo chu lap: mo hinh tu them danh tu truoc ma ("một mạng [T1]" voi [T1] = "mạng sâu")."""
    first = original.split()
    out, pos = [], 0
    for m in _placeholder_regex(code).finditer(text):
        before = text[pos:m.start()]
        for k in (3, 2, 1):                              # tu cuoi phia truoc trung tu dau cua chu dat lai
            words = before.rstrip().split()
            if len(first) >= k and len(words) >= k and all(w.isalpha() for w in first[:k]) and \
                    [w.lower() for w in words[-k:]] == [w.lower() for w in first[:k]]:
                before = before.rstrip()[: -len(" ".join(words[-k:]))]
                before = before if before.endswith(" ") or not before else before + " "
                break
        rep = _capitalize(original) if _at_sentence_start("".join(out) + before) else original
        out += [before, rep]
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


# Cho tach cau khi dich lai: sau dau cham/hoi/than/hai cham, truoc chu hoa, ma giu cho, ngoac hoac ngoac kep.
_CAU = re.compile(r"(?<=[.!?:])\s+(?=[A-Z\[(“\"])")


def _ma_roi(model_output: str, info: dict) -> list[str]:
    """Ma giu cho khong con trong ban dich."""
    return [c for c in info.get("placeholders", {}) if not _placeholder_regex(c).search(model_output)]


def _so_cho_hong(model_output: str, info: dict, chen: list[str] = ()) -> int:
    """Ma giu cho bi roi + chu da chen thang ma khong con trong ban dich."""
    low = model_output.lower()
    return len(_ma_roi(model_output, info)) + sum(c.lower() not in low for c in chen)


def retry_lost_terms(model_output: str, info: dict, translate_fn: Callable[[str], str]) -> tuple[str, dict]:
    """Neu mo hinh lam roi ma giu cho thi dich lai doan; tra (ban dich, info) de dua vao finalize.

    Goi giua buoc dich va finalize, voi chinh ham dich da dung:
        out, info = retry_lost_terms(translate_fn(text_in), info, translate_fn)
        text_out = finalize(out, info)
    Khong roi ma thi tra nguyen, khong goi mo hinh. Roi ma thi:
    1. Ma bi roi thay bang chinh chu no dai dien ("the [T1] behavior" -> "the tiệm cận behavior"), dich lai.
    2. Neu van hong va doan co nhieu cau: dich tung cau roi ghep lai (cau ngan it roi ma hon).
    Lay ban it cho hong nhat; hoa thi giu ban dich truoc.
    Thi nghiem 21/11 (eval/thi_nghiem_v5_va_dich_lai.md): sai thuat ngu 25/428 -> 7/428, dich lai 48/270 doan.
    """
    text_in = info.get("text_in")
    roi = _ma_roi(model_output, info)
    if not roi or text_in is None:
        return model_output, info
    ph = info["placeholders"]
    chen = [ph[c] for c in roi]
    t1 = text_in
    for c in roi:
        t1 = t1.replace(c, ph[c])
    info1 = {**info, "placeholders": {c: v for c, v in ph.items() if c not in roi}, "text_in": t1}
    r1 = translate_fn(t1)
    ung = [(_so_cho_hong(model_output, info), model_output, info), (_so_cho_hong(r1, info1, chen), r1, info1)]
    cau = [c for c in _CAU.split(text_in) if c.strip()]
    if ung[1][0] > 0 and len(cau) > 1:
        r2 = " ".join(translate_fn(c) for c in cau)
        ung.append((_so_cho_hong(r2, info), r2, info))
    _, out, info_out = min(ung, key=lambda u: u[0])     # min lay muc dau tien khi hoa
    return out, info_out


def finalize(model_output: str, info: dict) -> str:
    """Sau khi mo hinh dich xong: dat lai cac tu duoc bao ve theo info["placeholders"], roi don ban dich.

    Tu dat lai o dau cau thi viet hoa chu dau (softmax -> Softmax). Don (chi khi doan goc khong co thu do):
    bo "…" mo hinh tu them, bo the HTML (<sup>8</sup>) va dau * in nghieng, tra lai so thu tu dau muc ("1.").
    """
    text = model_output
    for code, original in info.get("placeholders", {}).items():
        text = _dat_lai(text, code, original)
    return don_ban_dich(text, info.get("nguon", ""), info.get("dau_muc", ""))


def don_ban_dich(text: str, nguon: str, dau_muc: str = "") -> str:
    if nguon:                                           # chi don khi biet doan goc (info cu khong co thi bo qua)
        if "…" not in nguon and "..." not in nguon:
            text = re.sub(r"\s*(…|\.{3,})", "", text)
        if "<" not in nguon:
            text = re.sub(r"</?(?:sub|sup|b|i|em|strong|u|span|p)\b[^>]*>|<br\s*/?>", "", text)
        if "*" not in nguon:
            text = re.sub(r"(?<!\*)\*{1,3}([^*\n]+?)\*{1,3}(?!\*)", r"\1", text)
    if dau_muc and not re.match(r"\s*(\d{1,2}[.)]|\(\w{1,3}\)|[•▪◦–-])", text):
        text = f"{dau_muc} {text.lstrip()}"
    return re.sub(r"[ \t]{2,}", " ", text).strip()
