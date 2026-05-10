#!/bin/bash
# macOS launcher — double-click to start Russian Vocab Studio.
# Keeps Terminal open and prints why it failed if anything goes wrong.

cd "$(dirname "$0")"
xattr -dr com.apple.quarantine . 2>/dev/null || true

LOG="run_log.txt"
exec > >(tee "$LOG") 2>&1

echo "──────────────────────────────────────────────"
echo "  Russian Vocab Studio — launcher"
echo "  $(date)"
echo "  Folder: $(pwd)"
echo "──────────────────────────────────────────────"

# Look for any working Python 3.10+
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
  echo "ERROR: Python 3.10+ not found."
  echo "    Install it from: https://www.python.org/downloads/macos/"
  echo "    (pick the universal2 / Apple Silicon build)"
  echo
  read -n1 -r -p "Press any key to close…"
  exit 1
fi

VENV=".venv"

# Rebuild venv if it was created with a different Python.
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
    echo "ERROR: failed to create virtualenv."
    read -n1 -r -p "Press any key to close…"
    exit 1
  fi
fi

VENV_PY="$VENV/bin/python"

echo "Checking dependencies (first run can take 3-5 minutes)…"
"$VENV_PY" -m pip install --upgrade pip --quiet 2>/dev/null
if ! "$VENV_PY" -m pip install -r requirements.txt --quiet; then
  echo "ERROR: failed to install dependencies. See messages above."
  read -n1 -r -p "Press any key to close…"
  exit 1
fi

echo "Launching app…"
echo "──────────────────────────────────────────────"
echo

if ! "$VENV_PY" app.py; then
  echo
  echo "──────────────────────────────────────────────"
  echo "ERROR: the app exited with an error."
  echo "    Full log: $(pwd)/$LOG"
  read -n1 -r -p "Press any key to close…"
  exit 1
fi
