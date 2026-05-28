from russian_vocab_desktop.tokenize import tokenize


def test_tokenize_drops_mixed_script_tokens():
    text = "вода вoда книга abc Москва"
    assert tokenize(text, min_length=2) == ["вода", "книга", "москва"]


def test_tokenize_respects_min_length():
    assert tokenize("я и мы дом", min_length=2) == ["мы", "дом"]
