"""Kiem tra diem giao giua A (terms/) va B (pipeline/). Ca hai phai giu test nay xanh."""
import inspect

import terms
from pipeline.run import translate_chapter
from pipeline.translate import fake_translate


def test_glossary_loads_with_expected_columns():
    glossary = terms.load_glossary()
    assert len(glossary) > 400
    kinds = {t.cach_xu_ly for t in glossary}
    assert kinds <= {"giữ tiếng Anh", "Anh (Việt)", "Việt (Anh)", "dịch"}


def test_signatures_unchanged():
    assert list(inspect.signature(terms.new_chapter).parameters) == []
    assert list(inspect.signature(terms.prepare).parameters) == ["segment", "state"]
    assert list(inspect.signature(terms.finalize).parameters) == ["model_output", "info"]


def test_prepare_and_finalize_types():
    state = terms.new_chapter()
    text_in, info = terms.prepare("Quicksort is a divide-and-conquer algorithm.", state)
    assert isinstance(text_in, str) and isinstance(info, dict)
    assert isinstance(terms.finalize(text_in, info), str)


def test_keep_english_term_survives_round_trip():
    # Voi dich gia (tra nguyen van), tu "giu tieng Anh" phai con nguyen sau ba buoc.
    out = translate_chapter(["Quicksort and Merge sort are sorting algorithms."], fake_translate)
    assert "Quicksort" in out[0] and "Merge sort" in out[0]


def test_pipeline_keeps_segment_order():
    segs = ["First segment.", "Second segment.", "Third segment."]
    assert len(translate_chapter(segs, fake_translate)) == 3
