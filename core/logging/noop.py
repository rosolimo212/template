# coding: utf-8
"""
Логгер-заглушка при выключенном postgres.

Цель:
    Не писать в БД, но выдавать user_id через локальный json-счётчик.

Риски:
    Счётчик в data/user_counter.json рассчитан на один локальный процесс.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging.base import EventLogger

DEFAULT_COUNTER_PATH = Path("data/user_counter.json")


class NoopLogger(EventLogger):
    """Логирование отключено; user_id берётся из локального файла-счётчика."""

    def __init__(self, counter_path: str | Path = DEFAULT_COUNTER_PATH) -> None:
        self.counter_path = Path(counter_path)
        self.counter_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_counter(self) -> int:
        if not self.counter_path.exists():
            return 0
        with self.counter_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return int(data.get("last_user_id", 0))

    def _write_counter(self, value: int) -> None:
        with self.counter_path.open("w", encoding="utf-8") as f:
            json.dump({"last_user_id": value}, f, ensure_ascii=False, indent=2)

    def allocate_user_id(self) -> int:
        current = self._read_counter()
        new_id = current + 1
        self._write_counter(new_id)
        return new_id

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
