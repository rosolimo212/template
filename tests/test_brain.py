# coding: utf-8
"""Тесты чистой логики brain."""

from __future__ import annotations

from iter_core.brain import on_name_entered, on_start
from iter_core.models import Screen


def test_on_start_asks_name() -> None:
    response = on_start()
    assert "зовут" in response.text.lower()
    assert response.screen == Screen.START


def test_on_name_entered_shows_menu() -> None:
    response = on_name_entered("Роман")
    assert "Роман" in response.text
    assert len(response.buttons) == 3
    assert response.screen == Screen.MAIN_MENU
