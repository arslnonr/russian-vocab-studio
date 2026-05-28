"""Shared data models for the application."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

PosGroup = Literal["noun", "verb", "adjective", "adverb", "other"]
TextMode = Literal["auto", "text", "ocr"]
SortMode = Literal["frequency_desc", "alphabetical"]
ExportMode = Literal["single_file", "separate_by_pos", "both"]

ALL_POS_GROUPS: tuple[PosGroup, ...] = ("noun", "verb", "adjective", "adverb", "other")
POS_LABELS: dict[PosGroup, str] = {
    "noun": "nouns",
    "verb": "verbs",
    "adjective": "adjectives",
    "adverb": "adverbs",
    "other": "other",
}


@dataclass(frozen=True)
class ExtractionOptions:
    start_page: int = 1
    end_page: int | None = None
    text_mode: TextMode = "auto"
    dpi: int = 220
    min_length: int = 2
    min_frequency: int = 2
    exclude_proper_nouns: bool = True
    known_only: bool = True
    strict: bool = False
    exclude_basic_lemmas: bool = True
    custom_exclude_path: Path | None = None
    allowed_pos: frozenset[PosGroup] = field(
        default_factory=lambda: frozenset(ALL_POS_GROUPS)
    )
    include_frequency: bool = True
    include_pos: bool = True
    include_header: bool = True
    sort_mode: SortMode = "frequency_desc"
    export_mode: ExportMode = "single_file"
    use_cache: bool = True


@dataclass(frozen=True)
class LemmaEntry:
    lemma: str
    frequency: int
    pos: PosGroup


@dataclass(frozen=True)
class ProgressUpdate:
    stage: str
    current: int
    total: int
    message: str


@dataclass(frozen=True)
class ExtractionSummary:
    total_pages: int
    processed_pages: int
    text_pages: int
    ocr_pages: int
    kept_lemmas: int
    output_files: tuple[Path, ...]


ProgressCallback = Callable[[ProgressUpdate], None]
LogCallback = Callable[[str], None]
