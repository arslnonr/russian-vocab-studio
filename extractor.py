"""
Russian Vocab Studio – extraction engine

Pipeline: PDF -> Cyrillic tokens -> pymorphy3 lemmas -> filtered & counted -> CSV.

Required:
    pip install pymupdf pymorphy3 pymorphy3-dicts-ru
Optional (OCR for scanned PDFs):
    pip install easyocr            # heavy (~PyTorch); deep-learning OCR
    – or –
    pip install pytesseract pillow # lighter, needs system 'tesseract' + rus pack
"""

from __future__ import annotations

import csv
import io
import re
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

# Soft imports — surfaced as readable errors in the UI.
try:
    import fitz  # type: ignore  # pymupdf
except ImportError:  # pragma: no cover
    fitz = None  # type: ignore[assignment]

try:
    import pymorphy3  # type: ignore
except ImportError:  # pragma: no cover
    pymorphy3 = None  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_WORD_CANDIDATE_RE = re.compile(r'[^\s\.,!?;:\'"()\[\]{}\-—–…«»]+')
_CYRILLIC_ONLY_RE = re.compile(r"^[а-яёА-ЯЁ]+$")
_CYRILLIC_ANY_RE = re.compile(r"[А-Яа-яЁё]")
_CYRILLIC_TOKEN_RE = re.compile(r"[А-Яа-яЁё]{2,}")

_NOUN_TAGS = frozenset({"NOUN"})
_VERB_TAGS = frozenset({"VERB", "INFN"})
_ADJ_TAGS = frozenset({"ADJF", "ADJS", "COMP"})
_ADV_TAGS = frozenset({"ADVB"})
_PROPER_NOUN_TAGS = frozenset({"Name", "Surn", "Patr", "Orgn", "Geox"})

POS_GROUPS: tuple[str, ...] = ("noun", "verb", "adj", "adv", "other")

CYRILLIC_ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"


def cyrillic_sort_key(word: str) -> tuple[int, ...]:
    table = {ch: i for i, ch in enumerate(CYRILLIC_ALPHABET)}
    other = len(CYRILLIC_ALPHABET)
    return tuple(table.get(ch, other) for ch in word.lower())


# Built-in stoplist — taken from the original RussianVocabDesktop project so
# behaviour matches.
DEFAULT_BASIC_LEMMAS: frozenset[str] = frozenset(
    """
    а без более бы был быть в вам вас весь вот всегда все вы где да даже
    для до его еще ее же за здесь и из или им их к как какой когда кто ли
    меня между мне мой можно мы на над надо наш не него нее нет ни но него
    о об один она они оно от очень по под пока после потому почти при про
    разве раз с сам свой сейчас сказать совсем твой тем теперь то тогда
    того тоже только тот ты у уже хорошо хоть человек чего чем через что
    чтоб чтобы эта эти это этот я
    """.split()
)


# --------------------------------------------------------------------------- #
# Configuration & result types
# --------------------------------------------------------------------------- #


@dataclass
class ExtractOptions:
    pdf_path: Path
    csv_path: Path
    page_start: int = 1
    page_end: int | None = None
    pos_filter: set[str] = field(
        default_factory=lambda: {"noun", "verb", "adj", "adv"}
    )
    remove_proper_nouns: bool = True
    remove_basic_words: bool = True
    custom_exclude_path: Path | None = None
    min_length: int = 3
    min_frequency: int = 1
    sort_by: str = "frequency"
    include_frequency: bool = True
    include_pos: bool = True
    include_header: bool = True
    export_mode: str = "single_csv"
    reading_mode: str = "auto"
    ocr_dpi: int = 150                # 150 is enough for printed text and 2x faster than 220
    save_searchable_pdf: bool = True  # write a *_searchable.pdf alongside the CSV when OCR runs


@dataclass
class WordRow:
    lemma: str
    pos: str
    frequency: int


@dataclass
class ExtractResult:
    rows: list[WordRow]
    total_tokens: int
    pages_processed: int
    output_paths: list[Path]
    cyrillic_chars: int = 0      # raw Cyrillic chars seen in the PDF text
    raw_tokens: int = 0          # tokens before any filtering
    searchable_pdf_path: Path | None = None
    ocr_device: str = "cpu"      # which device EasyOCR ran on (cpu / cuda / mps)


class ExtractError(Exception):
    def __init__(self, key: str, **fmt):
        super().__init__(key)
        self.key = key
        self.fmt = fmt


class Cancelled(Exception):
    pass


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #


ProgressCb = Callable[[float, str], None]


def _check_deps() -> None:
    if fitz is None:
        raise ExtractError("msg_pymupdf_missing")
    if pymorphy3 is None:
        raise ExtractError("msg_pymorphy_missing")


def _check_cancel(ev: threading.Event | None) -> None:
    if ev is not None and ev.is_set():
        raise Cancelled()


def _has_usable_text_layer(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    cyrillic_chars = len(_CYRILLIC_ANY_RE.findall(stripped))
    tokens = len(_CYRILLIC_TOKEN_RE.findall(stripped))
    return cyrillic_chars >= 40 and tokens >= 8


_easyocr_reader = None
_easyocr_device: str = "cpu"


def _detect_torch_device() -> str:
    """Pick fastest available torch device: cuda > mps > cpu."""
    try:
        import torch  # type: ignore
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _get_easyocr(on_progress: "ProgressCb | None" = None):
    """Create / cache an EasyOCR reader on the fastest available device."""
    global _easyocr_reader, _easyocr_device
    if _easyocr_reader is not None:
        return _easyocr_reader

    if on_progress is not None:
        on_progress(-1.0, "ocr_init")

    import easyocr  # type: ignore

    device = _detect_torch_device()
    _easyocr_device = device

    if device == "cuda":
        # EasyOCR honours gpu=True for CUDA.
        _easyocr_reader = easyocr.Reader(["ru", "en"], gpu=True, verbose=False)
    elif device == "mps":
        # EasyOCR doesn't natively support MPS — load on CPU then move the
        # networks to MPS for ~5-10× speed-up on Apple Silicon.
        _easyocr_reader = easyocr.Reader(["ru", "en"], gpu=False, verbose=False)
        try:
            import torch  # type: ignore
            mps = torch.device("mps")
            if hasattr(_easyocr_reader, "detector") and _easyocr_reader.detector is not None:
                _easyocr_reader.detector = _easyocr_reader.detector.to(mps)
            if hasattr(_easyocr_reader, "recognizer") and _easyocr_reader.recognizer is not None:
                _easyocr_reader.recognizer = _easyocr_reader.recognizer.to(mps)
            _easyocr_reader.device = mps
        except Exception:
            _easyocr_device = "cpu"
    else:
        _easyocr_reader = easyocr.Reader(["ru", "en"], gpu=False, verbose=False)

    return _easyocr_reader


def current_ocr_device() -> str:
    return _easyocr_device


def _ocr_page(page, dpi: int,
              on_progress: "ProgressCb | None" = None,
              ) -> tuple[str, list[tuple[list, str, float]], tuple[int, int]]:
    """
    Return (text, raw_results, (img_width, img_height)) for one page.

    raw_results is the list of (bbox, text, confidence) tuples — used later
    to build a searchable PDF. Empty list if OCR didn't run.
    """
    try:
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        png_bytes = pix.tobytes("png")
        img_size = (pix.width, pix.height)
    except Exception:
        return "", [], (0, 0)

    # EasyOCR (preferred, GPU-accelerated)
    try:
        import easyocr  # type: ignore  # noqa: F401
        import numpy as np  # type: ignore
        from PIL import Image  # type: ignore

        reader = _get_easyocr(on_progress)
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        if on_progress is not None:
            on_progress(-2.0, "ocr_running")
        results = reader.readtext(np.array(img), detail=1, paragraph=False)
        # results: list of (bbox, text, conf)
        text = "\n".join(r[1] for r in results if r and len(r) >= 2)
        return text, results, img_size
    except ImportError:
        pass
    except Exception:
        pass

    # Tesseract fallback
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore

        img = Image.open(io.BytesIO(png_bytes))
        return pytesseract.image_to_string(img, lang="rus"), [], img_size
    except Exception:
        return "", [], img_size


def _read_pdf_text(opts: ExtractOptions, on_progress: ProgressCb,
                   cancel: threading.Event | None
                   ) -> tuple[str, int, dict[int, tuple[list, tuple[int, int]]]]:
    """
    Read every requested page. For each page that goes through OCR, we keep
    the raw `(bbox, text, confidence)` list and the rasterised image size so
    that we can later build a searchable PDF.

    Returns: (concatenated_text, pages_processed, per_page_ocr_data)
        per_page_ocr_data[page_index] = (results, (img_w, img_h))
    """
    assert fitz is not None
    doc = fitz.open(opts.pdf_path)
    try:
        total = doc.page_count
        start = max(1, opts.page_start) - 1
        end = total if opts.page_end is None else min(total, opts.page_end)
        if end <= start:
            end = start + 1

        chunks: list[str] = []
        ocr_pages: dict[int, tuple[list, tuple[int, int]]] = {}
        pages_total = end - start

        for i in range(start, end):
            _check_cancel(cancel)
            page = doc.load_page(i)
            text = ""
            if opts.reading_mode in ("auto", "text"):
                text = page.get_text("text") or ""

            need_ocr = (
                opts.reading_mode == "ocr"
                or (opts.reading_mode == "auto" and not _has_usable_text_layer(text))
            )

            if need_ocr:
                # Tell UI which page we're OCRing.
                on_progress(-3.0, f"ocr_page:{i - start + 1}/{pages_total}")
                ocr_text, ocr_results, img_size = _ocr_page(page, opts.ocr_dpi, on_progress)
                if ocr_text:
                    text = ocr_text
                if ocr_results:
                    ocr_pages[i] = (ocr_results, img_size)

            chunks.append(text)
            done = (i - start + 1) / max(1, pages_total)
            on_progress(0.05 + done * 0.5, f"page {i + 1}/{end}")

        return "\n".join(chunks), pages_total, ocr_pages
    finally:
        doc.close()


def _tokenize(text: str, min_length: int) -> list[str]:
    out: list[str] = []
    for m in _WORD_CANDIDATE_RE.finditer(text):
        w = m.group()
        if not _CYRILLIC_ONLY_RE.match(w):
            continue
        low = w.lower()
        if len(low) < min_length:
            continue
        out.append(low)
    return out


def _classify_pos(parse) -> str:
    pos = str(parse.tag.POS) if parse.tag.POS else ""
    if pos in _NOUN_TAGS:
        return "noun"
    if pos in _VERB_TAGS:
        return "verb"
    if pos in _ADJ_TAGS:
        return "adj"
    if pos in _ADV_TAGS:
        return "adv"
    return "other"


def _is_proper_noun(parse) -> bool:
    return bool(_PROPER_NOUN_TAGS & parse.tag.grammemes)


def _load_custom_exclude(path: Path | None) -> set[str]:
    if path is None:
        return set()
    if not path.exists():
        raise ExtractError("msg_custom_exclude_missing", path=str(path))
    return {line.strip().lower() for line in path.read_text("utf-8").splitlines()
            if line.strip()}


def extract(opts: ExtractOptions,
            on_progress: ProgressCb | None = None,
            cancel: threading.Event | None = None) -> ExtractResult:
    """Run the extraction. Raises ExtractError or Cancelled."""
    progress: ProgressCb = on_progress or (lambda *_: None)
    _check_deps()

    progress(0.02, "init")
    text, pages, ocr_pages = _read_pdf_text(opts, progress, cancel)

    progress(0.6, "tokenize")
    _check_cancel(cancel)
    cyrillic_chars_seen = len(_CYRILLIC_ANY_RE.findall(text))
    raw_tokens = sum(1 for _ in _CYRILLIC_TOKEN_RE.finditer(text))
    tokens = _tokenize(text, opts.min_length)

    excluded = _load_custom_exclude(opts.custom_exclude_path)
    if opts.remove_basic_words:
        excluded |= DEFAULT_BASIC_LEMMAS

    progress(0.65, "morph")
    morph = pymorphy3.MorphAnalyzer()  # type: ignore[union-attr]
    counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    cache: dict[str, tuple[str, str] | None] = {}

    n = max(1, len(tokens))
    for idx, tok in enumerate(tokens):
        if idx % 1000 == 0:
            _check_cancel(cancel)
            progress(0.65 + (idx / n) * 0.25, f"morph {idx}/{n}")

        if tok in cache:
            entry = cache[tok]
        else:
            parses = morph.parse(tok)
            if not parses:
                cache[tok] = None
                continue
            best = parses[0]
            if opts.remove_proper_nouns and _is_proper_noun(best):
                cache[tok] = None
                continue
            lemma = (best.normal_form or tok).replace("ё", "е")
            pos = _classify_pos(best)
            entry = (lemma, pos)
            cache[tok] = entry

        if entry is None:
            continue
        lemma, pos = entry

        if pos not in opts.pos_filter:
            continue
        if lemma in excluded:
            continue
        counts[(lemma, pos)] += 1

    progress(0.92, "build rows")
    rows = [
        WordRow(lemma=l, pos=p, frequency=f)
        for (l, p), f in counts.items()
        if f >= opts.min_frequency
    ]

    if opts.sort_by == "alpha":
        rows.sort(key=lambda r: cyrillic_sort_key(r.lemma))
    else:
        rows.sort(key=lambda r: (-r.frequency, cyrillic_sort_key(r.lemma)))

    progress(0.94, "write csv")
    output_paths = _write_outputs(rows, opts)

    # Build a searchable PDF if requested AND OCR actually ran.
    searchable_path: Path | None = None
    if opts.save_searchable_pdf and ocr_pages:
        progress(0.97, "searchable_pdf")
        on_progress(-4.0, "searchable_pdf")
        try:
            searchable_path = _save_searchable_pdf(opts.pdf_path, ocr_pages, opts)
        except Exception:
            # Don't fail the whole extraction over the PDF rebuild
            searchable_path = None

    progress(1.0, "done")

    return ExtractResult(
        rows=rows,
        total_tokens=len(tokens),
        pages_processed=pages,
        output_paths=output_paths,
        cyrillic_chars=cyrillic_chars_seen,
        raw_tokens=raw_tokens,
        searchable_pdf_path=searchable_path,
        ocr_device=current_ocr_device() if ocr_pages else "cpu",
    )


def _save_searchable_pdf(
    src_pdf: Path,
    ocr_pages: dict[int, tuple[list, tuple[int, int]]],
    opts: ExtractOptions,
) -> Path:
    """
    Re-open the original PDF and overlay invisible text on every OCRd page so
    the result is selectable / searchable. Writes <stem>_searchable.pdf next
    to the CSV output.
    """
    assert fitz is not None

    out_path = opts.csv_path.with_name(f"{opts.csv_path.stem}_searchable.pdf")
    if out_path.suffix.lower() != ".pdf":
        out_path = out_path.with_suffix(".pdf")

    doc = fitz.open(src_pdf)
    try:
        for page_idx, (results, (img_w, img_h)) in ocr_pages.items():
            page = doc.load_page(page_idx)
            pw, ph = page.rect.width, page.rect.height
            if img_w == 0 or img_h == 0:
                continue
            sx = pw / img_w
            sy = ph / img_h

            for entry in results:
                if not entry or len(entry) < 2:
                    continue
                bbox, text = entry[0], entry[1]
                if not text or not str(text).strip():
                    continue
                try:
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                except (TypeError, IndexError):
                    continue
                x0, x1 = min(xs) * sx, max(xs) * sx
                y0, y1 = min(ys) * sy, max(ys) * sy
                rect = fitz.Rect(x0, y0, x1, y1)
                if rect.is_empty or rect.is_infinite:
                    continue
                # Pick a font size that fills the box height.
                box_h = max(1.0, y1 - y0)
                font_size = max(4.0, box_h * 0.85)
                try:
                    page.insert_textbox(
                        rect,
                        str(text),
                        fontsize=font_size,
                        fontname="helv",
                        color=(0, 0, 0),
                        render_mode=3,        # invisible — selectable but not drawn
                        align=0,
                    )
                except Exception:
                    # Some fonts/encodings reject Cyrillic via insert_textbox;
                    # fall back to a single insert_text call which is more lenient.
                    try:
                        page.insert_text(
                            (rect.x0, rect.y0 + font_size),
                            str(text),
                            fontsize=font_size,
                            color=(0, 0, 0),
                            render_mode=3,
                        )
                    except Exception:
                        pass

        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(out_path, garbage=4, deflate=True)
    finally:
        doc.close()
    return out_path


# --------------------------------------------------------------------------- #
# CSV writers
# --------------------------------------------------------------------------- #


def _write_csv(path: Path, rows: Iterable[WordRow], opts: ExtractOptions) -> Path:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise ExtractError("msg_csv_perm_denied", path=str(path))

    headers = ["lemma"]
    if opts.include_pos:
        headers.append("pos")
    if opts.include_frequency:
        headers.append("frequency")

    try:
        fh = path.open("w", encoding="utf-8-sig", newline="")
    except PermissionError:
        # Most common cause on Windows: the file is open in Excel.
        raise ExtractError("msg_csv_locked", path=str(path))
    except OSError as e:
        raise ExtractError("msg_csv_write_failed", path=str(path), err=str(e))

    try:
        writer = csv.writer(fh)
        if opts.include_header:
            writer.writerow(headers)
        for r in rows:
            row: list = [r.lemma]
            if opts.include_pos:
                row.append(r.pos)
            if opts.include_frequency:
                row.append(r.frequency)
            writer.writerow(row)
    finally:
        fh.close()
    return path


def _write_outputs(rows: list[WordRow], opts: ExtractOptions) -> list[Path]:
    if opts.export_mode == "single_csv":
        return [_write_csv(opts.csv_path, rows, opts)]

    grouped: defaultdict[str, list[WordRow]] = defaultdict(list)
    for r in rows:
        grouped[r.pos].append(r)

    written: list[Path] = []
    if opts.export_mode == "both":
        written.append(_write_csv(opts.csv_path, rows, opts))

    base = opts.csv_path.with_suffix("")
    for pos, items in grouped.items():
        path = base.with_name(f"{base.name}_{pos}.csv")
        written.append(_write_csv(path, items, opts))
    return written
