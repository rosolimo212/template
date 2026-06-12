# coding: utf-8
"""Тесты общих UI-хелперов."""

from __future__ import annotations

from datetime import datetime

from core.models import Screen
from ui.helpers import apply_response, build_payload


def test_build_payload_with_registration() -> None:
    payload = build_payload(
        user_name="Роман",
        registration_date=datetime(2026, 6, 12, 10, 0, 0),
        text="Температура в Москве",
        screen=Screen.MAIN_MENU,
    )
    assert payload["user_name"] == "Роман"
    assert "2026-06-12" in payload["registration_date"]
    assert payload["screen"] == "main_menu"


def test_apply_response_updates_state() -> None:
    from core.brain import on_name_entered

    state: dict = {}
    response = on_name_entered("Аня")
    apply_response(state, response, user_name="Аня", registration_date="2026-01-01T00:00:00")

    assert state["screen"] == "main_menu"
    assert state["user_name"] == "Аня"
    assert len(state["buttons"]) == 3
