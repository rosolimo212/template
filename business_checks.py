# coding: utf-8
"""
Слой 2 тестирования — бизнес-проверки из task.md.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.app import AppService
from core.brain import BACK_TO_MENU_BUTTON, MENU_BUTTONS, match_menu_button
from core.collectors.weather import (
    format_weather_timings,
    get_current_temperature_with_timing,
)
from core.identity import make_user_id
from core.logging.factory import build_logger
from core.logging.noop import NoopLogger
from core.models import (
    ACTION_DIARY_TEXT,
    ACTION_NAME_ENTERED,
    ACTION_OPTION_1,
    ACTION_OPTION_2,
    ACTION_OPTION_3,
    Screen,
    UserIdentity,
)

REQUIRED_EVENTS = [
    "start_screen_visit",
    "main_menu_visit",
    "option1_visit",
    "option2_visit",
    "option3_visit",
    "registration",
    "diary_message_sent",
]

MAX_LATENCY_SEC = 8.0


class MemoryLogger:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.users: dict[str, dict[str, Any]] = {}
        self._by_external: dict[tuple[str, str], UserIdentity] = {}
        self._counter = 0

    def ensure_user(self, channel: str, external_user_id: str) -> UserIdentity:
        key = (channel, external_user_id)
        if key in self._by_external:
            return self._by_external[key]

        user_id = make_user_id(channel, external_user_id)
        if user_id in self.users:
            identity = UserIdentity(
                user_id,
                self.users[user_id]["internal_user_id"],
                external_user_id,
            )
            self._by_external[key] = identity
            return identity

        self._counter += 1
        self.users[user_id] = {"internal_user_id": self._counter}
        identity = UserIdentity(user_id, self._counter, external_user_id)
        self._by_external[key] = identity
        return identity

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


def _make_service(logger: MemoryLogger | None = None) -> tuple[AppService, MemoryLogger]:
    log = logger or MemoryLogger()
    config = {
        "weatherapi": {
            "url": "http://api.weatherapi.com/v1",
            "method": "/current.json",
            "api_key": "test-key",
            "city": "Moscow",
        },
        "paths": {"jokes_file": str(ROOT / "data" / "jokes.json")},
    }
    return AppService(logger=log, config=config), log


def _user_payload(user_name: str, registration_date: datetime) -> dict[str, Any]:
    return {
        "user_name": user_name,
        "registration_date": registration_date.isoformat(),
    }


def _run_full_scenario(service: AppService, logger: MemoryLogger, channel: str) -> UserIdentity:
    identity = logger.ensure_user(channel, "biz-check-user-1")
    service.handle_start(identity, channel)
    service.handle_action(
        identity, channel, ACTION_NAME_ENTERED, {"text": "Тестовый Пользователь"}
    )
    payload = _user_payload(
        "Тестовый Пользователь",
        logger.users[identity.user_id]["registration_date"],
    )
    with patch("core.app.get_current_temperature", return_value="+10°C"):
        service.handle_action(identity, channel, ACTION_OPTION_1, payload)
    with patch("core.app.get_random_joke", return_value="Анекдот дня"):
        service.handle_action(identity, channel, ACTION_OPTION_2, payload)
    service.handle_action(identity, channel, ACTION_OPTION_3, payload)
    service.handle_action(
        identity,
        channel,
        ACTION_DIARY_TEXT,
        {**payload, "text": "Запись в дневнике"},
    )
    return identity


def check_project_scaffold_exists() -> None:
    required = [
        "core/identity.py",
        "core/app.py",
        "sql/002_migrate_user_ids.sql",
        "ui/streamlit_app.py",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    if missing:
        raise AssertionError("Не найдены файлы: " + ", ".join(missing))


def check_logger_factory_builds() -> None:
    build_logger({"app": {"logging_enabled": False}, "logging": {"schema": "template"}})


def check_all_menu_buttons_defined() -> None:
    for label in MENU_BUTTONS:
        if match_menu_button(label) is None:
            raise AssertionError(f"Кнопка не распознаётся: {label!r}")


def check_all_menu_buttons_clickable() -> None:
    service, logger = _make_service()
    identity = logger.ensure_user("streamlit", "btn-test")
    service.handle_start(identity, "streamlit")
    service.handle_action(identity, "streamlit", ACTION_NAME_ENTERED, {"text": "Юля"})
    payload = _user_payload("Юля", logger.users[identity.user_id]["registration_date"])

    with patch("core.app.get_current_temperature", return_value="+7°C"):
        with patch("core.app.get_random_joke", return_value="Шутка"):
            for label in MENU_BUTTONS:
                resp = service.handle_action(
                    identity,
                    "streamlit",
                    "raw",
                    {**payload, "text": label, "screen": Screen.MAIN_MENU.value},
                )
                if not resp.text.strip():
                    raise AssertionError(f"Пустой ответ на кнопку: {label!r}")


def check_all_events_logged() -> None:
    service, logger = _make_service()
    _run_full_scenario(service, logger, "console")
    logged = {e["event_name"] for e in logger.events}
    missing = [n for n in REQUIRED_EVENTS if n not in logged]
    if missing:
        raise AssertionError(f"Не залогированы: {missing}")


def check_users_have_three_ids() -> None:
    service, logger = _make_service()
    identity = _run_full_scenario(service, logger, "telegram")
    row = logger.users[identity.user_id]
    if not row.get("external_user_id"):
        raise AssertionError("external_user_id не сохранён")
    if row["internal_user_id"] != identity.internal_user_id:
        raise AssertionError("internal_user_id не совпадает")


def check_users_overwritten() -> None:
    service, logger = _make_service()
    identity = logger.ensure_user("console", "overwrite-test")
    service.handle_action(identity, "console", ACTION_NAME_ENTERED, {"text": "Петр"})
    first_active = logger.users[identity.user_id]["last_active_at"]
    payload = _user_payload("Петр", logger.users[identity.user_id]["registration_date"])
    time.sleep(0.01)
    with patch("core.app.get_random_joke", return_value="x"):
        service.handle_action(identity, "console", ACTION_OPTION_2, payload)
    if logger.users[identity.user_id]["last_active_at"] < first_active:
        raise AssertionError("last_active_at не обновился")


def check_no_user_id_collisions() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        counter = Path(tmp) / "user_counter.json"
        logger = NoopLogger(counter_path=counter)
        ids = []
        for i in range(50):
            ident = logger.ensure_user("streamlit", f"session-{i}")
            ids.append(ident.internal_user_id)
            if i > 0 and ident.user_id == make_user_id("streamlit", f"session-{i-1}"):
                raise AssertionError("hash user_id коллизия")
        if len(ids) != len(set(ids)):
            raise AssertionError("Коллизии internal_user_id")


def check_special_chars_safe() -> None:
    name = 'O\'Brien "test" 🎉'
    service, logger = _make_service()
    identity = logger.ensure_user("telegram", "spec-1")
    service.handle_start(identity, "telegram")
    service.handle_action(identity, "telegram", ACTION_NAME_ENTERED, {"text": name})
    reg = [e for e in logger.events if e["event_name"] == "registration"][0]
    if reg["event_parameters"]["user_name"] != name:
        raise AssertionError("Имя исказилось в логе")


def check_scenario_latency_under_limit() -> None:
    service, logger = _make_service()
    started = time.monotonic()
    with patch("core.app.get_current_temperature", return_value="+1°C"):
        with patch("core.app.get_random_joke", return_value="быстро"):
            _run_full_scenario(service, logger, "streamlit")
    elapsed = time.monotonic() - started
    if elapsed >= MAX_LATENCY_SEC:
        raise AssertionError(f"Сценарий занял {elapsed:.2f} с")


def check_weather_timing_breakdown() -> None:
    """
    Реальный запрос к weatherapi (если есть config.yaml) + печать тайминга.
    """
    config_path = ROOT / "config.yaml"
    if not config_path.exists():
        print("  SKIP weather timing: нет config.yaml")
        return

    from core.config import load_app_config

    config = load_app_config(config_path)
    w = config["weatherapi"]

    text, timings = get_current_temperature_with_timing(
        api_key=w["api_key"],
        base_url=w["url"],
        method=w["method"],
        city=w["city"],
    )

    print(format_weather_timings(timings))
    print(f"  ответ (первые 80 символов): {text[:80]}")

    http_sec = float(timings.get("http_request_sec", 0))
    total_sec = float(timings.get("total_sec", 0))
    our_code_sec = total_sec - http_sec

    print(f"  вывод: HTTP ~{http_sec:.3f} с, наш код ~{our_code_sec:.3f} с, всего ~{total_sec:.3f} с")

    if total_sec >= MAX_LATENCY_SEC:
        raise AssertionError(f"Погода не уложилась в {MAX_LATENCY_SEC} с: {total_sec:.2f} с")


def run_all_checks() -> None:
    checks = [
        ("каркас проекта", check_project_scaffold_exists),
        ("фабрика логгера", check_logger_factory_builds),
        ("кнопки меню определены", check_all_menu_buttons_defined),
        ("кнопки меню кликабельны", check_all_menu_buttons_clickable),
        ("все события логируются", check_all_events_logged),
        ("три id в users", check_users_have_three_ids),
        ("users перезаписываются", check_users_overwritten),
        ("нет коллизий user_id", check_no_user_id_collisions),
        ("спецсимволы безопасны", check_special_chars_safe),
        (f"латентность сценария < {MAX_LATENCY_SEC} с", check_scenario_latency_under_limit),
        ("тайминг погоды по компонентам", check_weather_timing_breakdown),
    ]

    print("business_checks:")
    for title, fn in checks:
        fn()
        print(f"  OK: {title}")

    print("business_checks: OK")


if __name__ == "__main__":
    run_all_checks()
