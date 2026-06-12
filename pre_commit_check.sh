#!/usr/bin/env bash
# Проверки перед коммитом: слой 1 (pytest) + слой 2 (business_checks).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

python -m pytest tests/ -q
python business_checks.py

echo "pre_commit_check: OK"
