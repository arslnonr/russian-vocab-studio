#!/bin/bash
# macOS launcher — keeps Terminal open and prints WHY it failed.
# Uses PySide6 (Qt) instead of tkinter, so no Tcl/Tk version pain.

cd "$(dirname "$0")"
xattr -dr com.apple.quarantine . 2>/dev/null || true

LOG="run_log.txt"
exec > >(tee "$LOG") 2>&1

echo "──────────────────────────────────────────────"
echo "  Rusça Kelime Stüdyosu — launcher"
echo "  $(date)"
echo "  Folder: $(pwd)"
echo "──────────────────────────────────────────────"

# Look for any working Python 3.10+ — Qt itself doesn't care which one,
# we just need a venv we can install PySide6 into.
CANDIDATES=(
  "/opt/homebrew/bin/python3"
  "/opt/homebrew/bin/python3.12"
  "/opt/homebrew/bin/python3.11"
  "/usr/local/bin/python3"
  "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
  "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
  "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"
  "$(command -v python3)"
  "/usr/bin/python3"
)

PY=""
for cand in "${CANDIDATES[@]}"; do
  [ -z "$cand" ] && continue
  [ -x "$cand" ] || continue
  out=$("$cand" -c "import sys; print(sys.version_info[:2])" 2>&1) || continue
  ver=$("$cand" -c "import sys; print(sys.version_info[0]*100+sys.version_info[1])" 2>/dev/null)
  if [ -n "$ver" ] && [ "$ver" -ge 310 ]; then
    PY="$cand"
    echo "• Using Python: $cand ($("$cand" --version 2>&1))"
    break
  fi
  echo "• Skipping $cand: too old or broken"
done

if [ -z "$PY" ]; then
  echo
  echo "❌  Python 3.10+ bulunamadı."
  echo "    Lütfen şuradan kur: https://www.python.org/downloads/macos/"
  echo "    (universal2 / Apple Silicon uyumlu olan)"
  echo
  read -n1 -r -p "Kapatmak için bir tuşa bas…"
  exit 1
fi

VENV=".venv"

# If a previous run created a venv with a different Python, rebuild it.
if [ -d "$VENV" ]; then
  if [ -x "$VENV/bin/python" ]; then
    venv_real="$(readlink -f "$VENV/bin/python" 2>/dev/null || echo "")"
    py_real="$(readlink -f "$PY" 2>/dev/null || echo "")"
    if [ -n "$venv_real" ] && [ -n "$py_real" ] && [ "$venv_real" != "$py_real" ]; then
      echo "• Existing .venv was built with a different Python — rebuilding."
      rm -rf "$VENV"
    fi
  fi
fi

if [ ! -d "$VENV" ]; then
  echo "Creating virtualenv ($VENV)…"
  if ! "$PY" -m venv "$VENV"; then
    echo "❌  venv oluşturulamadı."
    read -n1 -r -p "Kapatmak için bir tuşa bas…"
    exit 1
  fi
fi

VENV_PY="$VENV/bin/python"

echo "Bağımlılıklar kontrol ediliyor (ilk açılışta birkaç dakika sürebilir)…"
"$VENV_PY" -m pip install --upgrade pip --quiet 2>/dev/null
if ! "$VENV_PY" -m pip install -r requirements.txt --quiet; then
  echo "❌  Bağımlılıklar kurulamadı (yukarıya bak)."
  read -n1 -r -p "Kapatmak için bir tuşa bas…"
  exit 1
fi

echo "Uygulama başlatılıyor…"
echo "──────────────────────────────────────────────"
echo

if ! "$VENV_PY" app.py; then
  echo
  echo "──────────────────────────────────────────────"
  echo "❌  Uygulama hata ile kapandı."
  echo "    Tam log: $(pwd)/$LOG"
  read -n1 -r -p "Kapatmak için bir tuşa bas…"
  exit 1
fi
