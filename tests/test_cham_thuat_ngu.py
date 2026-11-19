"""Bo cham thuat ngu (eval/, chu so huu: A) phai cho lai dung so lieu moc xuat phat.

Can pandas va openpyxl; may chua cai thi bo qua.
"""
import sys
from pathlib import Path

import pytest

pytest.importorskip("pandas")
pytest.importorskip("openpyxl")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import cham_thuat_ngu as C  # noqa: E402


@pytest.fixture(scope="module")
def bo_thu():
    return C.doc_bang(str(ROOT / "eval" / "data" / "so_sanh_ban_dich_danh_gia.xlsx"))


def test_so_cap_khop_moc(bo_thu):
    t = C.tong_ket(bo_thu, "tg_4b").set_index("bo")
    assert t.loc["d2l", "so_cap"] == 317 and t.loc["dsa", "so_cap"] == 111


def test_4b_khop_moc(bo_thu):
    # Moc dem tay: d2l 6/317, CLRS 82/111, nhat quan 78%. Tu dong ra 83 o CLRS (1 doan dem tay coi la dien dat khac).
    t = C.tong_ket(bo_thu, "tg_4b").set_index("bo")
    assert t.loc["d2l", "sai_nghia"] == 6
    assert t.loc["dsa", "sai_tu_dong"] == 83
    assert t.loc["tất cả", "nhat_quan"] == pytest.approx(77.6)


def test_chatgpt_khop_moc(bo_thu):
    t = C.tong_ket(bo_thu, "chatgpt").set_index("bo")
    assert t.loc["d2l", "sai_nghia"] == 4 and t.loc["dsa", "sai_tu_dong"] == 0
    assert t.loc["tất cả", "nhat_quan"] == pytest.approx(98.1)


def test_phan_loai_uu_tien_cach_viet_trong_bang():
    assert C.phan_loai("lan truyền ngược (backpropagation)", "backpropagation") == ("lan truyền ngược", "bảng")
    assert C.phan_loai("mạng nơ-ron hồi quy", "recurrent") == ("hồi quy", "sai")
    assert C.phan_loai("không có gì", "recurrence") == (C.KHAC, "khác")
