#!/usr/bin/env bash
# Обёртка для обратной совместимости → scripts/setup_postgres.sh
exec "$(dirname "$0")/setup_postgres.sh" "$@"
