"""Orchestrate the PDF extraction workflow."""

from __future__ import annotations

from pathlib import Path
import threading

import fitz

from .basic_vocab import DEFAULT_BASIC_LEMMAS
from .cache import read_cached_text, write_cached_text
from .export import export_entries
from .lemmatize import build_entries
from .models import ExtractionOptions, ExtractionSummary, ProgressUpdate
from .pdf_text import extract_page_text_from_document, get_page_count
from .tokenize import tokenize


def run_extraction(
    pdf_path: Path,
    output_path: Path,
    options: ExtractionOptions,
    *,
    progress_callback=None,
    log_callback=None,
    cancel_event: threading.Event | None = None,
) -> ExtractionSummary:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    total_pages = get_page_count(pdf_path)
    start_page, end_page = _validate_page_range(
        total_pages,
        options.start_page,
        options.end_page,
    )
    page_numbers = list(range(start_page, end_page + 1))
    page_texts: list[str] = []
    text_pages = 0
    ocr_pages = 0

    _emit_progress(
        progress_callback,
        "prepare",
        0,
        len(page_numbers),
        f"Preparing {len(page_numbers)} page(s).",
    )

    with fitz.open(pdf_path) as document:
        for index, page_number in enumerate(page_numbers, start=1):
            _ensure_not_cancelled(cancel_event)
            text, source = _load_page_text(
                document,
                pdf_path,
                page_number=page_number,
                options=options,
                log_callback=log_callback,
            )
            page_texts.append(text)
            if source == "ocr":
                ocr_pages += 1
                _log(log_callback, f"Page {page_number}: OCR")
            else:
                text_pages += 1
                _log(log_callback, f"Page {page_number}: direct text")
            _emit_progress(
                progress_callback,
                "pages",
                index,
                len(page_numbers),
                f"Processed page {page_number}/{end_page}.",
            )

    _ensure_not_cancelled(cancel_event)
    _log(log_callback, "Tokenizing extracted text.")

    tokens: list[str] = []
    for text in page_texts:
        tokens.extend(tokenize(text, min_length=options.min_length))

    excluded_lemmas = _build_excluded_lemma_set(options.custom_exclude_path)
    if options.exclude_basic_lemmas:
        excluded_lemmas |= DEFAULT_BASIC_LEMMAS

    _log(log_callback, f"Applying filters to {len(tokens)} token(s).")

    entries = build_entries(
        tokens,
        allowed_pos=options.allowed_pos,
        exclude_proper_nouns=options.exclude_proper_nouns,
        strict=options.strict,
        known_only=options.known_only,
        min_frequency=options.min_frequency,
        excluded_lemmas=frozenset(excluded_lemmas),
    )

    _ensure_not_cancelled(cancel_event)
    _emit_progress(progress_callback, "export", 0, 1, "Writing output files.")
    output_files = export_entries(
        entries,
        output_path,
        export_mode=options.export_mode,
        include_frequency=options.include_frequency,
        include_pos=options.include_pos,
        include_header=options.include_header,
        sort_mode=options.sort_mode,
    )
    _emit_progress(progress_callback, "export", 1, 1, "Done.")

    return ExtractionSummary(
        total_pages=total_pages,
        processed_pages=len(page_numbers),
        text_pages=text_pages,
        ocr_pages=ocr_pages,
        kept_lemmas=len(entries),
        output_files=output_files,
    )


def _load_page_text(
    document,
    pdf_path: Path,
    *,
    page_number: int,
    options: ExtractionOptions,
    log_callback=None,
):
    if options.use_cache:
        if options.text_mode in {"text", "auto"}:
            cached_text = read_cached_text(pdf_path, page_number=page_number, source="text", dpi=72)
            if cached_text is not None:
                if options.text_mode == "text":
                    return cached_text, "text"
                if _is_good_auto_text(cached_text):
                    return cached_text, "text"
        if options.text_mode in {"ocr", "auto"}:
            cached_ocr = read_cached_text(
                pdf_path,
                page_number=page_number,
                source="ocr",
                dpi=options.dpi,
            )
            if cached_ocr is not None:
                return cached_ocr, "ocr"

    text, source = extract_page_text_from_document(
        document,
        page_number,
        mode=options.text_mode,
        dpi=options.dpi,
        log_callback=log_callback,
    )
    if options.use_cache:
        cache_dpi = 72 if source == "text" else options.dpi
        write_cached_text(
            pdf_path,
            page_number=page_number,
            source=source,
            dpi=cache_dpi,
            text=text,
        )
    return text, source


def _is_good_auto_text(text: str) -> bool:
    stripped = text.strip()
    return len(stripped) >= 40


def _build_excluded_lemma_set(custom_path: Path | None) -> set[str]:
    if custom_path is None:
        return set()
    if not custom_path.exists():
        raise FileNotFoundError(f"Custom exclude list not found: {custom_path}")
    content = custom_path.read_text(encoding="utf-8")
    return {line.strip().lower() for line in content.splitlines() if line.strip()}


def _validate_page_range(total_pages: int, start_page: int, end_page: int | None) -> tuple[int, int]:
    if start_page < 1:
        raise ValueError("Start page must be at least 1.")
    effective_end = total_pages if end_page is None else end_page
    if effective_end < start_page:
        raise ValueError("End page must be greater than or equal to start page.")
    if effective_end > total_pages:
        raise ValueError(f"End page exceeds document length ({total_pages}).")
    return start_page, effective_end


def _emit_progress(callback, stage: str, current: int, total: int, message: str) -> None:
    if callback:
        callback(ProgressUpdate(stage=stage, current=current, total=total, message=message))


def _log(callback, message: str) -> None:
    if callback:
        callback(message)


def _ensure_not_cancelled(cancel_event: threading.Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Extraction cancelled.")
