# coding: utf-8
"""
Мозг системы — чистая логика сценария без I/O.

Цель:
    Определить переходы экранов и тексты ответов.

Вход:
    Действия пользователя (имя, выбор пункта меню, текст дневника).

Выход:
    AppResponse с текстом, кнопками и следующим экраном.

TODO:
    Реализовать полный сценарий MVP в фазе 4.
"""

from __future__ import annotations

from core.models import AppResponse, Screen


def on_start() -> AppResponse:
    """Стартовый экран: запрос имени."""
    return AppResponse(
        text="Как вас зовут?",
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
        buttons=[
            "Температура в Москве",
            "Случайный анекдот",
            "Дорогой дневник",
        ],
        screen=Screen.MAIN_MENU,
    )


def on_unknown_action() -> AppResponse:
    """Заглушка для нераспознанного действия."""
    return AppResponse(
        text="Не понял запрос. Выберите пункт из меню.",
        buttons=[
            "Температура в Москве",
            "Случайный анекдот",
            "Дорогой дневник",
        ],
        screen=Screen.MAIN_MENU,
    )
