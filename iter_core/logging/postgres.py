# coding: utf-8
"""
Логирование в postgres (схема template).

Цель:
    Писать users и events через SQLAlchemy + pandas, как в weather/data_load.py.

Вход:
    Секция logging из config.yaml.

Выход:
    Записи в template.users и template.events.

TODO:
    Реализовать insert/upsert в фазе 2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from iter_core.logging.base import EventLogger


class PostgresLogger(EventLogger):
    """Запись логов в postgres; пока заглушка с in-memory счётчиком user_id."""

    def __init__(self, logging_config: dict[str, Any]) -> None:
        self.logging_config = logging_config
        self._fallback_counter = 0

    def allocate_user_id(self) -> int:
        # TODO: заменить на nextval из postgres sequence в фазе 2.
        self._fallback_counter += 1
        return self._fallback_counter

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
        _ = (
            user_id,
            user_name,
            registration_date,
            registration_channel,
            last_active_at,
            is_paid,
            is_trial,
            is_active,
        )

    def log_event(
        self,
        user_id: int,
        event_name: str,
        channel: str,
        event_parameters: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        _ = (user_id, event_name, channel, event_parameters, timestamp)
