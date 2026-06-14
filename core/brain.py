# coding: utf-8
"""
Мозг системы — чистая логика сценария без I/O.

Цель:
    Определить переходы экранов и тексты ответов.

Вход:
    Действия пользователя (имя, выбор пункта меню, текст дневника).
    channel — интерфейс (streamlit | telegram | console) для текстов из JSON.

Выход:
    AppResponse — единый ответ ядра для любого UI-клиента.
"""

from __future__ import annotations

from core.messages import (
    BACK_TO_MENU_BUTTON,
    CHANGE_NAME_BUTTON,
    CONFIRM_NAME_BUTTON,
    MENU_BUTTONS,
    back_to_menu_button,
    button,
    change_name_button,
    confirm_name_button,
    menu_buttons,
    message,
)
from core.models import AppResponse, Screen


def format_display_name(user_name: str, *, with_at: bool = False) -> str:
    """
    Форматирует имя для показа пользователю (Telegram @ник).

    :param user_name: значение из БД или ввода
    :param with_at: добавить @ для telegram username
    """
    clean = user_name.strip().lstrip("@")
    if not clean:
        return user_name
    if with_at:
        return f"@{clean}"
    return clean


def on_start(channel: str | None = None) -> AppResponse:
    """Стартовый экран: запрос имени."""
    return AppResponse(
        text=message("start_ask_name", channel),
        buttons=[],
        screen=Screen.START,
    )


def on_empty_name(channel: str | None = None) -> AppResponse:
    """Пользователь отправил пустое имя."""
    return AppResponse(
        text=message("empty_name", channel),
        buttons=[],
        screen=Screen.START,
    )


def on_name_entered(user_name: str, channel: str | None = None) -> AppResponse:
    """После ввода имени — главное меню."""
    return AppResponse(
        text=message("main_menu_greeting", channel, user_name=user_name),
        buttons=menu_buttons(channel),
        screen=Screen.MAIN_MENU,
    )


def on_telegram_name_confirm(user_name: str, channel: str | None = None) -> AppResponse:
    """Telegram: ник подставлен автоматически, можно подтвердить или изменить."""
    display = format_display_name(user_name, with_at=True)
    return AppResponse(
        text=message("telegram_name_confirm", channel, display=display),
        buttons=[
            confirm_name_button(channel),
            change_name_button(channel),
        ],
        screen=Screen.NAME_CONFIRM,
    )


def on_change_name_prompt(channel: str | None = None) -> AppResponse:
    """Запрос другого имени (Telegram)."""
    return AppResponse(
        text=message("change_name_prompt", channel),
        buttons=[],
        screen=Screen.START,
    )


def on_main_menu_reminder(channel: str | None = None) -> AppResponse:
    """Напоминание меню при нераспознанном вводе."""
    return AppResponse(
        text=message("main_menu_reminder", channel),
        buttons=menu_buttons(channel),
        screen=Screen.MAIN_MENU,
    )


def on_option_1_result(weather_text: str, channel: str | None = None) -> AppResponse:
    """Результат запроса температуры."""
    return AppResponse(
        text=weather_text,
        buttons=menu_buttons(channel),
        screen=Screen.MAIN_MENU,
    )


def on_option_2_result(joke_text: str, channel: str | None = None) -> AppResponse:
    """Результат случайного анекдота."""
    return AppResponse(
        text=joke_text,
        buttons=menu_buttons(channel),
        screen=Screen.MAIN_MENU,
    )


def on_option_3_prompt(channel: str | None = None) -> AppResponse:
    """Экран ввода записи в дневник."""
    return AppResponse(
        text=message("diary_prompt", channel),
        buttons=[back_to_menu_button(channel)],
        screen=Screen.DIARY_WAIT,
    )


def on_diary_empty(channel: str | None = None) -> AppResponse:
    """Пустая запись дневника."""
    return AppResponse(
        text=message("diary_empty", channel),
        buttons=[back_to_menu_button(channel)],
        screen=Screen.DIARY_WAIT,
    )


def on_diary_saved(channel: str | None = None) -> AppResponse:
    """Подтверждение после сохранения дневника."""
    return AppResponse(
        text=message("diary_saved", channel),
        buttons=menu_buttons(channel),
        screen=Screen.MAIN_MENU,
    )


def match_menu_button(text: str, channel: str | None = None) -> str | None:
    """
    Сопоставляет текст кнопки с пунктом меню.

    :param text: ввод пользователя
    :param channel: интерфейс — тексты кнопок могут отличаться
    :return: option_1 | option_2 | option_3 или None
    """
    normalized = text.strip().casefold()
    buttons = menu_buttons(channel)
    mapping = {
        buttons[0].casefold(): "option_1",
        buttons[1].casefold(): "option_2",
        buttons[2].casefold(): "option_3",
    }
    return mapping.get(normalized)


def is_back_to_menu(text: str, channel: str | None = None) -> bool:
    """Проверяет, хочет ли пользователь вернуться в меню."""
    return text.strip().casefold() == back_to_menu_button(channel).casefold()


# Реэкспорт для обратной совместимости (default-тексты).
__all__ = [
    "BACK_TO_MENU_BUTTON",
    "CHANGE_NAME_BUTTON",
    "CONFIRM_NAME_BUTTON",
    "MENU_BUTTONS",
    "format_display_name",
    "is_back_to_menu",
    "match_menu_button",
    "on_change_name_prompt",
    "on_diary_empty",
    "on_diary_saved",
    "on_empty_name",
    "on_main_menu_reminder",
    "on_name_entered",
    "on_option_1_result",
    "on_option_2_result",
    "on_option_3_prompt",
    "on_start",
    "on_telegram_name_confirm",
]
