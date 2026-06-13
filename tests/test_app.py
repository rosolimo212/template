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

    def get_user_profile(self, identity: UserIdentity) -> dict[str, Any] | None:
        row = self.users.get(identity.user_id)
        if row is None:
            return None
        return {
            "user_name": str(row.get("user_name", "")),
            "registration_date": row.get("registration_date"),
        }


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


def test_telegram_username_auto_register() -> None:
    service, logger = _make_service()
    identity = logger.ensure_user("telegram", "777")
    resp = service.handle_start(
        identity,
        "telegram",
        {"telegram_username": "roman_dev"},
    )
    assert resp.screen == Screen.NAME_CONFIRM
    assert "roman_dev" in resp.text
    assert logger.users[identity.user_id]["user_name"] == "roman_dev"
    reg_events = [e for e in logger.events if e["event_name"] == "registration"]
    assert len(reg_events) == 1
    assert reg_events[0]["event_parameters"]["source"] == "telegram_username"


def test_telegram_username_confirm_goes_to_menu() -> None:
    from core.models import ACTION_NAME_CONFIRMED

    service, logger = _make_service()
    identity = logger.ensure_user("telegram", "778")
    service.handle_start(identity, "telegram", {"telegram_username": "nick"})
    resp = service.handle_action(
        identity,
        "telegram",
        ACTION_NAME_CONFIRMED,
        {"user_name": "nick"},
    )
    assert resp.screen == Screen.MAIN_MENU
    assert "nick" in resp.text


def test_telegram_no_username_asks_name() -> None:
    service, logger = _make_service()
    identity = logger.ensure_user("telegram", "779")
    resp = service.handle_start(identity, "telegram", {"telegram_username": ""})
    assert resp.screen == Screen.START
    assert "зовут" in resp.text.lower()


def test_returning_telegram_user_skips_registration() -> None:
    service, logger = _make_service()
    identity = logger.ensure_user("telegram", "780")
    service.handle_action(
        identity, "telegram", ACTION_NAME_ENTERED, {"text": "Анна"}
    )
    resp = service.handle_start(identity, "telegram", {"telegram_username": "anna"})
    assert resp.screen == Screen.MAIN_MENU
    assert "Анна" in resp.text


def test_empty_name_not_registered() -> None:
    service, logger = _make_service()
    identity = logger.ensure_user("console", "ext-2")
    service.handle_start(identity, "console")
    resp = service.handle_action(
        identity, "console", ACTION_NAME_ENTERED, {"text": "   "}
    )
    assert resp.screen == Screen.START
    assert logger.users[identity.user_id]["user_name"] == ""
