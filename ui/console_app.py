# coding: utf-8
"""Консольный клиент."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import ACTION_DIARY_TEXT, ACTION_NAME_ENTERED, Screen
from ui.base import build_app_service
from ui.helpers import (
    apply_response,
    build_payload,
    get_identity,
    init_user_identity,
)


def _print_response(state: dict[str, Any]) -> None:
    print()
    print(state.get("last_text", ""))
    print()


def run_console(config: dict[str, Any]) -> None:
    service = build_app_service(config)
    state: dict[str, Any] = {}

    identity = init_user_identity(service, state, "console")
    response = service.handle_start(identity, "console")
    apply_response(state, response)

    print("=== Template console ===")
    print(f"user_id (hash): {state['user_id']}")
    print(f"internal_user_id: {state['internal_user_id']}")
    print(f"external_user_id: {state['external_user_id']}")
    _print_response(state)

    while True:
        screen = state.get("screen", Screen.START.value)
        identity = get_identity(state)

        if screen == Screen.START.value:
            text = input("> ").strip()
            if text.lower() in ("exit", "quit", "выход"):
                break
            response = service.handle_action(
                identity,
                "console",
                ACTION_NAME_ENTERED,
                build_payload(text=text),
            )
            user_name = None
            reg_date = None
            if response.screen == Screen.MAIN_MENU:
                user_name = text
                reg_date = datetime.now().isoformat()
            apply_response(
                state,
                response,
                user_name=user_name,
                registration_date=reg_date,
            )
            _print_response(state)
            continue

        if screen == Screen.DIARY_WAIT.value:
            print("Введите запись (или 'меню' для возврата):")
            text = input("> ").strip()
            if text.lower() in ("exit", "quit", "выход"):
                break
            response = service.handle_action(
                identity,
                "console",
                ACTION_DIARY_TEXT,
                {
                    **build_payload(
                        user_name=state.get("user_name"),
                        registration_date=state.get("registration_date"),
                    ),
                    **build_payload(text=text, screen=screen),
                },
            )
            apply_response(state, response)
            _print_response(state)
            continue

        buttons = state.get("buttons", [])
        if buttons:
            print("Меню:")
            for idx, label in enumerate(buttons, start=1):
                print(f"  {idx}. {label}")
            print("  0. Выход")

        choice = input("> ").strip()
        if choice in ("0", "exit", "quit", "выход"):
            break

        if choice.isdigit() and buttons:
            idx = int(choice) - 1
            if 0 <= idx < len(buttons):
                text = buttons[idx]
            else:
                print("Нет такого пункта.")
                continue
        else:
            text = choice

        response = service.handle_action(
            identity,
            "console",
            "raw",
            {
                **build_payload(
                    user_name=state.get("user_name"),
                    registration_date=state.get("registration_date"),
                ),
                **build_payload(text=text, screen=screen),
            },
        )
        apply_response(state, response)
        _print_response(state)

    print("До встречи.")
