"""Build a desktop bundle with PyInstaller."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "launch.py"


def main() -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "RussianVocabStudio",
        "--paths",
        str(ROOT / "src"),
        "--collect-all",
        "easyocr",
        "--collect-all",
        "docx",
        "--collect-all",
        "pymorphy3",
        "--collect-all",
        "pymorphy3_dicts_ru",
        str(ENTRYPOINT),
    ]
    subprocess.run(command, check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
