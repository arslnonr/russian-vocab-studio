"""Tokenize Russian text into Cyrillic-only word tokens."""

from __future__ import annotations

import re

_WORD_CANDIDATE_RE = re.compile(r"[^\s\.,!?;:'\"()\[\]{}\-—–…«»]+")
_CYRILLIC_ONLY_RE = re.compile(r"^[а-яёА-ЯЁ]+$")


def tokenize(text: str, min_length: int = 2) -> list[str]:
    tokens: list[str] = []
    for match in _WORD_CANDIDATE_RE.finditer(text):
        word = match.group()
        if not _CYRILLIC_ONLY_RE.match(word):
            continue
        lowered = word.lower()
        if len(lowered) < min_length:
            continue
        tokens.append(lowered)
    return tokens
