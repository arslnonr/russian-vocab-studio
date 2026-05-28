# Russian Vocab Studio

Cross-platform desktop app for extracting Russian lemma lists from PDF files.

## What it does

- Accepts PDF files via drag-and-drop.
- Lets you choose a page range.
- Reads normal PDFs directly without OCR when a text layer exists.
- Falls back to OCR for scanned pages.
- Exports CSV or Word files, either as one file, separate files by word class, or both.
- Sorts alphabetically or by frequency.
- Can remove proper nouns.
- Can keep only dictionary-known words.
- Can drop built-in basic starter words.
- Can apply a custom exclude list from a `.txt` file.
- Can export only nouns, verbs, adjectives, adverbs, or any combination.

## Why this version is better than the original CLI flow

- No `poppler` dependency.
- No system-wide `tesseract` install.
- Digital PDFs are much faster because the app reads embedded text directly.
- OCR is only used when needed.
- EasyOCR downloads its model automatically on first OCR use, so the app can prepare itself on demand.

## Stack

- GUI: `PySide6`
- Direct PDF reading: `PyMuPDF`
- OCR fallback: `EasyOCR`
- Lemmatization and POS filtering: `pymorphy3`
- Word export: `python-docx`
- Packaging: `PyInstaller`

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,build]"
python -m russian_vocab_desktop
```

Run tests:

```bash
PYTHONPATH=src pytest
```

## Packaging

Build a local desktop bundle:

```bash
pip install -e ".[build]"
python scripts/build_app.py
```

PyInstaller produces a native bundle for the current operating system only. The included GitHub Actions workflow builds:

- a macOS `.app` bundle on `macos-latest`
- a Windows desktop bundle on `windows-latest`

Artifacts are uploaded automatically by the workflow.

## First-run behavior

- For normal text PDFs: no network is required.
- For scanned PDFs: the first OCR run may download EasyOCR model files.
- After the first OCR run, the downloaded model files are reused from the user data directory.

## Output

Single-file mode writes one CSV or Word file.

Separate mode writes files such as:

- `book_lemmas_nouns.csv`
- `book_lemmas_verbs.csv`
- `book_lemmas_adjectives.csv`
- `book_lemmas_adverbs.csv`
- `book_lemmas_other.csv`

If you choose `.docx` as the output extension, the app writes the same file set as Word documents instead.

## Current limitation

If you want final binaries for both macOS and Windows, build each one on its own platform or let GitHub Actions build both artifacts for you.
