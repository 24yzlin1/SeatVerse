#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -x "backend/.venv/Scripts/python.exe" ]; then
  PYTHON_BIN="backend/.venv/Scripts/python.exe"
elif [ -x "backend/.venv/bin/python" ]; then
  PYTHON_BIN="backend/.venv/bin/python"
elif [ -n "${PYTHON:-}" ]; then
  PYTHON_BIN="$PYTHON"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "python interpreter not found; run 'uv sync' in backend first" >&2
  exit 2
fi

exec "$PYTHON_BIN" scripts/scan_banned.py "$@"
