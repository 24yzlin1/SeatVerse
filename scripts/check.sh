#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> frontend check"
(cd frontend && npm run check)

echo "==> frontend lint"
(cd frontend && npm run lint)

echo "==> frontend build"
(cd frontend && npm run build)

echo "==> backend mypy"
(cd backend && uv run poe check)

echo "==> backend pytest"
set +e
(cd backend && uv run poe test)
status=$?
set -e
if [ "$status" -ne 0 ] && [ "$status" -ne 5 ]; then
  echo "backend pytest failed with exit code $status" >&2
  exit "$status"
fi

echo "ALL GREEN"
