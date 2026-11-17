"""Xu ly thuat ngu quanh moi lan dich (chu so huu: A).

B chi goi ba ham nay, khong goi gi khac trong thu muc terms/:

    state = new_chapter()
    text_in, info = prepare(segment, state)
    text_out = finalize(model_output, info)
"""
from terms.core import ChapterState, Term, finalize, load_glossary, new_chapter, prepare

__all__ = ["ChapterState", "Term", "finalize", "load_glossary", "new_chapter", "prepare"]
