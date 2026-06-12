# coding: utf-8
"""
Общие функции для UI-клиентов.

Цель:
    Одинаково собирать payload и обновлять состояние сессии после AppResponse.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.models import AppResponse, Screen


def build_payload(
    user_name: str | None = None,
    registration_date: str | datetime | None = None,
    text: str | None = None,
    screen: Screen | str | None = None,
) -> dict[str, Any]:
    """
    Собирает payload для AppService.handle_action.

    :param user_name: имя после регистрации
    :param registration_date: время регистрации (iso-строка или datetime)
    :param text: ввод пользователя
    :param screen: текущий экран
    :return: dict для payload
    """
    payload: dict[str, Any] = {}

    if user_name:
        payload["user_name"] = user_name

    if registration_date is not None:
        if isinstance(registration_date, datetime):
            payload["registration_date"] = registration_date.isoformat()
        else:
            payload["registration_date"] = registration_date

    if text is not None:
        payload["text"] = text

    if screen is not None:
        if isinstance(screen, Screen):
            payload["screen"] = screen.value
        else:
            payload["screen"] = screen

    return payload


def apply_response(
    state: dict[str, Any],
    response: AppResponse,
    *,
    user_name: str | None = None,
    registration_date: str | None = None,
) -> None:
    """
    Обновляет словарь состояния UI после ответа ядра.

    :param state: session_state (streamlit), FSM data (telegram) или dict (console)
    :param response: ответ AppService
    :param user_name: если только что зарегистрировались
    :param registration_date: iso-строка времени регистрации
    """
    state["last_text"] = response.text
    state["screen"] = response.screen.value
    state["buttons"] = list(response.buttons)

    if user_name is not None:
        state["user_name"] = user_name

    if registration_date is not None:
        state["registration_date"] = registration_date
