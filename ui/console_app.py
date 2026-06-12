# coding: utf-8
"""
Консольный клиент для отладки ядра без браузера и telegram.
"""

from __future__ import annotations

from typing import Any

from ui.base import build_app_service


def run_console(config: dict[str, Any]) -> None:
    """
    Минимальный консольный цикл для проверки ядра.

    :param config: конфиг из config.yaml
    """
    service = build_app_service(config)
    user_id = service.logger.allocate_user_id()
    response = service.handle_start(user_id, "console")

    print("=== Template console (фаза 0) ===")
    print(response.text)
    print(f"user_id: {user_id}")
    print("Для выхода нажмите Enter.")
    input()
