# coding: utf-8
"""
Тексты диалогов с пользователем (data/dialog_messages.json).

Цель:
    Вынести все user-facing строки из кода в один JSON для правки и локализации.

Вход:
    name сообщения или кнопки, опционально channel (streamlit | telegram | console).

Выход:
    Строка для показа пользователю. Пустое поле канала в JSON → берётся default.

Риски:
    При смене текста кнопки нужно синхронно обновить match_menu_button в brain.py
    (сопоставление идёт по отображаемому тексту).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_MESSAGES_PATH = Path(__file__).resolve().parents[1] / "data" / "dialog_messages.json"

# Каналы приложения → ключи в JSON (browser = streamlit).
CHANNEL_TO_UI_KEY = {
    "console": "console",
    "telegram": "telegram",
    "streamlit": "browser",
}


@lru_cache(maxsize=1)
def _load_catalog(path: str | None = None) -> dict[str, Any]:
    """
    Загружает каталог сообщений один раз за процесс.

    :param path: путь к JSON; None — data/dialog_messages.json
    :return: словарь с ключами messages и buttons
    """
    file_path = Path(path) if path else DEFAULT_MESSAGES_PATH
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_channel_key(channel: str | None) -> str | None:
    """Преобразует channel приложения в ключ поля JSON."""
    if channel is None:
        return None
    return CHANNEL_TO_UI_KEY.get(channel, channel)


def _pick_text(entry: dict[str, Any], channel: str | None) -> str:
    """
    Выбирает текст: override канала или default.

    :param entry: элемент messages/buttons из JSON
    :param channel: streamlit | telegram | console | None
    """
    ui_key = _resolve_channel_key(channel)
    if ui_key:
        override = str(entry.get(ui_key, "") or "").strip()
        if override:
            return override
    return str(entry["default"])


def _find_by_name(section: str, name: str, path: str | None = None) -> dict[str, Any]:
    catalog = _load_catalog(path)
    for item in catalog.get(section, []):
        if item.get("name") == name:
            return item
    raise KeyError(f"Не найден {section} name={name!r} в dialog_messages.json")


def message(
    name: str,
    channel: str | None = None,
    *,
    path: str | None = None,
    **placeholders: Any,
) -> str:
    """
    Текст сообщения по имени.

    :param name: ключ name в JSON (например start_ask_name)
    :param channel: интерфейс; None — только default
    :param placeholders: подстановки в {user_name}, {display}, …
    :return: готовая строка
    """
    entry = _find_by_name("messages", name, path)
    text = _pick_text(entry, channel)
    if placeholders:
        text = text.format(**placeholders)
    return text


def button(
    name: str,
    channel: str | None = None,
    *,
    path: str | None = None,
) -> str:
    """
    Текст кнопки по имени (menu_option_1, back_to_menu, …).

    :param name: ключ name в секции buttons JSON
    :param channel: интерфейс; None — default
    """
    entry = _find_by_name("buttons", name, path)
    return _pick_text(entry, channel)


def menu_buttons(channel: str | None = None, *, path: str | None = None) -> list[str]:
    """Три пункта главного меню в порядке option_1 … option_3."""
    return [
        button("menu_option_1", channel, path=path),
        button("menu_option_2", channel, path=path),
        button("menu_option_3", channel, path=path),
    ]


def back_to_menu_button(channel: str | None = None) -> str:
    return button("back_to_menu", channel)


def confirm_name_button(channel: str | None = None) -> str:
    return button("confirm_name", channel)


def change_name_button(channel: str | None = None) -> str:
    return button("change_name", channel)


# Константы по умолчанию (default-тексты) — для импортов без channel.
MENU_BUTTONS = menu_buttons()
BACK_TO_MENU_BUTTON = back_to_menu_button()
CONFIRM_NAME_BUTTON = confirm_name_button()
CHANGE_NAME_BUTTON = change_name_button()
