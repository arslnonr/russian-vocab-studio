"""OCR support built around EasyOCR."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from .app_paths import model_dir

_reader = None


def easyocr_available() -> bool:
    try:
        import easyocr  # noqa: F401
    except ImportError:
        return False
    return True


def ensure_easyocr(log_callback=None):
    global _reader
    if _reader is not None:
        return _reader

    if not easyocr_available():
        raise RuntimeError(
            "EasyOCR is not installed. Install project dependencies before using OCR."
        )

    import easyocr

    if log_callback:
        log_callback(
            "Preparing OCR models. On first use EasyOCR may download its model files automatically."
        )
    _reader = easyocr.Reader(
        ["ru", "en"],
        gpu=False,
        model_storage_directory=str(model_dir()),
        download_enabled=True,
    )
    return _reader


def warm_up(log_callback=None) -> None:
    ensure_easyocr(log_callback=log_callback)


def ocr_pil_image(image: Image.Image, log_callback=None) -> str:
    reader = ensure_easyocr(log_callback=log_callback)
    import numpy as np

    result = reader.readtext(np.array(image), detail=0, paragraph=True)
    return "\n".join(result)


def model_storage_path() -> Path:
    return model_dir()
