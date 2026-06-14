# coding: utf-8
"""Тесты загрузки dialog_messages.json."""

from __future__ import annotations

from core.messages import button, menu_buttons, message


def test_message_default() -> None:
    text = message("start_ask_name")
    assert "зовут" in text.lower()


def test_menu_buttons_count() -> None:
    assert len(menu_buttons()) == 3


def test_button_confirm_name() -> None:
    assert button("confirm_name") == "Всё верно"


def test_message_with_placeholder() -> None:
    text = message("main_menu_greeting", user_name="Анна")
    assert "Анна" in text
