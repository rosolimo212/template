# coding: utf-8
"""
Cookie-сессия браузера для Streamlit.

Цель:
    После закрытия вкладки вернуть того же пользователя (external_user_id)
    и последний экран без повторной регистрации.

Хранится в cookie template_browser_session (JSON, max-age 365 дней):
    external_user_id, screen, user_name, registration_date

Streamlit session_state живёт только пока открыта сессия WebSocket;
cookie — мост между визитами одного браузера.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

COOKIE_NAME = "template_browser_session"
COOKIE_MAX_AGE_DAYS = 365


def session_cookie_payload(state: dict[str, Any]) -> dict[str, str]:
    """
    Собирает данные для записи в cookie из session state.

    :param state: st.session_state (dict-like)
    :return: только непустые строковые поля
    """
    payload: dict[str, str] = {}

    external = state.get("external_user_id")
    if external:
        payload["external_user_id"] = str(external)

    screen = state.get("screen")
    if screen:
        payload["screen"] = str(screen)

    user_name = state.get("user_name")
    if user_name:
        payload["user_name"] = str(user_name)

    reg_date = state.get("registration_date")
    if reg_date:
        payload["registration_date"] = str(reg_date)

    return payload


def encode_session_cookie(payload: dict[str, str]) -> str:
    """JSON для значения cookie (без пробелов — компактнее)."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def decode_session_cookie(raw: str | None) -> dict[str, str]:
    """
    Разбирает cookie; при ошибке — пустой dict (новый визит).

    :param raw: строка из cookie или None
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items() if v is not None and str(v).strip()}


def apply_cookie_to_state(state: dict[str, Any], cookie_data: dict[str, str]) -> None:
    """
    Восстанавливает поля session state из cookie (до init_user_identity).

    external_user_id из cookie → тот же пользователь в postgres.
    """
    if cookie_data.get("external_user_id"):
        state["external_user_id"] = cookie_data["external_user_id"]
    if cookie_data.get("screen"):
        state["screen"] = cookie_data["screen"]
    if cookie_data.get("user_name"):
        state["user_name"] = cookie_data["user_name"]
    if cookie_data.get("registration_date"):
        state["registration_date"] = cookie_data["registration_date"]


def cookie_expires_at() -> datetime:
    """Срок жизни cookie для CookieManager."""
    return datetime.now(timezone.utc) + timedelta(days=COOKIE_MAX_AGE_DAYS)
