#!/usr/bin/env bash
# Миграция схемы id: старый BIGINT user_id -> hash user_id + internal + external.
#
#   cd /home/roman/python/kotelok/template
#   chmod +x scripts/migrate_user_ids.sh
#   ./scripts/migrate_user_ids.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_NAME="${DB_NAME:-iter_template_stage}"
DB_USER="${DB_USER:-roman}"

echo "=== Диагностика ДО миграции ==="
psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -f "${ROOT}/sql/000_diagnose_schema.sql"

echo ""
echo "=== Шаг 1: pgcrypto (от postgres) ==="
if command -v sudo >/dev/null 2>&1; then
    cat "${ROOT}/sql/002a_pgcrypto.sql" | (cd /tmp && sudo -u postgres psql -d "${DB_NAME}")
else
    echo "Запустите вручную от postgres:"
    echo "  psql -d ${DB_NAME} -f ${ROOT}/sql/002a_pgcrypto.sql"
fi

echo ""
echo "=== Шаг 2: миграция (от ${DB_USER}) ==="
psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -f "${ROOT}/sql/002_migrate_user_ids.sql"

echo ""
echo "=== Диагностика ПОСЛЕ миграции ==="
psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -f "${ROOT}/sql/000_diagnose_schema.sql"

echo ""
echo "Готово."
