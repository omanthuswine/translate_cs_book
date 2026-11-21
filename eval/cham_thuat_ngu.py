"""Cham thuat ngu tren bo thu (chu so huu: A).

Cach dem giong bang `tong_hop` trong so_sanh_ban_dich_danh_gia.xlsx (da doi chieu lai, xem eval/README.md):
- Chi xet doan "văn xuôi". Moi cap (doan, thuat ngu theo doi) tinh mot lan, khop "term(s|es)" khong phan biet hoa thuong.
- Ban dich cua cap do duoc xep vao bien the dau tien (theo thu tu ben duoi) co mat trong ban dich,
  khong co bien the nao thi la "(khác/bỏ sót)".
- Chia hai bo theo nhom thuat ngu (khong theo sach): "dsa" la 6 thuat ngu thuat toan, "d2l" la 14 tu con lai.
- nhat_quan = tong (so lan cua bien the pho bien nhat moi thuat ngu) / tong so cap.

Moi bien the thuoc mot loai:
- "bảng": dung cach viet trong bang thuat ngu
- "đúng": dung nghia, khac cach viet
- "sai":  sai nghia (vd recurrent -> "hồi quy", recurrence -> "đệ quy")

Chay:  python eval/cham_thuat_ngu.py eval/data/so_sanh_ban_dich_danh_gia.xlsx tg_4b tg_12b chatgpt
"""
from __future__ import annotations

import re
import sys
from collections import Counter

import pandas as pd

KHAC = "(khác/bỏ sót)"

# 20 thuat ngu theo doi cua moc xuat phat. Thu tu bien the = thu tu uu tien khi ban dich co nhieu bien the.
THEO_DOI: dict[str, list[tuple[str, str]]] = {
    "hidden layer": [("lớp ẩn", "bảng"), ("tầng ẩn", "đúng")],
    "hidden state": [("trạng thái ẩn", "bảng")],
    "hidden unit": [("đơn vị ẩn", "bảng"), ("nút ẩn", "đúng")],
    "time step": [("bước thời gian", "bảng"), ("thời điểm", "đúng")],
    "dropout": [("dropout", "bảng")],
    "backpropagation": [("lan truyền ngược", "bảng"), ("truyền ngược", "đúng"), ("backpropagation", "đúng")],
    "activation function": [("hàm kích hoạt", "bảng")],
    "regularization": [("điều chuẩn", "bảng"), ("chính quy hóa", "đúng"), ("chuẩn hóa", "sai"),
                       ("regularization", "bảng")],
    "generalization": [("khái quát hóa", "bảng"), ("tổng quát hóa", "đúng"), ("khái quát", "đúng")],
    "label": [("nhãn", "bảng")],
    "feature": [("đặc trưng", "bảng"), ("đặc điểm", "đúng"), ("tính năng", "đúng")],
    "dataset": [("tập dữ liệu", "bảng"), ("bộ dữ liệu", "đúng"), ("dataset", "đúng")],
    # "rnn": bang thuat ngu viet "recurrent neural network" cac lan sau la "RNN"
    "recurrent": [("hồi tiếp", "bảng"), ("hồi quy", "sai"), ("lặp", "đúng"), ("recurrent", "đúng"),
                  ("tái phát", "sai"), ("rnn", "bảng")],
    "recurrence": [("truy hồi", "bảng"), ("đệ quy", "sai")],
    "recursion tree": [("cây đệ quy", "bảng")],
    "master method": [("phương pháp master", "bảng"), ("phương pháp chính", "sai"),
                      ("phương pháp tổng quát", "sai")],
    "subproblem": [("bài toán con", "bảng")],
    "asymptotic": [("tiệm cận", "bảng"), ("asymptotic", "đúng")],
    "running time": [("thời gian chạy", "bảng"), ("thời gian thực thi", "đúng"), ("thời gian thực hiện", "đúng")],
    "minibatch": [("minibatch", "bảng"), ("mini-batch", "đúng"), ("lô nhỏ", "đúng"), ("lô dữ liệu nhỏ", "đúng")],
}
BO_DSA = {"recurrence", "recursion tree", "master method", "subproblem", "asymptotic", "running time"}

# Cham theo bang v5: cac tu v5 xep "Anh (Việt)" thi lan dau "hidden state (trạng thái ẩn)", cac lan sau "hidden state".
# Chu tieng Anh la cach viet cua bang, dat len dau de lan dau (co ca hai) va cac lan sau cung mot bien the.
_ANH_VIET_V5 = ("hidden state", "backpropagation", "activation function", "regularization", "dataset")
THEO_DOI_V5 = {t: ([(t, "bảng")] + [v for v in vs if v[0] != t]) if t in _ANH_VIET_V5 else vs
               for t, vs in THEO_DOI.items()}

_PATTERNS = {t: re.compile(rf"\b{re.escape(t)}(?:e?s)?\b", re.IGNORECASE) for t in THEO_DOI}


def tim_thuat_ngu(source: str) -> list[str]:
    """Cac thuat ngu theo doi co trong cau goc."""
    return [t for t, p in _PATTERNS.items() if p.search(source)]


def phan_loai(ban_dich: str, term: str, theo_doi: dict = THEO_DOI) -> tuple[str, str]:
    """(bien the, loai) cua thuat ngu `term` trong ban dich."""
    text = str(ban_dich).lower()
    for variant, loai in theo_doi[term]:
        if variant in text:
            return variant, loai
    return KHAC, "khác"


def cac_cap(df: pd.DataFrame, col: str, theo_doi: dict = THEO_DOI) -> pd.DataFrame:
    """Moi dong mot cap (doan, thuat ngu): id, bo, term, bien_the, loai."""
    prose = df[df["loai_doan"] == "văn xuôi"] if "loai_doan" in df else df
    rows = []
    for r in prose.itertuples(index=False):
        for term in tim_thuat_ngu(r.source):
            variant, loai = phan_loai(getattr(r, col), term, theo_doi)
            bo = "dsa" if term in BO_DSA else "d2l"
            rows.append({"id": r.id, "bo": bo, "term": term, "bien_the": variant, "loai": loai})
    return pd.DataFrame(rows, columns=["id", "bo", "term", "bien_the", "loai"])


def _nhat_quan(pairs: pd.DataFrame) -> float:
    if pairs.empty:
        return float("nan")
    top = pairs.groupby("term")["bien_the"].agg(lambda s: Counter(s).most_common(1)[0][1])
    return top.sum() / len(pairs)


def tong_ket(df: pd.DataFrame, col: str, theo_doi: dict = THEO_DOI) -> pd.DataFrame:
    """Mot dong cho moi bo (d2l, dsa) va mot dong "tất cả": so cap, sai, khac, khop bang, nhat quan."""
    pairs = cac_cap(df, col, theo_doi)
    out = []
    for bo, g in [*pairs.groupby("bo"), ("tất cả", pairs)]:
        out.append({
            "he_thong": col, "bo": bo, "so_cap": len(g),
            "sai_nghia": int((g.loai == "sai").sum()),
            "khac_bo_sot": int((g.loai == "khác").sum()),
            "khop_bang": int((g.loai == "bảng").sum()),
            "nhat_quan": round(100 * _nhat_quan(g), 1),
        })
    res = pd.DataFrame(out)
    res["sai_tu_dong"] = res.sai_nghia + res.khac_bo_sot
    res["ty_le_sai_%"] = (100 * res.sai_tu_dong / res.so_cap).round(1)
    return res


def bang_bien_the(df: pd.DataFrame, col: str) -> pd.Series:
    """Giong cot he thong trong tong_hop: 'lớp ẩn (37), tầng ẩn (2)'."""
    pairs = cac_cap(df, col)
    return pairs.groupby("term", sort=False)["bien_the"].agg(
        lambda s: ", ".join(f"{v} ({n})" for v, n in Counter(s).most_common()))


def doc_bang(path: str) -> pd.DataFrame:
    if path.endswith(".csv"):
        return pd.read_csv(path)
    return pd.read_excel(path, sheet_name="so_sanh")


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        raise SystemExit(__doc__)
    df = doc_bang(argv[0])
    pd.set_option("display.width", 200)
    for col in argv[1:]:
        print(tong_ket(df, col).to_string(index=False))
        print()


if __name__ == "__main__":
    main(sys.argv[1:])
