# coding: utf-8
"""Тесты чистой логики brain."""

from __future__ import annotations

from core.brain import (
    CHANGE_NAME_BUTTON,
    CONFIRM_NAME_BUTTON,
    on_name_entered,
    on_start,
    on_telegram_name_confirm,
)
from core.models import Screen


def test_on_start_asks_name() -> None:
    response = on_start()
    assert "зовут" in response.text.lower()
    assert response.screen == Screen.START


def test_on_name_entered_shows_menu() -> None:
    response = on_name_entered("Роман")
    assert "Роман" in response.text
    assert len(response.buttons) == 3
    assert response.screen == Screen.MAIN_MENU


def test_on_telegram_name_confirm() -> None:
    response = on_telegram_name_confirm("roman_dev")
    assert "@roman_dev" in response.text
    assert CONFIRM_NAME_BUTTON in response.buttons
    assert CHANGE_NAME_BUTTON in response.buttons
    assert response.screen == Screen.NAME_CONFIRM
