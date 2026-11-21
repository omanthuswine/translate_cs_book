"""Tao bang thuat ngu v5 tu ket qua xep nhom va nhan xet cua nguoi duyet (chu so huu: A).

Dau vao: cache/thuat_ngu/phan_loai.json (phan_loai.py), terms/xay_dung/nhan_xet_claude.csv (nguoi duyet: Claude).
Dau ra (KHONG ghi de bang dang dung terms/glossary_cs_vi.csv):
- terms/thuat_ngu_khmt_v5.xlsx: bang day du kem can cu tung muc, sheet nguyen_tac.
- terms/glossary_cs_vi_v5.csv: dung cot nhu glossary_cs_vi.csv; tu_dong = có | không | ngữ cảnh.
- terms/xay_dung/cho_xac_minh.csv: thuat ngu moi chua du can cu, de khao sat / bo sung nguon sau.

Vao bang v5: moi muc cua v4 (da cap nhat), thuat ngu moi co cach dich doi chieu duoc tu >= 2 nguon uy tin hoac
do tin cay >= vua, va thuat ngu nguoi duyet da xem.
Chay (tu goc repo): python -m terms.xay_dung.xay_bang_v5
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from terms.xay_dung.phan_loai import cach_viet

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cache" / "thuat_ngu"
HERE = Path(__file__).resolve().parent
TERMS = ROOT / "terms"

MAU = {"Anh (Việt)": "FCE4D6", "giữ tiếng Anh": "FFF2CC", "Việt (Anh)": "E2EFDA", "dịch": None}   # nhu v4
NGUON_TEN = {"v4": "bảng v4", "d2l": "D2L (người dịch)", "mlcb": "Machine Learning cơ bản", "vnoi": "VNOI",
             "ms": "Microsoft", "wiki": "Wikipedia", "fineweb": "web (FineWeb-2)"}


def doc_nhan_xet() -> dict[str, dict]:
    with open(HERE / "nhan_xet_claude.csv", encoding="utf-8", newline="") as f:
        return {r["en"].lower(): r for r in csv.DictReader(f)}


def ap_nhan_xet(x: dict, nx: dict) -> dict | None:
    """Ap nhan xet cua nguoi duyet. None = bo khoi bang."""
    if nx["hanh_dong"] == "bỏ":
        return None
    kind, vi, dau = nx["cach_xu_ly"], nx["vi"] or None, nx["dau"] or None
    lan_dau, lan_sau = cach_viet(kind, x["en"], vi, dau)
    return {**x, "cach_xu_ly": kind, "vi": vi, "lan_dau": lan_dau, "lan_sau": lan_sau, "tu_dong": nx["tu_dong"],
            "tin_cay": "người duyệt", "quyet_dinh": "nhận xét của Claude" + (f": {nx['ly_do']}" if nx["ly_do"] else ""),
            "ly_do": x.get("ly_do", "")}


def main() -> None:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    import terms
    v4 = {t.source.lower(): t for t in terms.load_glossary()}
    nx = doc_nhan_xet()
    res = json.loads((CACHE / "phan_loai.json").read_text(encoding="utf-8"))

    bang, cho = [], []
    for x in res:
        k = x["en"].lower()
        if k in nx:
            x = ap_nhan_xet(x, nx[k])
            if x is None:
                continue
        elif "bo" in x:
            continue
        dat = x.get("v4") or x["tin_cay"] in ("cao", "vừa", "người duyệt") or x.get("vi_du_nguon")
        # Luat an toan: muc moi do may tu quyet KHONG chen tu dong. Duyet mau 21/11 thay ~20% muc loai nay co van de
        # (vd deviation -> "độ lệch chuẩn"); chi muc v4 va muc nguoi duyet da xem moi duoc chen.
        if dat and not x.get("v4") and x["tin_cay"] != "người duyệt" and x["tu_dong"] != "không":
            x["tu_dong"] = "không"
            x["ly_do"] = "; ".join(s for s in (x.get("ly_do", ""), "mục mới do máy quyết: chưa chèn tự động") if s)
        (bang if dat else cho).append(x)
    # bang v4 phai du 484 muc (khong muc nao bi bo)
    thieu = set(v4) - {x["en"].lower() for x in bang}
    assert not thieu, f"mat muc cua v4: {sorted(thieu)[:10]}"

    # Bot ma thua (bot_ma_thua.py): mo hinh von da dich dung thi thoi chen, moi ma them la them mot cho co the roi
    p_bot = HERE / "mo_hinh_tu_dich_dung.csv"
    tu_dich_dung = {r["en"].lower(): r for r in csv.DictReader(open(p_bot, encoding="utf-8"))} if p_bot.exists() else {}
    for x in bang:
        r = tu_dich_dung.get(x["en"].lower())
        if r and x["tu_dong"] != "không" and x["lan_dau"] == x["lan_sau"]:
            x["tu_dong"] = "không"
            x["ly_do"] = "; ".join(s for s in (x.get("ly_do", ""), f"bớt mã thừa: mô hình tự dịch đúng {float(r['ty_le_dung']):.0%} "
                                   f"trên {r['so_doan']} đoạn ngoài bộ chấm") if s)

    thu_tu = {k: i for i, k in enumerate(v4)}                       # v4 giu thu tu cu, muc moi xep sau theo linh vuc
    bang.sort(key=lambda x: (thu_tu.get(x["en"].lower(), 10**6), x["linh_vuc"], x["en"].lower()))

    def thay_doi(x: dict) -> str:
        t = v4.get(x["en"].lower())
        if not t:
            return "mới"
        if (x["cach_xu_ly"], x["lan_dau"], x["lan_sau"]) == (t.cach_xu_ly, t.lan_dau, t.lan_sau):
            return ""
        return f"v4: {t.cach_xu_ly} | {t.lan_dau}"

    # --- CSV cho chuong trinh (cung cot voi glossary_cs_vi.csv)
    with open(TERMS / "glossary_cs_vi_v5.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["source", "cach_xu_ly", "lan_dau", "lan_sau", "linh_vuc", "tu_dong"])
        for x in bang:
            w.writerow([x["en"], x["cach_xu_ly"], x["lan_dau"], x["lan_sau"], x["linh_vuc"], x["tu_dong"]])

    # --- Excel day du kem can cu
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "thuat_ngu"
    cols = ["Tiếng Anh", "Cách xử lý", "Lần đầu trong chương", "Các lần sau", "Lĩnh vực", "Xử lý tự động",
            "Độ tin cậy", "Căn cứ", "Nguồn ủng hộ cách dịch", "Tỷ lệ viết tiếng Anh", "Thay đổi so với v4"]
    ws.append(cols)
    for c in ws[1]:
        c.font, c.fill = Font(bold=True), PatternFill("solid", fgColor="DDEBF7")
    for x in bang:
        nguon = ", ".join(NGUON_TEN.get(n, n) for n in x.get("vi_ung_ho", []))
        can_cu = "; ".join(s for s in (x.get("quyet_dinh", ""), x.get("ly_do", "")) if s)
        ws.append([x["en"], x["cach_xu_ly"], x["lan_dau"], x["lan_sau"], x["linh_vuc"], x["tu_dong"], x["tin_cay"],
                   can_cu, nguon, x.get("ty_le_en"), thay_doi(x)])
        mau = MAU.get(x["cach_xu_ly"])
        if mau:
            for c in ws[ws.max_row]:
                c.fill = PatternFill("solid", fgColor=mau)
    for col, width in zip("ABCDEFGHIJK", (30, 14, 40, 28, 18, 12, 12, 60, 34, 10, 40)):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes, ws.auto_filter.ref = "B2", f"A1:K{ws.max_row}"

    nt = wb.create_sheet("nguyen_tac")
    for line in NGUYEN_TAC:
        nt.append([line])
    nt.column_dimensions["A"].width = 140
    wb.save(TERMS / "thuat_ngu_khmt_v5.xlsx")

    # --- Danh sach cho xac minh
    with open(HERE / "cho_xac_minh.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["en", "linh_vuc", "de_xuat", "vi_de_xuat", "nguon_ung_ho", "ty_le_en", "ly_do"])
        for x in sorted(cho, key=lambda x: (x["linh_vuc"], x["en"].lower())):
            w.writerow([x["en"], x["linh_vuc"], x["cach_xu_ly"], x.get("vi_de_xuat") or "",
                        ",".join(x.get("vi_ung_ho", [])), x.get("ty_le_en"), x.get("ly_do", "")])

    moi = [x for x in bang if not x.get("v4")]
    print(f"Bang v5: {len(bang)} muc (v4: {len(bang) - len(moi)}, moi: {len(moi)}) | cho xac minh: {len(cho)}")
    print("  cach xu ly:", dict(Counter(x["cach_xu_ly"] for x in bang)))
    print("  tu_dong:", dict(Counter(x["tu_dong"] for x in bang)))
    print("  do tin cay:", dict(Counter(x["tin_cay"] for x in bang)))
    print("  muc v4 thay doi:", sum(1 for x in bang if x.get("v4") and thay_doi(x)))
    print("  moi theo linh vuc:", dict(Counter(x["linh_vuc"] for x in moi).most_common()))


NGUYEN_TAC = [
    "BẢNG THUẬT NGỮ v5 (21/11/2026). Mở rộng từ v4 bằng số liệu cách người Việt thật sự viết, xem terms/xay_dung/README.md",
    "",
    "BỐN CÁCH XỬ LÝ (giữ như v4)",
    "giữ tiếng Anh: để nguyên ở mọi lần. Anh (Việt): lần đầu 'overfitting (quá khớp)', các lần sau 'overfitting'.",
    "Việt (Anh): lần đầu 'ngăn xếp (stack)', sau 'ngăn xếp'. dịch: chỉ tiếng Việt.",
    "",
    "QUYẾT ĐỊNH BẰNG SỐ LIỆU",
    "Đếm trong văn bản kỹ thuật tiếng Việt (D2L bản người dịch, Machine Learning cơ bản, VNOI, Wikipedia, web FineWeb-2):",
    "người Việt viết thuật ngữ bằng tiếng Anh bao nhiêu phần trăm số lần.",
    "Dưới 20%: dịch. Từ 80%: giữ tiếng Anh. Lưng chừng: Anh (Việt) (nhóm chốt: ưu tiên Anh (Việt), cả với mục cũ của v4).",
    "Chỉ đếm chỗ đang nói chuyện chuyên ngành (có thuật ngữ khác cùng mảng gần đó), đã trừ phần dùng theo nghĩa đời thường.",
    "Đổi quyết định của v4 chỉ khi độ tin cậy cao: nhiều dữ liệu, xa ngưỡng, ít nhất 2 nguồn cùng kết luận.",
    "",
    "CÁCH DỊCH TIẾNG VIỆT: NGUỒN UY TÍN, ĐỐI CHIẾU NHIỀU NGUỒN",
    "Nguồn hạng 1: bảng v4, D2L bản người dịch (bảng thuật ngữ + gióng hàng 4.438 cặp đoạn song ngữ), Machine Learning cơ bản",
    "(sách, blog, chỉ mục song ngữ), VNOI Wiki, bảng thuật ngữ Việt hóa của Microsoft. Hạng 2: Wikipedia. Hạng 3: web.",
    "Một cách dịch chỉ được dùng khi có ít nhất 2 nguồn độc lập cùng dùng, trong đó ít nhất 1 nguồn hạng 1, và có bằng chứng",
    "ghép đôi (bảng ghi vậy, tác giả tự chú thích trong ngoặc, hoặc dùng cùng bài với chữ tiếng Anh).",
    "",
    "CỘT 'XỬ LÝ TỰ ĐỘNG'",
    "có: luôn chèn (thay bằng mã giữ chỗ, dán lại sau khi dịch). không: để mô hình tự dịch.",
    "ngữ cảnh: từ đa nghĩa (attention, kernel, clustering): chỉ chèn khi đoạn văn đang nói về mảng của thuật ngữ đó.",
    "",
    "NGƯỜI DUYỆT",
    "Mục ghi 'nhận xét của Claude' do Claude tự duyệt theo hiểu biết về thuật ngữ tin học tiếng Việt, khi số liệu chưa đủ",
    "hoặc nguồn dịch sai (vd Microsoft dịch 'garbage collection' là 'bộ sưu tập rác'; dân lập trình nói 'thu gom rác').",
    "Mục chưa đủ căn cứ không vào bảng, nằm ở terms/xay_dung/cho_xac_minh.csv để khảo sát sau.",
]


if __name__ == "__main__":
    main()
