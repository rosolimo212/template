# coding: utf-8
"""Тесты AppService — сквозной сценарий MVP."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import patch

from core.app import AppService
from core.identity import make_user_id
from core.logging.base import EventLogger
from core.models import (
    ACTION_DIARY_TEXT,
    ACTION_NAME_ENTERED,
    ACTION_OPTION_1,
    ACTION_OPTION_2,
    ACTION_OPTION_3,
    Screen,
    UserIdentity,
)


class FakeLogger(EventLogger):
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.users: dict[str, dict[str, Any]] = {}
        self._counter = 0

    def ensure_user(self, channel: str, external_user_id: str) -> UserIdentity:
        user_id = make_user_id(channel, external_user_id)
        if user_id in self.users:
            row = self.users[user_id]
            return UserIdentity(user_id, row["internal_user_id"], external_user_id)

        self._counter += 1
        self.users[user_id] = {
            "internal_user_id": self._counter,
            "external_user_id": external_user_id,
        }
        return UserIdentity(user_id, self._counter, external_user_id)

    def upsert_user(
        self,
        identity: UserIdentity,
        user_name: str,
        registration_date: datetime,
        registration_channel: str,
        last_active_at: datetime,
        is_paid: bool = False,
        is_trial: bool = False,
        is_active: bool = True,
    ) -> None:
        self.users[identity.user_id] = {
            "internal_user_id": identity.internal_user_id,
            "external_user_id": identity.external_user_id,
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
        identity: UserIdentity,
        event_name: str,
        channel: str,
        event_parameters: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        self.events.append(
            {
                "user_id": identity.user_id,
                "internal_user_id": identity.internal_user_id,
                "external_user_id": identity.external_user_id,
                "event_name": event_name,
                "channel": channel,
                "event_parameters": event_parameters,
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
    identity = logger.ensure_user("streamlit", "ext-1")
    service.handle_start(identity, "streamlit")

    assert identity.user_id in logger.users
    assert logger.users[identity.user_id]["user_name"] == ""
    assert logger.events[0]["event_name"] == "start_screen_visit"


def test_full_mvp_flow_logs_all_events() -> None:
    service, logger = _make_service()
    channel = "console"
    identity = logger.ensure_user(channel, "ext-test-1")

    start_resp = service.handle_start(identity, channel)
    assert start_resp.screen == Screen.START

    name_resp = service.handle_action(
        identity,
        channel,
        ACTION_NAME_ENTERED,
        {"text": "Роман"},
    )
    assert name_resp.screen == Screen.MAIN_MENU

    event_names = [e["event_name"] for e in logger.events]
    assert "start_screen_visit" in event_names
    assert "registration" in event_names
    assert "main_menu_visit" in event_names

    reg_date = logger.users[identity.user_id]["registration_date"]
    payload = _user_payload("Роман", reg_date)

    with patch("core.app.get_current_temperature", return_value="В Moscow сейчас +5°C."):
        service.handle_action(identity, channel, ACTION_OPTION_1, payload)

    with patch("core.app.get_random_joke", return_value="Тестовый анекдот"):
        service.handle_action(identity, channel, ACTION_OPTION_2, payload)

    service.handle_action(identity, channel, ACTION_OPTION_3, payload)
    service.handle_action(
        identity,
        channel,
        ACTION_DIARY_TEXT,
        {**payload, "text": 'Мысли с "кавычками" и O\'Brien'},
    )

    assert "diary_message_sent" in [e["event_name"] for e in logger.events]


def test_ensure_user_same_external_id_same_hash() -> None:
    logger = FakeLogger()
    a = logger.ensure_user("telegram", "12345")
    b = logger.ensure_user("telegram", "12345")
    assert a.user_id == b.user_id
    assert a.internal_user_id == b.internal_user_id


def test_ensure_user_same_external_reuses_internal() -> None:
    logger = FakeLogger()
    a = logger.ensure_user("streamlit", "session-abc")
    b = logger.ensure_user("streamlit", "session-abc")
    assert a.internal_user_id == b.internal_user_id
    assert a.user_id == b.user_id


def test_empty_name_not_registered() -> None:
    service, logger = _make_service()
    identity = logger.ensure_user("console", "ext-2")
    service.handle_start(identity, "console")
    resp = service.handle_action(
        identity, "console", ACTION_NAME_ENTERED, {"text": "   "}
    )
    assert resp.screen == Screen.START
    assert logger.users[identity.user_id]["user_name"] == ""
