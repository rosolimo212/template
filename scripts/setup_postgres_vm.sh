#!/usr/bin/env bash
# Обёртка для VM → тот же setup, база communication как на stage.
exec "$(dirname "$0")/setup_postgres.sh" "$@"
