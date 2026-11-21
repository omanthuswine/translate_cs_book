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
    assert ov.lan_dau in out[0]                   # overfitting (quá khớp)
    assert ov.lan_sau not in sent[1]              # lan sau la tieng Anh -> ma giu cho
    assert out[1] == f"Avoid {ov.lan_sau}."


def test_new_chapter_resets_first_use():
    st = G["stack"]
    _, out1 = run(["A stack here.", "Another stack."])
    _, out2 = run(["A stack again."])
    assert st.lan_dau in out1[0] and st.lan_sau in out1[1] and st.lan_dau not in out1[1]
    assert st.lan_dau in out2[0]


@pytest.mark.parametrize("protect_all", [True, False])
def test_capitalized_at_sentence_start(monkeypatch, protect_all):
    monkeypatch.setattr(terms.core, "PROTECT_ALL_FORMS", protect_all)
    _, out = run(["Stacks are simple."])
    assert out[0].startswith(G["stack"].lan_dau[0].upper() + G["stack"].lan_dau[1:])


def test_longest_term_wins():
    _, out = run(["The batch size of each batch."])
    assert G["batch size"].lan_dau in out[0]
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


def test_vietnamese_forms_are_hidden_too_by_default():
    st = G["stack"]
    sent, out = run(["A stack here.", "Stacks again."])
    assert "ngăn" not in sent[0] and "[T1]" in sent[0]
    assert out[0] == f"A {st.lan_dau} here."
    assert out[1] == f"{st.lan_sau[0].upper() + st.lan_sau[1:]} again."   # dau cau viet hoa


def test_inline_mode_inserts_vietnamese_forms_directly(monkeypatch):
    monkeypatch.setattr(terms.core, "PROTECT_ALL_FORMS", False)
    sent, out = run(["We study overfitting.", "A stack here."])
    assert G["overfitting"].lan_dau in sent[0] and G["stack"].lan_dau in sent[1]
    assert "[T" not in sent[1]


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


# --- Don ban dich (finalize) ---------------------------------------------------------------------------------

def test_finalize_drops_word_repeated_before_placeholder():
    info = {"placeholders": {"[T1]": "mạng sâu", "[T2]": "phương pháp Master"}}
    out = terms.finalize("Xét một mạng [T1] và dùng phương pháp [T2].", info)
    assert out == "Xét một mạng sâu và dùng phương pháp Master."


@pytest.mark.parametrize("nguon, ra, mong", [
    ("Consider a bank that wants to develop a", "Hãy xem xét một ngân hàng muốn phát triển…", "Hãy xem xét một ngân hàng muốn phát triển"),
    ("on the D2L.ai website8 and on GitHub9.", "trên D2L.ai<sup>8</sup> và GitHub<sup>9</sup>.", "trên D2L.ai8 và GitHub9."),
    ("matrices with a rows and b columns", "ma trận có *a* hàng và **b** cột", "ma trận có a hàng và b cột"),
    ("Wait... what?", "Đợi đã... sao?", "Đợi đã... sao?"),            # doan goc co "..." thi giu
])
def test_finalize_removes_what_model_added(nguon, ra, mong):
    assert terms.finalize(ra, {"placeholders": {}, "nguon": nguon}) == mong


def test_finalize_restores_lost_list_number():
    _, info = terms.prepare("1. Register an account on the forum.", terms.new_chapter())
    assert terms.finalize("Đăng ký một tài khoản trên diễn đàn.", info) == "1. Đăng ký một tài khoản trên diễn đàn."
    assert terms.finalize("1. Đăng ký.", info) == "1. Đăng ký."


# --- Chen theo ngu canh ("ngữ cảnh") va vi tri bo nghia ------------------------------------------------------

@pytest.fixture
def bang_tam(tmp_path, monkeypatch):
    """Bang thuat ngu nho co muc "ngữ cảnh" (bang chinh thuc v4 chua co loai nay)."""
    p = tmp_path / "bang.csv"
    p.write_text(
        "source,cach_xu_ly,lan_dau,lan_sau,linh_vuc,tu_dong\n"
        "attention,Anh (Việt),attention (chú ý),attention,NLP,ngữ cảnh\n"
        "transformer,giữ tiếng Anh,Transformer,Transformer,NLP,có\n"
        "query,giữ tiếng Anh,query,query,NLP,có\n"
        "asymptotic,dịch,tiệm cận,tiệm cận,Thuật toán,có\n",
        encoding="utf-8")
    monkeypatch.setattr(terms.core, "GLOSSARY_PATH", p)
    monkeypatch.setattr(terms.core, "PROTECT_ALL_FORMS", True)
    return p


def test_context_term_injected_only_in_technical_context(bang_tam):
    st = terms.new_chapter()
    thuong, info = terms.prepare("Pay attention to the boundary cases.", st)
    assert "attention" in thuong and info["terms"] == []
    ky_thuat, info = terms.prepare("The Transformer computes attention from each query.", st)
    assert "attention" not in ky_thuat and "attention" in info["terms"]


def test_context_term_uses_chapter_topic(bang_tam, monkeypatch):
    monkeypatch.setattr(terms.core, "NGU_CANH_CHUONG", 2)
    st = terms.new_chapter()
    terms.prepare("A Transformer uses each query.", st)          # chuong dang noi ve NLP
    _, info = terms.prepare("We add attention here.", st)
    assert info["terms"] == ["attention"]


def test_modifier_position_can_use_inline_vietnamese(bang_tam, monkeypatch):
    monkeypatch.setattr(terms.core, "VI_TRI_BO_NGHIA", "chen_thang")
    text_in, info = terms.prepare("The asymptotic behavior is clear. It is asymptotic.", terms.new_chapter())
    assert "tiệm cận behavior" in text_in                        # truoc danh tu: chen thang
    assert list(info["placeholders"].values()) == ["tiệm cận"]   # dung rieng: van dung ma


# --- Dich lai khi mo hinh lam roi ma (retry_lost_terms) -----------------------------------------------------

class DichGia:
    """Ham dich gia: tra theo bang {dau vao: ban dich}, ghi lai cac lan goi."""
    def __init__(self, bang, mac_dinh="x"):
        self.bang, self.mac_dinh, self.goi = bang, mac_dinh, []

    def __call__(self, text):
        self.goi.append(text)
        return self.bang.get(text, self.mac_dinh)


def test_retry_does_nothing_when_no_placeholder_lost(bang_tam):
    text_in, info = terms.prepare("The asymptotic behavior is clear.", terms.new_chapter())
    dich = DichGia({})
    assert terms.retry_lost_terms("Hành vi [T1] rõ ràng.", info, dich) == ("Hành vi [T1] rõ ràng.", info)
    assert dich.goi == []


def test_retry_writes_lost_term_inline(bang_tam):
    text_in, info = terms.prepare("The asymptotic behavior is clear.", terms.new_chapter())
    assert text_in == "The [T1] behavior is clear."
    dich = DichGia({"The tiệm cận behavior is clear.": "Hành vi tiệm cận rõ ràng."})
    out, info2 = terms.retry_lost_terms("Hành vi rõ ràng.", info, dich)      # mo hinh bo mat [T1]
    assert dich.goi == ["The tiệm cận behavior is clear."]                   # chen thang du, khong tach cau
    assert terms.finalize(out, info2) == "Hành vi tiệm cận rõ ràng."


def test_retry_splits_sentences_when_inline_still_fails(bang_tam):
    text_in, info = terms.prepare("The asymptotic behavior is clear. It is asymptotic.", terms.new_chapter())
    assert text_in == "The [T1] behavior is clear. It is [T2]."
    dich = DichGia({"The tiệm cận behavior is clear. It is [T2].": "Hành vi rõ ràng. Nó là [T2].",
                    "The [T1] behavior is clear.": "Hành vi [T1] rõ ràng.", "It is [T2].": "Nó là [T2]."})
    out, info2 = terms.retry_lost_terms("Hành vi rõ ràng. Nó là [T2].", info, dich)
    assert len(dich.goi) == 3
    assert terms.finalize(out, info2) == "Hành vi tiệm cận rõ ràng. Nó là tiệm cận."


def test_retry_keeps_first_translation_when_nothing_is_better(bang_tam):
    _, info = terms.prepare("The asymptotic behavior is clear. It is asymptotic.", terms.new_chapter())
    out, info2 = terms.retry_lost_terms("Hành vi rõ ràng. Nó là [T2].", info, DichGia({}))
    assert out == "Hành vi rõ ràng. Nó là [T2]." and info2 is info


def test_retry_ignores_info_without_text_in():
    info = {"placeholders": {"[T1]": "GPU"}}
    assert terms.retry_lost_terms("mất mã", info, DichGia({})) == ("mất mã", info)
