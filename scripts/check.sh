#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> frontend check"
(cd frontend-alt && npm run check)

echo "==> frontend lint"
(cd frontend-alt && npm run lint)

echo "==> frontend build"
(cd frontend-alt && npm run build)

echo "==> banned-item scan"
bash scripts/scan_banned.sh

echo "==> sync endpoint scan"
(cd backend && uv run python ../scripts/scan_sync_endpoints.py)

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
