# Russian Vocab Studio

Extract Russian vocabulary from any PDF, lemmatized and frequency‑counted, exported as a clean CSV ready for Anki, Excel, or your own scripts.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org)
[![Built with PySide6](https://img.shields.io/badge/built%20with-PySide6-41cd52.svg)](https://wiki.qt.io/Qt_for_Python)

UI in **Türkçe · Русский · English** — switch instantly from the top‑right.

---

## Features

- **Real lemmatization** with [pymorphy3](https://github.com/no-plan-cat/pymorphy3) — `идём → идти`, `столицей → столица`
- **Part-of-speech filter** — pick nouns, verbs, adjectives, adverbs, or all
- **Smart filters** — drop proper nouns, drop the 100 most basic Russian words, set min word length and min frequency
- **Custom exclude list** — feed it a `.txt` of lemmas you already know
- **Sort** by descending frequency or proper Cyrillic alphabetical order
- **Export modes** — single CSV, one CSV per part of speech, or both
- **Auto OCR** — falls back to OCR (EasyOCR or Tesseract, optional) when a PDF page has no text layer
- **Drag‑and‑drop**, cancellable extraction, light/minimal UI

---

## Install

### Option 1 — prebuilt (recommended for most people)

Download the latest release for your OS from the [**Releases**](../../releases) page:

- **Windows** → unzip → double‑click `RussianVocabStudio.exe`
- **macOS** → unzip → drag `RussianVocabStudio.app` to Applications

No Python install needed.

### Option 2 — from source

```bash
git clone https://github.com/arslnonr/russian-vocab-studio.git
cd russian-vocab-studio
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Or just double‑click `run.command` (macOS) / `BAŞLAT.bat` (Windows) — the script creates the venv, installs deps, and launches the app on first run.

### Optional — OCR for scanned PDFs

In `requirements.txt`, uncomment one of the OCR backends:

- `easyocr` — deep‑learning, better quality, ~200 MB model download on first use
- `pytesseract` + system `tesseract` with the Russian language pack — lighter

Then in the app, set **Reading mode → OCR**.

---

## Usage

1. Drop a PDF onto the drop zone (or click to browse).
2. Pick a page range, or leave **All pages** ticked.
3. Toggle the part‑of‑speech pills — **only the selected ones** end up in the output.
4. (Optional) Tweak **Min. length** (default 3) and **Min. frequency** (default 2).
5. Choose where the CSV should go and whether to export one combined file or split per POS.
6. Hit **Extract Vocabulary**.

The status chip turns green and the file path appears at the bottom.

### CSV format

| lemma | pos  | frequency |
|-------|------|-----------|
| дом   | noun | 12        |
| идти  | verb | 9         |

`pos` ∈ `{noun, verb, adj, adv, other}`. Both `pos` and `frequency` columns are toggleable.

---

## Architecture

Two clean modules so you can use the engine without the UI:

```
russian-vocab-studio/
├── app.py              # PySide6 GUI — light theme, drag-drop, threaded
├── extractor.py        # Pipeline: PDF → tokens → lemmas → CSV (no Qt deps)
├── translations.py     # TR / RU / EN bundles
├── requirements.txt
├── run.command         # macOS launcher
├── BAŞLAT.bat          # Windows launcher
└── .github/workflows/  # CI builds .exe and .app on every tag
```

Use `extractor.py` as a library:

```python
from pathlib import Path
from extractor import ExtractOptions, extract

result = extract(ExtractOptions(
    pdf_path=Path("kitap.pdf"),
    csv_path=Path("kelimeler.csv"),
    pos_filter={"noun", "verb"},
    min_frequency=3,
    sort_by="frequency",
))
print(f"{len(result.rows)} lemmas → {result.output_paths[0]}")
```

---

## Build native binaries from source

Releases are built automatically by [GitHub Actions](.github/workflows/build.yml) on every `v*` tag — Windows `.exe` and macOS `.app` are uploaded to the matching Release.

To build locally:

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name RussianVocabStudio \
    --collect-data pymorphy3_dicts_ru \
    --hidden-import pymorphy3.opencorpora_dict \
    app.py
```

The bundle ends up in `dist/RussianVocabStudio/` (Windows) or `dist/RussianVocabStudio.app/` (macOS).

---

## Contributing

Issues and PRs welcome. Especially:

- Better default stoplists for different CEFR levels
- Sentence‑context column (one example sentence per lemma)
- Export to `.xlsx`, Anki‑ready format
- Additional UI languages

---

## License

[MIT](LICENSE) © 2026 Onur Arslan

---

<details>
<summary><b>Türkçe — Hızlı Başlangıç</b></summary>

PDF'den Rusça kelimeleri çıkarıp lemma + frekans + kelime türü içeren temiz bir CSV oluşturan minimal masaüstü uygulaması.

### Kurulum

**Hazır paket (önerilen):** [Releases](../../releases) sayfasından sistemine uygun olanı indir:
- Windows: `.zip`'i aç, `RussianVocabStudio.exe`'ye çift tıkla
- macOS: `.zip`'i aç, `RussianVocabStudio.app`'i Uygulamalar'a sürükle

**Kaynak koddan:**
```bash
git clone https://github.com/arslnonr/russian-vocab-studio.git
cd russian-vocab-studio
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Nasıl kullanılır

1. PDF'i sürükle bırak.
2. Sayfa aralığını ve istediğin **Kelime Türleri**'ni seç (yalnız fiil, yalnız isim, vs.).
3. **Filtreler**'den Min. harf sayısı (örn. 3) ve Min. tekrar (örn. 5) ayarla.
4. **Çıktı**'da hedef yolu seç ve "Tek CSV" / "Türlere ayır" seçeneğini belirle.
5. **Kelimeleri Çıkar** butonuna bas.

Sağ üstten arayüz dilini Türkçe ⇄ Русский ⇄ English değiştirebilirsin.

### CSV formatı

`lemma, pos, frequency` — Anki ve Excel ile uyumlu.

</details>
