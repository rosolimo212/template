# coding: utf-8
"""
AppService — оркестратор ядра.

Цель:
    Связать brain, collectors и logging в единую точку для UI-клиентов.

Вход:
    user_id, channel, действие пользователя.

Выход:
    AppResponse для отображения клиентом.

TODO:
    Полная реализация сценария MVP в фазе 4.
"""

from __future__ import annotations

from typing import Any

from core.brain import on_start, on_unknown_action
from core.logging.base import EventLogger
from core.models import AppResponse


class AppService:
    """Единая точка входа бизнес-логики для всех интерфейсов."""

    def __init__(self, logger: EventLogger, config: dict[str, Any]) -> None:
        self.logger = logger
        self.config = config

    def handle_start(self, user_id: int, channel: str) -> AppResponse:
        """
        Обработка первого визита / команды start.

        :param user_id: внутренний идентификатор пользователя
        :param channel: streamlit | telegram | console
        :return: ответ для UI
        """
        self.logger.log_event(
            user_id=user_id,
            event_name="start_screen_visit",
            channel=channel,
            event_parameters=None,
        )
        return on_start()

    def handle_action(
        self,
        user_id: int,
        channel: str,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> AppResponse:
        """
        Заглушка обработки действий до реализации MVP.

        :param user_id: внутренний идентификатор
        :param channel: канал интерфейса
        :param action: тип действия (пока не используется)
        :param payload: дополнительные данные
        :return: ответ для UI
        """
        _ = (user_id, channel, action, payload)
        return on_unknown_action()
