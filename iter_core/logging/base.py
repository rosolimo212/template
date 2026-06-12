# coding: utf-8
"""
Контракт логирования.

Цель:
    Позволить подменять postgres и noop без изменения AppService.

Выход:
    Методы log_event, upsert_user, allocate_user_id.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class EventLogger(ABC):
    """Базовый интерфейс логгера событий и пользователей."""

    @abstractmethod
    def allocate_user_id(self) -> int:
        """Выдать новый внутренний user_id без коллизий."""

    @abstractmethod
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
        """Создать или обновить запись пользователя."""

    @abstractmethod
    def log_event(
        self,
        user_id: int,
        event_name: str,
        channel: str,
        event_parameters: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Записать событие в events."""
