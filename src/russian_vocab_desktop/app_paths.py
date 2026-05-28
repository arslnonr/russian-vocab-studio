"""Application cache and data directories."""

from __future__ import annotations

from pathlib import Path

from platformdirs import PlatformDirs

_DIRS = PlatformDirs(appname="RussianVocabDesktop", appauthor="OpenAI", ensure_exists=True)


def app_cache_dir() -> Path:
    path = Path(_DIRS.user_cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def app_data_dir() -> Path:
    path = Path(_DIRS.user_data_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def page_cache_dir() -> Path:
    path = app_cache_dir() / "page_text"
    path.mkdir(parents=True, exist_ok=True)
    return path


def model_dir() -> Path:
    path = app_data_dir() / "ocr_models"
    path.mkdir(parents=True, exist_ok=True)
    return path
