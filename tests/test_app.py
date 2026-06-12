# coding: utf-8
"""Тесты AppService — сквозной сценарий MVP."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import patch

from core.app import AppService
from core.logging.base import EventLogger
from core.models import (
    ACTION_DIARY_TEXT,
    ACTION_NAME_ENTERED,
    ACTION_OPTION_1,
    ACTION_OPTION_2,
    ACTION_OPTION_3,
    Screen,
)


class FakeLogger(EventLogger):
    """Логгер в память для тестов."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.users: dict[int, dict[str, Any]] = {}
        self._counter = 0

    def allocate_user_id(self) -> int:
        self._counter += 1
        return self._counter

    def upsert_user(
        self,
        user_id: int,
        user_name: str,
        registration_date: datetime,
        registration_channel: str,
        last_active_at: datetime,
        is_paid: bool = False,
        is_trial: bool = False,
        is_active: bool = True,
    ) -> None:
        self.users[user_id] = {
            "user_name": user_name,
            "registration_date": registration_date,
            "registration_channel": registration_channel,
            "last_active_at": last_active_at,
            "is_paid": is_paid,
            "is_trial": is_trial,
            "is_active": is_active,
        }

    def log_event(
        self,
        user_id: int,
        event_name: str,
        channel: str,
        event_parameters: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        self.events.append(
            {
                "user_id": user_id,
                "event_name": event_name,
                "channel": channel,
                "event_parameters": event_parameters,
                "timestamp": timestamp,
            }
        )


def _make_service() -> tuple[AppService, FakeLogger]:
    logger = FakeLogger()
    config = {
        "weatherapi": {
            "url": "http://api.weatherapi.com/v1",
            "method": "/current.json",
            "api_key": "key",
            "city": "Moscow",
        },
        "paths": {"jokes_file": "data/jokes.json"},
    }
    return AppService(logger=logger, config=config), logger


def _user_payload(user_name: str, registration_date: datetime) -> dict[str, Any]:
    return {
        "user_name": user_name,
        "registration_date": registration_date.isoformat(),
    }


def test_handle_start_creates_user_before_event() -> None:
    service, logger = _make_service()
    service.handle_start(1, "streamlit")

    assert 1 in logger.users
    assert logger.users[1]["user_name"] == ""
    assert logger.events[0]["event_name"] == "start_screen_visit"


def test_full_mvp_flow_logs_all_events() -> None:
    service, logger = _make_service()
    user_id = 1
    channel = "console"

    start_resp = service.handle_start(user_id, channel)
    assert start_resp.screen == Screen.START

    name_resp = service.handle_action(
        user_id,
        channel,
        ACTION_NAME_ENTERED,
        {"text": "Роман"},
    )
    assert name_resp.screen == Screen.MAIN_MENU
    assert "Роман" in name_resp.text

    event_names = [e["event_name"] for e in logger.events]
    assert "start_screen_visit" in event_names
    assert "registration" in event_names
    assert "main_menu_visit" in event_names
    assert logger.users[1]["user_name"] == "Роман"

    reg_date = logger.users[1]["registration_date"]
    payload = _user_payload("Роман", reg_date)

    with patch(
        "core.app.get_current_temperature",
        return_value="В Moscow сейчас +5°C.",
    ):
        opt1 = service.handle_action(user_id, channel, ACTION_OPTION_1, payload)

    assert "+5°C" in opt1.text
    assert "option1_visit" in [e["event_name"] for e in logger.events]

    with patch("core.app.get_random_joke", return_value="Тестовый анекдот"):
        opt2 = service.handle_action(user_id, channel, ACTION_OPTION_2, payload)

    assert "Тестовый анекдот" in opt2.text
    assert "option2_visit" in [e["event_name"] for e in logger.events]

    opt3 = service.handle_action(user_id, channel, ACTION_OPTION_3, payload)
    assert opt3.screen == Screen.DIARY_WAIT
    assert "option3_visit" in [e["event_name"] for e in logger.events]

    diary = service.handle_action(
        user_id,
        channel,
        ACTION_DIARY_TEXT,
        {**payload, "text": 'Мысли с "кавычками" и O\'Brien'},
    )
    assert diary.screen == Screen.MAIN_MENU
    assert "сохранена" in diary.text.lower()

    diary_events = [
        e for e in logger.events if e["event_name"] == "diary_message_sent"
    ]
    assert len(diary_events) == 1
    assert "O'Brien" in diary_events[0]["event_parameters"]["text"]


def test_empty_name_not_registered() -> None:
    service, logger = _make_service()
    resp = service.handle_action(1, "console", ACTION_NAME_ENTERED, {"text": "   "})
    assert resp.screen == Screen.START
    assert "пустым" in resp.text.lower()
    assert 1 not in logger.users


def test_users_overwritten_on_touch() -> None:
    service, logger = _make_service()
    service.handle_action(1, "console", ACTION_NAME_ENTERED, {"text": "Аня"})

    first_active = logger.users[1]["last_active_at"]
    payload = _user_payload("Аня", logger.users[1]["registration_date"])

    with patch("core.app.get_random_joke", return_value="шутка"):
        service.handle_action(1, "console", ACTION_OPTION_2, payload)

    assert logger.users[1]["user_name"] == "Аня"
    assert logger.users[1]["last_active_at"] >= first_active


def test_raw_text_menu_matching() -> None:
    service, logger = _make_service()
    service.handle_action(1, "console", ACTION_NAME_ENTERED, {"text": "Иван"})
    payload = _user_payload("Иван", logger.users[1]["registration_date"])

    with patch("core.app.get_current_temperature", return_value="холодно"):
        resp = service.handle_action(
            1,
            "console",
            "raw",
            {**payload, "text": "Температура в Москве", "screen": "main_menu"},
        )

    assert "холодно" in resp.text
