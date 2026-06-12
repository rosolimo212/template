#!/usr/bin/env bash
# Тот же порядок настройки postgres на prod/stage VM.
# Отличие только в имени базы: iter_template_prod вместо iter_template_stage.
#
# Перед запуском на VM:
#   1. Замените DB_NAME ниже или передайте через переменную окружения
#   2. Выполните те же шаги: роли → пароль roman → база → схема → tester
#
# Запуск:
#   DB_NAME=iter_template_prod ./scripts/setup_postgres_vm.sh

set -euo pipefail

export DB_NAME="${DB_NAME:-iter_template_prod}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Настройка VM: база ${DB_NAME}"
echo "Шаги 1–2 (роли и пароль roman) — как в setup_postgres_local.sh"
echo ""

# Шаги 1–2: роли — тот же sql/000_setup_roles.sql через postgres OS user
if command -v sudo >/dev/null 2>&1; then
    cat "${ROOT}/sql/000_setup_roles.sql" | (cd /tmp && sudo -u postgres psql -v ON_ERROR_STOP=1)
else
    cat "${ROOT}/sql/000_setup_roles.sql" | (cd /tmp && su - postgres -c "psql -v ON_ERROR_STOP=1")
fi

echo ""
echo "Задайте пароль roman: sudo -u postgres psql → \\password roman"
read -r -p "Enter после задания пароля... " _
read -r -s -p "Пароль roman: " ROMAN_PASSWORD
echo ""
export PGPASSWORD="${ROMAN_PASSWORD}"

psql -h localhost -U roman -d postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
    || psql -h localhost -U roman -d postgres -c "CREATE DATABASE ${DB_NAME} OWNER roman;"

psql -h localhost -U roman -d "${DB_NAME}" -f "${ROOT}/sql/001_init.sql"
psql -h localhost -U roman -d postgres \
    -c "GRANT CONNECT ON DATABASE ${DB_NAME} TO tester;"
psql -h localhost -U roman -d "${DB_NAME}" -f "${ROOT}/sql/002_grants_tester.sql"

echo "VM: база ${DB_NAME} готова."
