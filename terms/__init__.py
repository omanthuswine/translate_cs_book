"""Xu ly thuat ngu quanh moi lan dich (chu so huu: A).

B chi goi cac ham nay, khong goi gi khac trong thu muc terms/:

    state = new_chapter()
    text_in, info = prepare(segment, state)
    model_output = translate_fn(text_in)
    model_output, info = retry_lost_terms(model_output, info, translate_fn)   # tuy chon: dich lai khi roi ma
    text_out = finalize(model_output, info)
"""
from terms.core import ChapterState, Term, finalize, load_glossary, new_chapter, prepare, retry_lost_terms

__all__ = ["ChapterState", "Term", "finalize", "load_glossary", "new_chapter", "prepare", "retry_lost_terms"]
