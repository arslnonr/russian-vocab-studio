from russian_vocab_desktop.lemmatize import build_entries


def test_build_entries_applies_pos_and_frequency_filters():
    tokens = [
        "читаю",
        "читал",
        "книга",
        "книги",
        "быстро",
        "иван",
    ]
    entries = build_entries(
        tokens,
        allowed_pos=frozenset({"noun", "verb"}),
        exclude_proper_nouns=True,
        known_only=True,
        min_frequency=2,
    )

    reduced = {(entry.lemma, entry.pos, entry.frequency) for entry in entries}
    assert reduced == {
        ("читать", "verb", 2),
        ("книга", "noun", 2),
    }


def test_build_entries_excludes_custom_lemmas():
    tokens = ["книга", "книги", "дом", "дома"]
    entries = build_entries(
        tokens,
        excluded_lemmas=frozenset({"дом"}),
        known_only=True,
    )
    lemmas = {entry.lemma for entry in entries}
    assert lemmas == {"книга"}
