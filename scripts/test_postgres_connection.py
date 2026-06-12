# coding: utf-8
"""
Быстрая проверка подключения к postgres из config.yaml.

Запуск:
    python scripts/test_postgres_connection.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.config import load_app_config
from core.db import get_connection
from core.logging.postgres import PostgresLogger


def main() -> None:
    config = load_app_config(ROOT / "config.yaml")
    logging_cfg = config["logging"]

    conn = get_connection(logging_cfg)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1
    finally:
        conn.close()

    logger = PostgresLogger(logging_cfg)
    user_id = logger.allocate_user_id()
    print(f"Подключение OK. Тестовый user_id из sequence: {user_id}")


if __name__ == "__main__":
    main()
