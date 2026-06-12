# coding: utf-8
"""
Логирование в postgres (схема template).

Цель:
    Писать users и events через SQLAlchemy + pandas и psycopg2,
    в стиле weather/data_load.py.

Вход:
    Секция logging из config.yaml.

Выход:
    Записи в template.users и template.events.

Риски:
    При недоступной БД методы выбросят исключение наверх.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd

from core.db import get_connection, get_engine
from core.logging.base import EventLogger


class PostgresLogger(EventLogger):
    """Запись логов в postgres."""

    def __init__(self, logging_config: dict[str, Any]) -> None:
        self.logging_config = logging_config
        self.schema = logging_config["schema"]

    def allocate_user_id(self) -> int:
        """
        Берёт следующий user_id из sequence таблицы template.users.

        :return: новый уникальный user_id
        """
        sequence_name = f"{self.schema}.users_user_id_seq"
        query = f"SELECT nextval(%s)"

        conn = get_connection(self.logging_config)
        try:
            with conn.cursor() as cur:
                cur.execute(query, (sequence_name,))
                row = cur.fetchone()
            conn.commit()
        finally:
            conn.close()

        if row is None:
            raise RuntimeError("postgres не вернул user_id из sequence")

        return int(row[0])

    def upsert_user(
        self,
        user_id: int,
        user_name: str,
        registration_date: datetime,
        registration_channel: str,
        last_active_at: datetime,
        is_paid: bool = False,
        is_trial: bool = False,
        is_active: bool = True,
    ) -> None:
        """
        Создаёт или обновляет пользователя по user_id.

        При повторном вызове с тем же user_id поля перезаписываются.
        """
        table_name = f"{self.schema}.users"
        query = f"""
            INSERT INTO {table_name} (
                user_id,
                user_name,
                registration_date,
                registration_channel,
                last_active_at,
                is_paid,
                is_trial,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                user_name = EXCLUDED.user_name,
                registration_date = EXCLUDED.registration_date,
                registration_channel = EXCLUDED.registration_channel,
                last_active_at = EXCLUDED.last_active_at,
                is_paid = EXCLUDED.is_paid,
                is_trial = EXCLUDED.is_trial,
                is_active = EXCLUDED.is_active
        """

        conn = get_connection(self.logging_config)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        user_id,
                        user_name,
                        registration_date,
                        registration_channel,
                        last_active_at,
                        is_paid,
                        is_trial,
                        is_active,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def log_event(
        self,
        user_id: int,
        event_name: str,
        channel: str,
        event_parameters: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Добавляет строку в template.events через pandas.to_sql.
        """
        event_time = timestamp or datetime.now()
        params_json = None
        if event_parameters is not None:
            params_json = json.dumps(event_parameters, ensure_ascii=False)

        row = {
            "timestamp": event_time,
            "user_id": user_id,
            "event_name": event_name,
            "channel": channel,
            "event_parameters": params_json,
        }
        df = pd.DataFrame([row])

        engine = get_engine(self.logging_config)
        df.to_sql(
            "events",
            con=engine,
            schema=self.schema,
            if_exists="append",
            index=False,
        )
