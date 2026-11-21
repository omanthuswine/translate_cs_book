"""Gom van ban ky thuat tieng Viet de dem cach nguoi Viet that su viet thuat ngu (chu so huu: A).

Nguon (deu cong khai):
- d2l-vi nhanh v0.15: ban NGUOI dich cua Dive into Deep Learning (nhanh main/release la dich may, khong dung).
- VNOI Wiki: bai viet thuat toan do cong dong viet, co tac gia va nguoi duyet.
- Machine Learning cơ bản (Vũ Hữu Tiệp): sach (LaTeX) va blog, tai lieu hoc may tieng Viet duoc dung rong rai.
- Wikipedia tieng Viet (wikimedia/wikipedia 20231101.vi).
- FineWeb-2 tieng Viet (HuggingFaceFW/fineweb-2, vie_Latn, giay phep ODC-By): khoang 2.8 GB, xem FW_FILES.

Chi giu bai "ky thuat": co tu MIN_MARKERS tu khoa ky thuat khac nhau. Tu khoa gom ca tieng Anh va tieng Viet,
nhieu linh vuc, de viec loc khong thien ve cach viet nao khi dem.

Ket qua: cache/thuat_ngu/kho/<nguon>.jsonl, moi dong {"nguon", "url", "text"}.

Chay (tu goc repo):
    python -m terms.xay_dung.tai_kho_vi --nguon d2l vnoi wiki fineweb
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NGUON_DIR = ROOT / "cache" / "thuat_ngu" / "nguon"
KHO_DIR = ROOT / "cache" / "thuat_ngu" / "kho"

MIN_MARKERS = 4
MIN_CHARS = 400
MARKERS = [
    # tieng Viet
    "máy tính", "phần mềm", "phần cứng", "lập trình", "lập trình viên", "mã nguồn", "thuật toán",
    "cấu trúc dữ liệu", "cơ sở dữ liệu", "hệ điều hành", "mạng máy tính", "giao thức", "máy chủ",
    "trình biên dịch", "bộ nhớ", "tiến trình", "luồng", "bảo mật", "mã hóa", "học máy", "học sâu",
    "trí tuệ nhân tạo", "mạng nơ-ron", "dữ liệu", "công nghệ thông tin", "kiểm thử", "đồ thị",
    "độ phức tạp", "truy vấn", "biên dịch", "lỗ hổng", "điện toán đám mây",
    # tieng Anh
    "algorithm", "software", "hardware", "database", "server", "compiler", "python", "java",
    "javascript", "c++", "sql", "linux", "git", "github", "api", "cpu", "gpu", "http", "tcp",
    "framework", "code", "debug", "deploy", "machine learning", "deep learning", "neural network",
    "backend", "frontend", "docker", "kubernetes", "thread", "process", "query", "cache",
]
_MARKER_RE = re.compile(r"(?<![\w+])(" + "|".join(re.escape(m) for m in sorted(MARKERS, key=len, reverse=True))
                        + r")(?![\w+])")


def chuan_hoa(text: str) -> str:
    return unicodedata.normalize("NFC", text)


_CO_DAU = set("ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ")


def la_tieng_viet(text: str) -> bool:
    """Bo tep chu yeu la ma ve hinh (TikZ) hay code: chu co dau tieng Viet phai chiem it nhat 5% so chu cai."""
    letters = [c for c in text.lower() if c.isalpha()]
    return bool(letters) and sum(c in _CO_DAU for c in letters) / len(letters) >= 0.05


def la_bai_ky_thuat(text: str) -> bool:
    if len(text) < MIN_CHARS:
        return False
    return len(set(_MARKER_RE.findall(text.lower()))) >= MIN_MARKERS


class Ghi:
    """Ghi tung bai vao jsonl, bo bai trung (theo noi dung)."""

    def __init__(self, nguon: str, ghi_tiep: bool = False):
        KHO_DIR.mkdir(parents=True, exist_ok=True)
        self.path = KHO_DIR / f"{nguon}.jsonl"
        self.nguon, self.seen, self.n, self.chars = nguon, set(), 0, 0
        cu = []
        if ghi_tiep and self.path.exists():              # chay tiep: giu bai cu (bo dong hong do bi ngat giua chung)
            for line in open(self.path, encoding="utf-8"):
                try:
                    cu.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        self.f = open(self.path, "w", encoding="utf-8")
        for d in cu:
            self.them(d["text"], d["url"])

    def them(self, text: str, url: str = "") -> None:
        text = chuan_hoa(text).strip()
        h = hashlib.md5(text.encode("utf-8")).digest()
        if h in self.seen:
            return
        self.seen.add(h)
        self.f.write(json.dumps({"nguon": self.nguon, "url": url, "text": text}, ensure_ascii=False) + "\n")
        self.n += 1
        self.chars += len(text)

    def dong(self) -> None:
        self.f.close()
        print(f"  {self.nguon}: {self.n} bai, {self.chars / 1e6:.1f} trieu ky tu -> {self.path}", flush=True)


# --------------------------------------------------------------------------- markdown cuc bo

_CODE = re.compile(r"```.*?```", re.S)
_MATH = re.compile(r"\$\$.*?\$\$", re.S)
_COMMENT = re.compile(r"<!--.*?-->", re.S)          # d2l v0.15: ban tieng Anh goc nam trong comment
_FRONT = re.compile(r"\A---\n.*?\n---\n", re.S)     # VNOI: thong tin dau bai


def lam_sach_md(text: str) -> str:
    for rx in (_FRONT, _COMMENT, _CODE, _MATH):
        text = rx.sub(" ", text)
    return text


def tu_markdown(thu_muc: str, nguon: str, url_goc: str, ghi: "Ghi | None" = None, duoi: str = "*.md") -> None:
    g = ghi or Ghi(nguon)
    base = NGUON_DIR / thu_muc
    for p in sorted(base.rglob(duoi)):
        if ".git" in p.parts:
            continue
        raw = p.read_text(encoding="utf-8", errors="replace")
        if duoi == "*.tex":
            from terms.xay_dung.kho_en import _tex
            text = _tex(raw)
        else:
            text = lam_sach_md(raw)
        if len(text.strip()) >= MIN_CHARS and la_tieng_viet(text):   # nguon chuyen nganh: khong can loc tu khoa
            g.them(text, url_goc + p.relative_to(base).as_posix())
    if ghi is None:
        g.dong()


def tu_mlcb() -> None:
    """Sach va blog "Machine Learning cơ bản" (Vũ Hữu Tiệp): tai lieu hoc may tieng Viet duoc dung rong rai."""
    g = Ghi("mlcb")
    tu_markdown("ebookMLCB", "mlcb", "https://github.com/tiepvupsu/ebookMLCB/blob/master/", g, "*.tex")
    tu_markdown("tiepvupsu.github.io", "mlcb", "https://github.com/tiepvupsu/tiepvupsu.github.io/blob/master/", g)
    g.dong()


# --------------------------------------------------------------------------- Hugging Face

def tu_wikipedia() -> None:
    import pyarrow.parquet as pq
    from huggingface_hub import HfApi, hf_hub_download

    repo = "wikimedia/wikipedia"
    files = sorted(f.path for f in HfApi().list_repo_tree(repo, repo_type="dataset", path_in_repo="20231101.vi")
                   if f.path.endswith(".parquet"))
    g, xem = Ghi("wiki"), 0
    for path in files:
        local = hf_hub_download(repo, path, repo_type="dataset")
        for batch in pq.ParquetFile(local).iter_batches(columns=["url", "text"], batch_size=5000):
            for url, text in zip(batch.column("url").to_pylist(), batch.column("text").to_pylist()):
                xem += 1
                if la_bai_ky_thuat(text):
                    g.them(text, url)
        print(f"  wiki: xong {path}, da xem {xem} bai, giu {g.n}", flush=True)
    g.dong()


# Doc tung doan nho tren Hugging Face rat cham (file luu dang chia manh), nen tai nguyen file roi loc tren may.
# Kho fineweb.jsonl hien gom: 401 row group dau cua train/000_00000 (doc truc tiep lan dau, 0.78 GB)
# + nguyen file train/004_00005 (1.96 GB, file nho nhat) + test/000_00000 (59 MB).
FW_FILES = ["data/vie_Latn/train/004_00005.parquet", "data/vie_Latn/test/000_00000.parquet"]


def tu_fineweb(files: list[str], ghi_tiep: bool = True) -> None:
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download

    g, t0 = Ghi("fineweb", ghi_tiep=ghi_tiep), time.time()
    print(f"  fineweb: giu {g.n} bai tu lan truoc", flush=True)
    for path in files:
        local = hf_hub_download("HuggingFaceFW/fineweb-2", path, repo_type="dataset")
        print(f"  fineweb: da tai {path}, {(time.time() - t0) / 60:.1f} phut", flush=True)
        xem = 0
        for batch in pq.ParquetFile(local).iter_batches(columns=["url", "text"], batch_size=10000):
            for url, text in zip(batch.column("url").to_pylist(), batch.column("text").to_pylist()):
                xem += 1
                if la_bai_ky_thuat(text):
                    g.them(text, url)
        print(f"  fineweb: xong {path}, xem {xem} bai, tong giu {g.n}, {(time.time() - t0) / 60:.1f} phut", flush=True)
    g.dong()


def van_thuong(so_bai: int = 100_000) -> None:
    """Mau van ban DOI THUONG (bai khong phai ky thuat) tu file FineWeb da tai, ghi vao kho/chung.jsonl.

    Dung de tru phan mot chu duoc dung theo nghia thuong ("chú ý", "mất mát", "luồng") khi dem cach viet.
    """
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download

    local = hf_hub_download("HuggingFaceFW/fineweb-2", FW_FILES[0], repo_type="dataset")
    g = Ghi("chung")
    for batch in pq.ParquetFile(local).iter_batches(columns=["url", "text"], batch_size=10000):
        for url, text in zip(batch.column("url").to_pylist(), batch.column("text").to_pylist()):
            if len(text) >= MIN_CHARS and not la_bai_ky_thuat(text):
                g.them(text, url)
        if g.n >= so_bai:
            break
    g.dong()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nguon", nargs="+", default=["d2l", "vnoi", "wiki", "fineweb"])
    ap.add_argument("--fineweb-file", nargs="+", default=FW_FILES)
    args = ap.parse_args()
    if "d2l" in args.nguon:
        tu_markdown("d2l-vi", "d2l", "https://github.com/d2l-ai/d2l-vi/blob/v0.15/")
    if "vnoi" in args.nguon:
        tu_markdown("vnoi_wiki", "vnoi", "https://github.com/VNOI-Admin/vnoi_wiki/blob/master/")
    if "mlcb" in args.nguon:
        tu_mlcb()
    if "wiki" in args.nguon:
        tu_wikipedia()
    if "fineweb" in args.nguon:
        tu_fineweb(args.fineweb_file)
    if "chung" in args.nguon:
        van_thuong()


if __name__ == "__main__":
    main()
