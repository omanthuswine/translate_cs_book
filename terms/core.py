"""Module thuat ngu (chu so huu: A).

B goi ba ham quanh moi lan dich mot doan van (chu ky ham giu nguyen, xem tests/test_contract.py):

    state = new_chapter()
    text_in, info = prepare(segment, state)
    text_out = finalize(model_output, info)

Voi moi thuat ngu tim thay trong doan van (chi xet tu co tu_dong = "có"):
- Chon cach viet: lan_dau neu thuat ngu chua gap trong chuong, nguoc lai lan_sau.
- Cach viet chi gom chu tieng Anh (Quicksort, RNN, "overfitting" o cac lan sau) phai giu nguyen,
  nen thay bang ma giu cho [T1], [T2]... de mo hinh khong dich mat; finalize dat lai.
- Cach viet co tieng Viet ("ngăn xếp (stack)", "overfitting (quá khớp)") thi chen thang vao cau,
  mo hinh dich phan con lai xung quanh.
Tu tu_dong = "không" (tu da nghia nhu kernel, bias, leaf) de nguyen cho mo hinh tu dich theo ngu canh.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

GLOSSARY_PATH = Path(__file__).with_name("glossary_cs_vi.csv")
GLOSSARY_COLUMNS = ("source", "cach_xu_ly", "lan_dau", "lan_sau", "linh_vuc", "tu_dong")

# Ma giu cho thay tu phai giu tieng Anh: [T1], [T2], ...
PLACEHOLDER = "[T{}]"


@dataclass(frozen=True)
class Term:
    source: str        # thuat ngu tieng Anh, vd "overfitting"
    cach_xu_ly: str    # "giữ tiếng Anh" | "Anh (Việt)" | "Việt (Anh)" | "dịch"
    lan_dau: str       # cach viet lan dau trong chuong, vd "overfitting (quá khớp)"
    lan_sau: str       # cach viet cac lan sau, vd "overfitting"
    linh_vuc: str
    tu_dong: bool      # False = tu da nghia, de mo hinh tu dich theo ngu canh


@dataclass
class ChapterState:
    """Trang thai cua mot chuong: nho thuat ngu nao da xuat hien de chi ghi ngoac o lan dau."""
    seen: set[str] = field(default_factory=set)


@lru_cache(maxsize=4)
def load_glossary(path: str | Path = GLOSSARY_PATH) -> tuple[Term, ...]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = set(GLOSSARY_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Bang thuat ngu thieu cot: {sorted(missing)}")
        return tuple(
            Term(r["source"], r["cach_xu_ly"], r["lan_dau"], r["lan_sau"], r["linh_vuc"], r["tu_dong"] == "có")
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
    inside = re.search(r"\(([^()]+)\)\s*$", term.lan_dau)
    if inside:
        names.add(inside.group(1))
    return frozenset(_norm(n) for n in names)


@lru_cache(maxsize=4)
def _matcher(path: str | Path = GLOSSARY_PATH) -> tuple[re.Pattern, tuple[Term, ...], tuple[frozenset[str], ...]]:
    """Mot regex cho ca bang, cum dai dung truoc de "batch size" thang "batch"."""
    terms = tuple(sorted((t for t in load_glossary(path) if t.tu_dong), key=lambda t: len(t.source), reverse=True))
    alternatives = "|".join(f"(?P<t{i}>{_term_pattern(t.source)})" for i, t in enumerate(terms))
    # Khong khop khi dinh lien chu, gach noi, dau cham (nn.Dropout, RNN-based) hoac la loi goi ham (softmax(x)).
    pattern = re.compile(rf"(?<![\w\-.])(?:{alternatives})(?![\w\-(]|\.\w)")
    return pattern, terms, tuple(_aliases(t) for t in terms)


_PAREN_AFTER = re.compile(r"\s*\(\s*([^()]{1,60}?)\s*\)")
_SENTENCE_END = re.compile(r"[.!?][\"'”’)\]]*\s+$")


def _at_sentence_start(before: str) -> bool:
    return not before.strip() or bool(_SENTENCE_END.search(before))


def _capitalize(text: str) -> str:
    return text[:1].upper() + text[1:]


def _must_stay_english(term: Term, text: str) -> bool:
    """Cach viet chi gom chu ASCII la tieng Anh can giu nguyen, nen dung ma giu cho."""
    return term.cach_xu_ly == "giữ tiếng Anh" or text.isascii()


def prepare(segment: str, state: ChapterState) -> tuple[str, dict]:
    """Truoc khi dua doan van cho mo hinh.

    Tra ve (van ban dua cho mo hinh, info). info gom:
    - "placeholders": {ma giu cho: cach viet dat lai}, finalize dung.
    - "terms": thuat ngu tim thay theo thu tu (cot source), de danh gia.
    """
    pattern, terms, aliases = _matcher()
    placeholders: dict[str, str] = {}
    found: list[str] = []
    pieces: list[str] = []
    pos, code_no = 0, 0

    while m := pattern.search(segment, pos):
        idx = int(m.lastgroup[1:])
        term = terms[idx]
        end = m.end()
        # "recurrent neural networks (RNNs)": ngoac sau la ten viet tat cua chinh thuat ngu -> bo,
        # vi cach viet ta chen da co ngoac rieng.
        paren = _PAREN_AFTER.match(segment, end)
        if paren and _norm(paren.group(1)) in aliases[idx]:
            end = paren.end()

        text = term.lan_sau if term.source in state.seen else term.lan_dau
        state.seen.add(term.source)
        found.append(term.source)

        if _must_stay_english(term, text):
            code_no += 1
            while PLACEHOLDER.format(code_no) in segment:   # tranh trung chu san co trong doan
                code_no += 1
            code = PLACEHOLDER.format(code_no)
            placeholders[code] = text
            text = code
        elif m.group()[0].isupper() and _at_sentence_start(segment[:m.start()]):
            text = _capitalize(text)

        pieces.append(segment[pos:m.start()])
        pieces.append(text)
        pos = end

    pieces.append(segment[pos:])
    return "".join(pieces), {"placeholders": placeholders, "terms": found}


# ---------------------------------------------------------------------------
# Sau khi dich
# ---------------------------------------------------------------------------

def _placeholder_regex(code: str) -> re.Pattern:
    """Khop ma giu cho ca khi mo hinh doi ngoac hoac them dau cach: "[T1]", "[ T1 ]", "(T1)", "【T1】"."""
    no = re.fullmatch(re.escape(PLACEHOLDER).replace(r"\{\}", r"(\d+)"), code).group(1)
    return re.compile(rf"[\[(【{{<⟦]\s*T\s*{no}\s*[\])】}}>⟧]", re.IGNORECASE)


def finalize(model_output: str, info: dict) -> str:
    """Sau khi mo hinh dich xong: dat lai cac tu duoc bao ve theo info["placeholders"].

    Tu dat lai o dau cau thi viet hoa chu dau (softmax -> Softmax).

    TODO (A, tuan 2): bo dau "…" mo hinh tu them, bo ky hieu markdown/HTML (*, <sub>),
    khoi phuc so thu tu dau muc.
    """
    text = model_output
    for code, original in info.get("placeholders", {}).items():
        def put_back(m: re.Match, original: str = original) -> str:
            return _capitalize(original) if _at_sentence_start(m.string[:m.start()]) else original
        text = _placeholder_regex(code).sub(put_back, text)
    return text
