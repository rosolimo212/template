# coding: utf-8
"""Проверка подключения к postgres."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.config import load_app_config
from core.db import postgres_connection
from core.logging.postgres import PostgresLogger


def main() -> None:
    config = load_app_config(ROOT / "config.yaml")
    logging_cfg = config["logging"]

    with postgres_connection(logging_cfg) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1

    logger = PostgresLogger(logging_cfg)
    identity = logger.ensure_user("console", "connection-test")
    print("Подключение OK.")
    print(f"  user_id (hash): {identity.user_id}")
    print(f"  internal_user_id: {identity.internal_user_id}")
    print(f"  external_user_id: {identity.external_user_id}")


if __name__ == "__main__":
    main()
