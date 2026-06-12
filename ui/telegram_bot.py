# coding: utf-8
"""
Telegram-клиент на aiogram 3.

Цель:
    Тонкий адаптер над AppService; telegram не обязателен для работы системы.

Вход:
    config с telegram.token.

Выход:
    Полный сценарий MVP в telegram.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from core.models import ACTION_DIARY_TEXT, ACTION_NAME_ENTERED, Screen
from ui.base import build_app_service
from ui.helpers import apply_response, build_payload


class Flow(StatesGroup):
    """Состояния пользователя в telegram."""

    start = State()
    main_menu = State()
    diary = State()


def _make_keyboard(buttons: list[str]) -> ReplyKeyboardMarkup:
    """Reply-клавиатура из списка подписей."""
    rows = [[KeyboardButton(text=label)] for label in buttons]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def _send_response(message: Message, state: FSMContext) -> None:
    """Отправляет пользователю последний текст и клавиатуру из FSM data."""
    data = await state.get_data()
    text = data.get("last_text", "")
    buttons = data.get("buttons", [])
    markup = _make_keyboard(buttons) if buttons else None
    await message.answer(text, reply_markup=markup)


async def run_telegram(config: dict[str, Any]) -> None:
    """
    Запускает telegram-бота.

    :param config: конфиг из config.yaml
    """
    token = config["telegram"]["token"]
    service = build_app_service(config)

    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext) -> None:
        await state.clear()
        user_id = service.logger.allocate_user_id()
        response = service.handle_start(user_id, "telegram")

        session_state: dict[str, Any] = {"user_id": user_id}
        apply_response(session_state, response)
        await state.update_data(**session_state)
        await state.set_state(Flow.start)
        await _send_response(message, state)

    @dp.message(Flow.start)
    async def on_start_screen(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        user_id = data["user_id"]
        user_name = (message.text or "").strip()

        response = service.handle_action(
            user_id,
            "telegram",
            ACTION_NAME_ENTERED,
            build_payload(text=user_name),
        )

        reg_name = None
        reg_date = None
        if response.screen == Screen.MAIN_MENU:
            reg_name = user_name
            reg_date = datetime.now().isoformat()

        apply_response(
            data,
            response,
            user_name=reg_name,
            registration_date=reg_date,
        )
        await state.update_data(**data)
        await state.set_state(Flow.main_menu)
        await _send_response(message, state)

    @dp.message(Flow.main_menu, F.text)
    async def on_main_menu(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        user_id = data["user_id"]
        text = message.text or ""

        response = service.handle_action(
            user_id,
            "telegram",
            "raw",
            {
                **build_payload(
                    user_name=data.get("user_name"),
                    registration_date=data.get("registration_date"),
                ),
                **build_payload(text=text, screen=Screen.MAIN_MENU),
            },
        )
        apply_response(data, response)

        if response.screen == Screen.DIARY_WAIT:
            await state.set_state(Flow.diary)
        else:
            await state.set_state(Flow.main_menu)

        await state.update_data(**data)
        await _send_response(message, state)

    @dp.message(Flow.diary, F.text)
    async def on_diary(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        user_id = data["user_id"]
        text = message.text or ""

        if text.strip().casefold() == "в главное меню":
            response = service.handle_action(
                user_id,
                "telegram",
                "raw",
                {
                    **build_payload(
                        user_name=data.get("user_name"),
                        registration_date=data.get("registration_date"),
                    ),
                    **build_payload(text=text, screen=Screen.DIARY_WAIT),
                },
            )
        else:
            response = service.handle_action(
                user_id,
                "telegram",
                ACTION_DIARY_TEXT,
                {
                    **build_payload(
                        user_name=data.get("user_name"),
                        registration_date=data.get("registration_date"),
                    ),
                    **build_payload(text=text, screen=Screen.DIARY_WAIT),
                },
            )

        apply_response(data, response)
        await state.set_state(Flow.main_menu)
        await state.update_data(**data)
        await _send_response(message, state)

    await dp.start_polling(bot)
