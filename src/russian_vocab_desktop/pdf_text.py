"""PDF page counting, direct text extraction and OCR fallback."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import fitz
from PIL import Image

from .ocr import ocr_pil_image

_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
_TOKEN_RE = re.compile(r"[А-Яа-яЁё]{2,}")


def get_page_count(pdf_path: Path) -> int:
    with fitz.open(pdf_path) as document:
        return len(document)


def extract_page_text_from_document(
    document,
    page_number: int,
    *,
    mode: str = "auto",
    dpi: int = 220,
    log_callback=None,
) -> tuple[str, str]:
    page = document.load_page(page_number - 1)
    direct_text = page.get_text("text")

    if mode == "text":
        return direct_text, "text"
    if mode == "ocr":
        return _ocr_page(page, dpi=dpi, log_callback=log_callback), "ocr"
    if _has_usable_text_layer(direct_text):
        return direct_text, "text"
    return _ocr_page(page, dpi=dpi, log_callback=log_callback), "ocr"


def extract_page_text(
    pdf_path: Path,
    page_number: int,
    *,
    mode: str = "auto",
    dpi: int = 220,
    log_callback=None,
) -> tuple[str, str]:
    with fitz.open(pdf_path) as document:
        return extract_page_text_from_document(
            document,
            page_number,
            mode=mode,
            dpi=dpi,
            log_callback=log_callback,
        )


def _has_usable_text_layer(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    cyrillic_chars = len(_CYRILLIC_RE.findall(stripped))
    tokens = len(_TOKEN_RE.findall(stripped))
    return cyrillic_chars >= 40 or tokens >= 8


def _ocr_page(page, *, dpi: int, log_callback=None) -> str:
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    image = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
    try:
        return ocr_pil_image(image, log_callback=log_callback)
    finally:
        image.close()
