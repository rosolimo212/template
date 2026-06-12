# coding: utf-8
"""
Мозг системы — чистая логика сценария без I/O.

Цель:
    Определить переходы экранов и тексты ответов.

Вход:
    Действия пользователя (имя, выбор пункта меню, текст дневника).

Выход:
    AppResponse с текстом, кнопками и следующим экраном.
"""

from __future__ import annotations

from core.models import AppResponse, Screen

MENU_BUTTONS = [
    "Температура в Москве",
    "Случайный анекдот",
    "Дорогой дневник",
]

BACK_TO_MENU_BUTTON = "В главное меню"


def on_start() -> AppResponse:
    """Стартовый экран: запрос имени."""
    return AppResponse(
        text="Как вас зовут?",
        buttons=[],
        screen=Screen.START,
    )


def on_empty_name() -> AppResponse:
    """Пользователь отправил пустое имя."""
    return AppResponse(
        text="Имя не может быть пустым. Как вас зовут?",
        buttons=[],
        screen=Screen.START,
    )


def on_name_entered(user_name: str) -> AppResponse:
    """После ввода имени — главное меню."""
    return AppResponse(
        text=(
            f"Приятно познакомиться, {user_name}!\n\n"
            "Главное меню:\n"
            "1 — узнать текущую температуру в Москве\n"
            "2 — прочитать случайный анекдот\n"
            "3 — дорогой дневник: записать мысли о дне"
        ),
        buttons=list(MENU_BUTTONS),
        screen=Screen.MAIN_MENU,
    )


def on_main_menu_reminder() -> AppResponse:
    """Напоминание меню при нераспознанном вводе."""
    return AppResponse(
        text="Выберите пункт из главного меню.",
        buttons=list(MENU_BUTTONS),
        screen=Screen.MAIN_MENU,
    )


def on_option_1_result(weather_text: str) -> AppResponse:
    """Результат запроса температуры."""
    return AppResponse(
        text=weather_text,
        buttons=list(MENU_BUTTONS),
        screen=Screen.MAIN_MENU,
    )


def on_option_2_result(joke_text: str) -> AppResponse:
    """Результат случайного анекдота."""
    return AppResponse(
        text=joke_text,
        buttons=list(MENU_BUTTONS),
        screen=Screen.MAIN_MENU,
    )


def on_option_3_prompt() -> AppResponse:
    """Экран ввода записи в дневник."""
    return AppResponse(
        text="Дорогой дневник: напишите мысли о текущем дне в свободной форме.",
        buttons=[BACK_TO_MENU_BUTTON],
        screen=Screen.DIARY_WAIT,
    )


def on_diary_empty() -> AppResponse:
    """Пустая запись дневника."""
    return AppResponse(
        text="Запись не может быть пустой. Напишите хотя бы одно слово.",
        buttons=[BACK_TO_MENU_BUTTON],
        screen=Screen.DIARY_WAIT,
    )


def on_diary_saved() -> AppResponse:
    """Подтверждение после сохранения дневника."""
    return AppResponse(
        text="Запись сохранена. Спасибо, что поделились!",
        buttons=list(MENU_BUTTONS),
        screen=Screen.MAIN_MENU,
    )


def match_menu_button(text: str) -> str | None:
    """
    Сопоставляет текст кнопки с пунктом меню.

    :param text: ввод пользователя
    :return: option_1 | option_2 | option_3 или None
    """
    normalized = text.strip().casefold()
    mapping = {
        MENU_BUTTONS[0].casefold(): "option_1",
        MENU_BUTTONS[1].casefold(): "option_2",
        MENU_BUTTONS[2].casefold(): "option_3",
    }
    return mapping.get(normalized)


def is_back_to_menu(text: str) -> bool:
    """Проверяет, хочет ли пользователь вернуться в меню."""
    return text.strip().casefold() == BACK_TO_MENU_BUTTON.casefold()
