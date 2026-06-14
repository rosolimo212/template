#!/usr/bin/env bash
# Настройка postgres: база communication + схема template.
# Одинаковые имена на stage (локально) и prod (VM); данные на разных серверах.
#
#   cd /path/to/template
#   chmod +x scripts/setup_postgres.sh
#   ./scripts/setup_postgres.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DB_NAME="${DB_NAME:-communication}"
DB_OWNER="${DB_OWNER:-roman}"
DB_SCHEMA="${DB_SCHEMA:-template}"

if [[ "${EUID}" -eq 0 ]] && id postgres &>/dev/null; then
    AS_POSTGRES() { su - postgres -c "$*"; }
    MAY_SUDO() { "$@"; }
elif command -v sudo >/dev/null 2>&1; then
    AS_POSTGRES() { sudo -u postgres "$@"; }
    MAY_SUDO() { sudo "$@"; }
else
    echo "Нужен sudo или запуск от root."
    exit 1
fi

run_sql_as_postgres() {
    local sql_file="$1"
    cat "${sql_file}" | (cd /tmp && AS_POSTGRES psql -v ON_ERROR_STOP=1)
}

echo "=== Шаг 0. PostgreSQL ==="

if ! command -v psql >/dev/null 2>&1; then
    echo "Устанавливаю postgresql..."
    MAY_SUDO apt-get update
    MAY_SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib
fi

if command -v systemctl >/dev/null 2>&1; then
    MAY_SUDO systemctl enable postgresql
    MAY_SUDO systemctl start postgresql
fi

if ! AS_POSTGRES psql -tAc "SELECT 1" >/dev/null 2>&1; then
    echo "postgres не отвечает. Проверьте: sudo systemctl status postgresql"
    exit 1
fi

echo "=== Шаг 1. Роли root, roman, tester ==="
run_sql_as_postgres "${ROOT}/sql/000_setup_roles.sql"

echo ""
echo "=== Шаг 2. Пароль roman (вручную) ==="
echo "  sudo -u postgres psql"
echo "  \\password roman"
echo ""
read -r -p "Нажмите Enter, когда пароль roman задан... " _

echo ""
read -r -s -p "Введите пароль roman для создания базы и таблиц: " ROMAN_PASSWORD
echo ""

export PGPASSWORD="${ROMAN_PASSWORD}"

echo "=== Шаг 3. База ${DB_NAME} (от ${DB_OWNER}) ==="
EXISTS="$(psql -h localhost -p 5432 -U "${DB_OWNER}" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | tr -d '[:space:]')"
if [[ "${EXISTS}" != "1" ]]; then
    psql -h localhost -p 5432 -U "${DB_OWNER}" -d postgres \
        -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_OWNER};"
else
    echo "База ${DB_NAME} уже существует."
fi

echo "=== Шаг 4. Схема ${DB_SCHEMA} и таблицы (от ${DB_OWNER}) ==="
psql -h localhost -p 5432 -U "${DB_OWNER}" -d "${DB_NAME}" -f "${ROOT}/sql/001_init.sql"
psql -h localhost -p 5432 -U "${DB_OWNER}" -d "${DB_NAME}" -f "${ROOT}/sql/003_unique_channel_external.sql"

echo "=== Шаг 5. Права tester ==="
psql -h localhost -p 5432 -U "${DB_OWNER}" -d postgres \
    -c "GRANT CONNECT ON DATABASE ${DB_NAME} TO tester;"
psql -h localhost -p 5432 -U "${DB_OWNER}" -d "${DB_NAME}" -f "${ROOT}/sql/002_grants_tester.sql"

echo "=== Проверка ==="
psql -h localhost -p 5432 -U "${DB_OWNER}" -d "${DB_NAME}" -c "\dn"
psql -h localhost -p 5432 -U "${DB_OWNER}" -d "${DB_NAME}" -c "\dt ${DB_SCHEMA}.*"

if [[ ! -f config.yaml ]]; then
    echo "Создаю config.yaml..."
    cp config.example.yaml config.yaml
    sed -i "s/password: YOUR_PASSWORD_HERE/password: ${ROMAN_PASSWORD}/" config.yaml
    echo "config.yaml создан. Допишите weatherapi.api_key и telegram.token."
else
    echo "config.yaml уже есть — проверьте logging.database=communication и schema=template."
fi

unset PGPASSWORD

echo ""
echo "=== Готово ==="
echo "База:   ${DB_NAME} (одинаково на stage и prod)"
echo "Схема:  ${DB_SCHEMA} (первая; дальше — по тому же шаблону)"
echo "Таблицы: ${DB_SCHEMA}.users, ${DB_SCHEMA}.events"
echo ""
echo "Проверка:"
echo "  psql -h localhost -U roman -d ${DB_NAME} -c 'SELECT COUNT(*) FROM ${DB_SCHEMA}.users'"
