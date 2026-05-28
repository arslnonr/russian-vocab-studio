"""Russian lemmatization and filtering helpers."""

from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

import pymorphy3

from .models import ALL_POS_GROUPS, LemmaEntry, PosGroup

_morph = pymorphy3.MorphAnalyzer()
_PROPER_NOUN_TAGS = frozenset({"Surn", "Name", "Patr", "Geox", "Orgn"})
_VERB_TAGS = frozenset({"VERB", "INFN"})
_ADJECTIVE_TAGS = frozenset({"ADJF", "ADJS", "COMP"})
_ADVERB_TAGS = frozenset({"ADVB"})


@lru_cache(maxsize=50000)
def _best_parse(token: str):
    parses = _morph.parse(token)
    return parses[0] if parses else None


def pos_group_for_token(token: str) -> PosGroup:
    parse = _best_parse(token)
    if parse is None:
        return "other"
    pos = parse.tag.POS
    if pos == "NOUN":
        return "noun"
    if pos in _VERB_TAGS:
        return "verb"
    if pos in _ADJECTIVE_TAGS:
        return "adjective"
    if pos in _ADVERB_TAGS:
        return "adverb"
    return "other"


def is_proper_noun(token: str) -> bool:
    parse = _best_parse(token)
    if parse is None:
        return False
    return bool(_PROPER_NOUN_TAGS & parse.tag.grammemes)


def lemmatize_token(token: str, strict: bool = False, known_only: bool = False) -> str | None:
    parse = _best_parse(token)
    if parse is None:
        return None if (strict or known_only) else token
    if known_only and not parse.is_known:
        return None
    return parse.normal_form


def build_entries(
    tokens: list[str],
    *,
    allowed_pos: frozenset[PosGroup] = frozenset(ALL_POS_GROUPS),
    exclude_proper_nouns: bool = False,
    strict: bool = False,
    known_only: bool = False,
    min_frequency: int = 1,
    excluded_lemmas: frozenset[str] = frozenset(),
) -> list[LemmaEntry]:
    counts: dict[tuple[str, PosGroup], int] = defaultdict(int)

    for token in tokens:
        if exclude_proper_nouns and is_proper_noun(token):
            continue
        lemma = lemmatize_token(token, strict=strict, known_only=known_only)
        if lemma is None or lemma in excluded_lemmas:
            continue
        pos = pos_group_for_token(token)
        if pos not in allowed_pos:
            continue
        counts[(lemma, pos)] += 1

    entries = [
        LemmaEntry(lemma=lemma, frequency=freq, pos=pos)
        for (lemma, pos), freq in counts.items()
        if freq >= min_frequency
    ]
    return entries


def cyrillic_sort_key(word: str) -> tuple[int, ...]:
    order = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    return tuple(order.index(ch) if ch in order else len(order) for ch in word)
