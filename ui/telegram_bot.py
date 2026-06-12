# coding: utf-8
"""
Telegram-клиент на aiogram 3.

Цель:
    Тонкий адаптер над AppService; telegram не обязателен для работы системы.

TODO:
    Полный сценарий MVP в фазе 5.
"""

from __future__ import annotations

from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from ui.base import build_app_service


async def run_telegram(config: dict[str, Any]) -> None:
    """
    Запускает telegram-бота.

    :param config: конфиг из config.yaml
    """
    token = config["telegram"]["token"]
    service = build_app_service(config)

    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        user_id = service.logger.allocate_user_id()
        response = service.handle_start(user_id, "telegram")
        await message.answer(response.text)

    await dp.start_polling(bot)
