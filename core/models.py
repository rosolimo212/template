# coding: utf-8
"""
Общие структуры данных ядра.

Цель:
    Единые типы для users, events и ответов UI без привязки к конкретному клиенту.

Выход:
    dataclass-объекты, которые передаются между brain, app и logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class UserIdentity:
    """Тройка идентификаторов пользователя."""

    user_id: str
    internal_user_id: int
    external_user_id: str


class Screen(str, Enum):
    """Экраны пользовательского сценария MVP."""

    START = "start"
    NAME_CONFIRM = "name_confirm"
    MAIN_MENU = "main_menu"
    OPTION_1 = "option_1"
    OPTION_2 = "option_2"
    OPTION_3 = "option_3"
    DIARY_WAIT = "diary_wait"


# Действия, которые UI передаёт в AppService.handle_action
ACTION_NAME_ENTERED = "name_entered"
ACTION_NAME_CONFIRMED = "name_confirmed"
ACTION_NAME_CHANGE = "name_change"
ACTION_OPTION_1 = "option_1"
ACTION_OPTION_2 = "option_2"
ACTION_OPTION_3 = "option_3"
ACTION_DIARY_TEXT = "diary_text"
ACTION_BACK_TO_MENU = "back_to_menu"


@dataclass
class UserRecord:
    """Запись пользователя для таблицы template.users."""

    user_id: str
    internal_user_id: int
    external_user_id: str
    user_name: str
    registration_date: datetime
    registration_channel: str
    last_active_at: datetime
    is_paid: bool = False
    is_trial: bool = False
    is_active: bool = True


@dataclass
class EventRecord:
    """Запись события для таблицы template.events."""

    timestamp: datetime
    user_id: str
    internal_user_id: int
    external_user_id: str
    event_name: str
    channel: str
    event_parameters: dict[str, Any] | None = None


@dataclass
class AppResponse:
    """Ответ ядра клиенту: текст, кнопки, следующий экран."""

    text: str
    buttons: list[str] = field(default_factory=list)
    screen: Screen = Screen.START
    finished: bool = False
