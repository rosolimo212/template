# coding: utf-8
"""
Общие функции для UI-клиентов (streamlit, telegram, console).

Цель:
    Связать session state интерфейса с AppService: identity, payload, AppResponse.

Термины:
    payload — словарь контекста для handle_action (текст ввода, экран, имя пользователя).
    AppResponse — ответ ядра (текст, кнопки, следующий экран).
    UserIdentity — тройка id из postgres/логгера.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.identity import new_external_user_id
from core.models import AppResponse, Screen, UserIdentity


def build_payload(
    user_name: str | None = None,
    registration_date: str | datetime | None = None,
    text: str | None = None,
    screen: Screen | str | None = None,
) -> dict[str, Any]:
    """
    Собирает payload для AppService.handle_action.

    payload — не «полезная нагрузка HTTP», а контекст текущего шага:
    что ввёл пользователь (text), на каком экране (screen), данные регистрации.

    :param user_name: имя после регистрации (для upsert last_active_at)
    :param registration_date: ISO-строка или datetime из session state
    :param text: сырой ввод пользователя
    :param screen: текущий Screen — brain решает, как интерпретировать text
    :return: словарь только с переданными непустыми полями
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
    Записывает AppResponse в session state UI-клиента.

    AppResponse — результат работы brain/app; UI только отображает last_text и buttons.

    :param state: session state (dict или streamlit session_state)
    :param response: ответ AppService
    :param user_name: опционально обновить имя в state после регистрации
    :param registration_date: опционально ISO-дата регистрации
    """
    state["last_text"] = response.text
    state["screen"] = response.screen.value
    state["buttons"] = list(response.buttons)

    if user_name is not None:
        state["user_name"] = user_name

    if registration_date is not None:
        state["registration_date"] = registration_date


def store_identity(state: dict[str, Any], identity: UserIdentity) -> None:
    """
    Сохраняет UserIdentity в session state.

    UserIdentity связывает UI-сессию со строкой в template.users.
    """
    state["user_id"] = identity.user_id
    state["internal_user_id"] = identity.internal_user_id
    state["external_user_id"] = identity.external_user_id


def get_identity(state: dict[str, Any]) -> UserIdentity:
    """
    Восстанавливает UserIdentity из session state.

    :raises KeyError: если init_user_identity ещё не вызывался
    """
    return UserIdentity(
        user_id=str(state["user_id"]),
        internal_user_id=int(state["internal_user_id"]),
        external_user_id=str(state["external_user_id"]),
    )


def init_user_identity(service, state: dict[str, Any], channel: str) -> UserIdentity:
    """
    Один external_user_id на сессию → одна строка в template.users.

    Повторный вызов (streamlit rerun) не создаёт нового internal_user_id.
    ensure_user ищет по (channel, external_user_id).

    :param service: AppService с логгером
    :param state: session state UI
    :param channel: streamlit | telegram | console
    :return: UserIdentity для передачи в handle_start / handle_action
    """
    if (
        state.get("user_id")
        and state.get("internal_user_id") is not None
        and state.get("external_user_id")
    ):
        return get_identity(state)

    if not state.get("external_user_id"):
        state["external_user_id"] = new_external_user_id(channel)

    identity = service.logger.ensure_user(channel, str(state["external_user_id"]))
    store_identity(state, identity)
    return identity
