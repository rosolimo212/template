# coding: utf-8
"""
Точка входа приложения.

Цель:
    Прочитать config.yaml, выбрать интерфейс и запустить нужный клиент.

Вход:
    config.yaml в корне проекта (секция app.interface).

Выход:
    Работающий процесс streamlit / telegram / console.

Риски:
    При неверном interface процесс завершится с ошибкой.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iter_core.config import load_app_config


def main() -> None:
    config = load_app_config("config.yaml")
    interface = config["app"]["interface"]

    if interface == "streamlit":
        from iter_ui.streamlit_app import run_streamlit

        run_streamlit(config)
    elif interface == "telegram":
        from iter_ui.telegram_bot import run_telegram

        asyncio.run(run_telegram(config))
    elif interface == "console":
        from iter_ui.console_app import run_console

        run_console(config)
    else:
        raise ValueError(
            f"Неизвестный интерфейс: {interface!r}. "
            "Ожидается streamlit, telegram или console."
        )


if __name__ == "__main__":
    main()
