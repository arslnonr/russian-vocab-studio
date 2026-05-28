"""Simple per-page text cache."""

from __future__ import annotations

from hashlib import sha1
from pathlib import Path

from .app_paths import page_cache_dir


def document_cache_key(pdf_path: Path) -> str:
    stat = pdf_path.stat()
    digest = sha1()
    digest.update(str(pdf_path.name).encode("utf-8"))
    digest.update(str(stat.st_size).encode("utf-8"))
    digest.update(str(stat.st_mtime_ns).encode("utf-8"))
    with pdf_path.open("rb") as handle:
        digest.update(handle.read(65536))
    return digest.hexdigest()[:16]


def cache_path(pdf_path: Path, *, page_number: int, source: str, dpi: int) -> Path:
    key = document_cache_key(pdf_path)
    path = page_cache_dir() / key
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{source}_dpi{dpi:03d}_page{page_number:04d}.txt"


def read_cached_text(pdf_path: Path, *, page_number: int, source: str, dpi: int) -> str | None:
    path = cache_path(pdf_path, page_number=page_number, source=source, dpi=dpi)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def write_cached_text(
    pdf_path: Path,
    *,
    page_number: int,
    source: str,
    dpi: int,
    text: str,
) -> None:
    path = cache_path(pdf_path, page_number=page_number, source=source, dpi=dpi)
    path.write_text(text, encoding="utf-8")
