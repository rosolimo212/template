# coding: utf-8
"""
Слой 2 тестирования — бизнес-проверки из task.md.

Запуск перед коммитом:
    python business_checks.py

или вместе с pytest:
    ./pre_commit_check.sh

Проверки намеренно простые и читаемые — без pytest.
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
from core.logging.factory import build_logger
from core.logging.noop import NoopLogger
from core.models import (
    ACTION_DIARY_TEXT,
    ACTION_NAME_ENTERED,
    ACTION_OPTION_1,
    ACTION_OPTION_2,
    ACTION_OPTION_3,
    Screen,
)

# Все event_name из task.md
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
    """Простой логгер в память для бизнес-проверок."""

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
            }
        )


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


def _run_full_scenario(service: AppService, logger: MemoryLogger, channel: str) -> None:
    """Проходит весь сценарий MVP как один пользователь."""
    user_id = logger.allocate_user_id()

    service.handle_start(user_id, channel)
    service.handle_action(
        user_id, channel, ACTION_NAME_ENTERED, {"text": "Тестовый Пользователь"}
    )

    payload = _user_payload(
        "Тестовый Пользователь",
        logger.users[user_id]["registration_date"],
    )

    with patch("core.app.get_current_temperature", return_value="+10°C"):
        service.handle_action(user_id, channel, ACTION_OPTION_1, payload)

    with patch("core.app.get_random_joke", return_value="Анекдот дня"):
        service.handle_action(user_id, channel, ACTION_OPTION_2, payload)

    service.handle_action(user_id, channel, ACTION_OPTION_3, payload)
    service.handle_action(
        user_id,
        channel,
        ACTION_DIARY_TEXT,
        {**payload, "text": "Запись в дневнике"},
    )


def check_project_scaffold_exists() -> None:
    """Ключевые файлы проекта на месте."""
    required = [
        "core/app.py",
        "core/brain.py",
        "core/config.py",
        "core/db.py",
        "core/logging/postgres.py",
        "ui/streamlit_app.py",
        "ui/helpers.py",
        "ui/console_app.py",
        "ui/telegram_bot.py",
        "sql/001_init.sql",
        "data/jokes.json",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    if missing:
        raise AssertionError("Не найдены файлы: " + ", ".join(missing))


def check_logger_factory_builds() -> None:
    """Фабрика логгера создаёт postgres или noop."""
    build_logger(
        {
            "app": {"logging_enabled": False},
            "logging": {"schema": "template"},
        }
    )
    build_logger(
        {
            "app": {"logging_enabled": True},
            "logging": {
                "host": "localhost",
                "port": 5432,
                "database": "db",
                "user": "u",
                "password": "p",
                "schema": "template",
            },
        }
    )


def check_all_menu_buttons_defined() -> None:
    """Все кнопки меню распознаются brain."""
    for label in MENU_BUTTONS:
        matched = match_menu_button(label)
        if matched is None:
            raise AssertionError(f"Кнопка не распознаётся: {label!r}")

    if match_menu_button(BACK_TO_MENU_BUTTON) is not None:
        raise AssertionError("Кнопка возврата не должна быть пунктом меню")


def check_all_menu_buttons_clickable() -> None:
    """
    Каждая кнопка меню вызывает действие и возвращает ответ с текстом.

    Проверяем логику (streamlit/telegram рендерят те же подписи).
    """
    service, logger = _make_service()
    user_id = 1
    channel = "streamlit"

    service.handle_start(user_id, channel)
    service.handle_action(user_id, channel, ACTION_NAME_ENTERED, {"text": "Юля"})
    payload = _user_payload("Юля", logger.users[user_id]["registration_date"])

    expectations = {
        MENU_BUTTONS[0]: "+",
        MENU_BUTTONS[1]: "анекдот",  # может быть текст ошибки или шутка
        MENU_BUTTONS[2]: "дневник",
    }

    with patch("core.app.get_current_temperature", return_value="+7°C"):
        with patch("core.app.get_random_joke", return_value="Шутка"):
            for label in MENU_BUTTONS:
                resp = service.handle_action(
                    user_id,
                    channel,
                    "raw",
                    {**payload, "text": label, "screen": Screen.MAIN_MENU.value},
                )
                if not resp.text.strip():
                    raise AssertionError(f"Пустой ответ на кнопку: {label!r}")

                if label == MENU_BUTTONS[2]:
                    if resp.screen != Screen.DIARY_WAIT:
                        raise AssertionError(f"Дневник: ожидали diary_wait, got {resp.screen}")
                else:
                    if not resp.buttons:
                        raise AssertionError(f"После {label!r} нет кнопок меню")


def check_all_events_logged() -> None:
    """Все event_name из task.md пишутся за полный сценарий."""
    service, logger = _make_service()
    _run_full_scenario(service, logger, "console")

    logged = {e["event_name"] for e in logger.events}
    missing = [name for name in REQUIRED_EVENTS if name not in logged]
    if missing:
        raise AssertionError(f"Не залогированы события: {missing}. Есть: {sorted(logged)}")


def check_users_overwritten() -> None:
    """Поля users перезаписываются при повторных действиях."""
    service, logger = _make_service()
    user_id = 1

    service.handle_action(user_id, "console", ACTION_NAME_ENTERED, {"text": "Петр"})
    first_active = logger.users[user_id]["last_active_at"]
    first_name = logger.users[user_id]["user_name"]

    payload = _user_payload(first_name, logger.users[user_id]["registration_date"])

    time.sleep(0.01)

    with patch("core.app.get_random_joke", return_value="x"):
        service.handle_action(user_id, "console", ACTION_OPTION_2, payload)

    second_active = logger.users[user_id]["last_active_at"]
    if second_active < first_active:
        raise AssertionError("last_active_at не обновился")
    if logger.users[user_id]["user_name"] != first_name:
        raise AssertionError("user_name не должен пропасть при touch")


def check_no_user_id_collisions() -> None:
    """Инкрементальный user_id без дубликатов (noop-счётчик)."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        counter = Path(tmp) / "user_counter.json"
        logger = NoopLogger(counter_path=counter)
        ids = [logger.allocate_user_id() for _ in range(50)]

        if len(ids) != len(set(ids)):
            raise AssertionError(f"Коллизии user_id: {ids}")

        # Новый экземпляр логгера читает тот же файл-счётчик
        logger2 = NoopLogger(counter_path=counter)
        next_id = logger2.allocate_user_id()
        if next_id in ids:
            raise AssertionError(f"Коллизия после перечитывания счётчика: {next_id}")


def check_special_chars_safe() -> None:
    """Спецсимволы в имени и дневнике не ломают ответ и лог."""
    special_names = [
        'O\'Brien',
        '"Вася"',
        "Имя <script>",
        "Юля 🎉",
        "back\\slash",
    ]
    diary_text = "Кавычки \"тут\", апостроф O'Hara, перенос\nстроки, emoji ☀"

    for name in special_names:
        service, logger = _make_service()
        user_id = logger.allocate_user_id()
        channel = "telegram"

        service.handle_start(user_id, channel)
        resp = service.handle_action(
            user_id, channel, ACTION_NAME_ENTERED, {"text": name}
        )
        if resp.screen != Screen.MAIN_MENU:
            raise AssertionError(f"Имя не принято: {name!r} -> {resp.text}")

        reg_events = [e for e in logger.events if e["event_name"] == "registration"]
        if reg_events[0]["event_parameters"]["user_name"] != name:
            raise AssertionError(f"Имя исказилось в логе: {name!r}")

        payload = _user_payload(name, logger.users[user_id]["registration_date"])
        service.handle_action(user_id, channel, ACTION_OPTION_3, payload)
        diary_resp = service.handle_action(
            user_id,
            channel,
            ACTION_DIARY_TEXT,
            {**payload, "text": diary_text},
        )
        if diary_resp.screen != Screen.MAIN_MENU:
            raise AssertionError(f"Дневник не сохранился для имени {name!r}")

        diary_events = [
            e for e in logger.events if e["event_name"] == "diary_message_sent"
        ]
        if diary_events[-1]["event_parameters"]["text"] != diary_text:
            raise AssertionError("Текст дневника исказился в event_parameters")


def check_scenario_latency_under_limit() -> None:
    """
    Полный сценарий (с mock API) укладывается в 8 секунд.

    Прокси для требований streamlit/telegram: тормоза в ядре ловим здесь.
    Реальный лаг UI с сетью — проверять вручную при приёмке.
    """
    service, logger = _make_service()
    started = time.monotonic()

    with patch("core.app.get_current_temperature", return_value="+1°C"):
        with patch("core.app.get_random_joke", return_value="быстро"):
            _run_full_scenario(service, logger, "streamlit")

    elapsed = time.monotonic() - started
    if elapsed >= MAX_LATENCY_SEC:
        raise AssertionError(
            f"Сценарий занял {elapsed:.2f} с (лимит {MAX_LATENCY_SEC} с)"
        )


def run_all_checks() -> None:
    checks = [
        ("каркас проекта", check_project_scaffold_exists),
        ("фабрика логгера", check_logger_factory_builds),
        ("кнопки меню определены", check_all_menu_buttons_defined),
        ("кнопки меню кликабельны", check_all_menu_buttons_clickable),
        ("все события логируются", check_all_events_logged),
        ("users перезаписываются", check_users_overwritten),
        ("нет коллизий user_id", check_no_user_id_collisions),
        ("спецсимволы безопасны", check_special_chars_safe),
        (f"латентность < {MAX_LATENCY_SEC} с", check_scenario_latency_under_limit),
    ]

    print("business_checks:")
    for title, fn in checks:
        fn()
        print(f"  OK: {title}")

    print("business_checks: OK")


if __name__ == "__main__":
    run_all_checks()
