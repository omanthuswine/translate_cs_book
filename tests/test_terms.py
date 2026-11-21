"""Kiem tra hanh vi ben trong module terms (chu so huu: A).

Gia tri mong doi doc tu bang thuat ngu, nen sua cach viet trong bang khong lam vo test;
chi khi doi cach xu ly cua cac tu dung o day (Quicksort, overfitting, stack, RNN...) moi phai sua test.
"""
import pytest

import terms

G = {t.source: t for t in terms.load_glossary()}


def run(segments, translate=lambda s: s):
    """Ba buoc cua diem giao tren mot chuong, voi dich gia tra nguyen van."""
    state = terms.new_chapter()
    sent, out = [], []
    for seg in segments:
        text_in, info = terms.prepare(seg, state)
        sent.append(text_in)
        out.append(terms.finalize(translate(text_in), info))
    return sent, out


def test_glossary_terms_used_here_keep_their_kind():
    assert G["Quicksort"].cach_xu_ly == "giữ tiếng Anh"
    assert G["overfitting"].cach_xu_ly == "Anh (Việt)" and G["overfitting"].tu_dong
    assert G["stack"].cach_xu_ly == "Việt (Anh)" and G["stack"].tu_dong
    assert G["recurrent neural network"].lan_sau == "RNN"
    assert not G["kernel"].tu_dong


def test_keep_english_is_hidden_from_model_then_restored():
    sent, out = run(["Quicksort is fast."])
    assert "Quicksort" not in sent[0] and "[T1]" in sent[0]
    assert out[0] == "Quicksort is fast."


def test_first_use_in_chapter_gets_gloss_later_uses_do_not():
    ov = G["overfitting"]
    sent, out = run(["We study overfitting.", "Avoid overfitting."])
    assert ov.lan_dau in sent[0]                  # chen thang: overfitting (quá khớp)
    assert ov.lan_sau not in sent[1]              # lan sau la tieng Anh -> ma giu cho
    assert out[1] == f"Avoid {ov.lan_sau}."


def test_new_chapter_resets_first_use():
    st = G["stack"]
    _, out1 = run(["A stack here.", "Another stack."])
    _, out2 = run(["A stack again."])
    assert st.lan_dau in out1[0] and st.lan_sau in out1[1] and st.lan_dau not in out1[1]
    assert st.lan_dau in out2[0]


def test_capitalized_at_sentence_start():
    sent, _ = run(["Stacks are simple."])
    assert sent[0].startswith(G["stack"].lan_dau[0].upper() + G["stack"].lan_dau[1:])


def test_longest_term_wins():
    sent, out = run(["The batch size of each batch."])
    assert G["batch size"].lan_dau in sent[0]
    assert out[0].endswith("of each batch.")


@pytest.mark.parametrize("text, source", [
    ("two stacks", "stack"),
    ("conditional probabilities", "conditional probability"),
    ("adjacency matrices", "adjacency matrix"),
    ("a fine tuning step", "fine-tuning"),
    ("a finetuning step", "fine-tuning"),
    ("Dijkstra’s algorithm", "Dijkstra's algorithm"),
])
def test_matches_plural_and_spelling_variants(text, source):
    state = terms.new_chapter()
    _, info = terms.prepare(text, state)
    assert info["terms"] == [source]


@pytest.mark.parametrize("text", [
    "Call nn.Dropout here.",          # thuoc tinh trong code
    "Compute softmax(x) first.",      # loi goi ham
    "Use np.array or a gan.",         # viet tat chi khop dung hoa thuong (NP, GAN)
    "A Gaussian kernel.",             # kernel: tu_dong = khong
])
def test_does_not_touch_code_or_ambiguous_words(text):
    text_in, info = terms.prepare(text, terms.new_chapter())
    assert text_in == text and info["terms"] == []


def test_existing_abbreviation_in_parentheses_is_not_doubled():
    rnn = G["recurrent neural network"]
    sent, out = run(["Recurrent neural networks (RNNs) are old."])
    assert "RNNs" not in sent[0] and "(RNN) (" not in out[0]
    assert out[0].lower().startswith(rnn.lan_dau.lower())


def test_protect_all_forms_hides_vietnamese_forms_too(monkeypatch):
    monkeypatch.setattr(terms.core, "PROTECT_ALL_FORMS", True)
    st = G["stack"]
    sent, out = run(["A stack here.", "Stacks again."])
    assert "ngăn" not in sent[0] and "[T1]" in sent[0]
    assert out[0] == f"A {st.lan_dau} here."
    assert out[1] == f"{st.lan_sau[0].upper() + st.lan_sau[1:]} again."   # dau cau viet hoa


def test_placeholder_never_collides_with_existing_text():
    sent, out = run(["Cite [T1] then use dropout."])
    assert sent[0].count("[T1]") == 1
    assert out[0] == "Cite [T1] then use dropout."


@pytest.mark.parametrize("model_output", ["[T1] nhanh.", "[ T1 ] nhanh.", "(T1) nhanh.", "【T1】 nhanh.", "[t1] nhanh."])
def test_finalize_tolerates_changed_brackets_and_capitalizes(model_output):
    _, info = terms.prepare("We apply dropout.", terms.new_chapter())
    assert terms.finalize(model_output, info) == "Dropout nhanh."


def test_finalize_does_not_confuse_t1_and_t12():
    info = {"placeholders": {"[T1]": "GPU", "[T12]": "CPU"}}
    assert terms.finalize("[T12] và [T1]", info) == "CPU và GPU"
