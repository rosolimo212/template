# coding: utf-8
"""Telegram-клиент на aiogram 3."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from core.messages import (
    change_name_button,
    confirm_name_button,
    message,
)
from core.models import (
    ACTION_DIARY_TEXT,
    ACTION_NAME_CHANGE,
    ACTION_NAME_CONFIRMED,
    ACTION_NAME_ENTERED,
    Screen,
    UserIdentity,
)
from ui.base import build_app_service
from ui.helpers import apply_response, build_payload, store_identity


class Flow(StatesGroup):
    start = State()
    name_confirm = State()
    main_menu = State()
    diary = State()


def _make_keyboard(buttons: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in buttons]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def _send_response(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = data.get("last_text", "")
    buttons = data.get("buttons", [])
    markup = _make_keyboard(buttons) if buttons else None
    await message.answer(text, reply_markup=markup)


def _identity_from_data(data: dict[str, Any]) -> UserIdentity:
    return UserIdentity(
        user_id=data["user_id"],
        internal_user_id=int(data["internal_user_id"]),
        external_user_id=data["external_user_id"],
    )


def _state_for_screen(screen: Screen) -> State:
    if screen == Screen.START:
        return Flow.start
    if screen == Screen.NAME_CONFIRM:
        return Flow.name_confirm
    if screen == Screen.DIARY_WAIT:
        return Flow.diary
    return Flow.main_menu


def _sync_profile(service, identity: UserIdentity, session_state: dict[str, Any]) -> None:
    profile = service.logger.get_user_profile(identity)
    if not profile:
        return

    user_name = str(profile.get("user_name") or "").strip()
    if user_name:
        session_state["user_name"] = user_name

    reg_date = profile.get("registration_date")
    if reg_date is not None:
        if isinstance(reg_date, datetime):
            session_state["registration_date"] = reg_date.isoformat()
        else:
            session_state["registration_date"] = str(reg_date)


async def run_telegram(config: dict[str, Any]) -> None:
    token = config["telegram"]["token"]
    service = build_app_service(config)

    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext) -> None:
        await state.clear()
        external_user_id = str(message.from_user.id)
        identity = service.logger.ensure_user("telegram", external_user_id)
        context = {
            "telegram_username": message.from_user.username or "",
        }
        response = service.handle_start(identity, "telegram", context)

        session_state: dict[str, Any] = {}
        store_identity(session_state, identity)
        _sync_profile(service, identity, session_state)
        apply_response(session_state, response)
        await state.update_data(**session_state)
        await state.set_state(_state_for_screen(response.screen))
        await _send_response(message, state)

    @dp.message(Flow.start)
    async def on_start_screen(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        identity = _identity_from_data(data)
        user_name = (message.text or "").strip()

        response = service.handle_action(
            identity,
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
        await state.set_state(_state_for_screen(response.screen))
        await _send_response(message, state)

    @dp.message(Flow.name_confirm)
    async def on_name_confirm(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        identity = _identity_from_data(data)
        text = (message.text or "").strip()
        payload = build_payload(
            user_name=data.get("user_name"),
            registration_date=data.get("registration_date"),
            text=text,
            screen=Screen.NAME_CONFIRM,
        )

        if text == confirm_name_button("telegram"):
            action = ACTION_NAME_CONFIRMED
        elif text == change_name_button("telegram"):
            action = ACTION_NAME_CHANGE
        else:
            action = ACTION_NAME_ENTERED
            payload = build_payload(text=text)

        response = service.handle_action(identity, "telegram", action, payload)

        reg_name = None
        reg_date = None
        if response.screen == Screen.MAIN_MENU:
            _sync_profile(service, identity, data)
            reg_name = data.get("user_name")
            reg_date = data.get("registration_date")

        apply_response(
            data,
            response,
            user_name=reg_name,
            registration_date=reg_date,
        )
        await state.update_data(**data)
        await state.set_state(_state_for_screen(response.screen))
        await _send_response(message, state)

    @dp.message(Flow.main_menu, F.text)
    async def on_main_menu(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        identity = _identity_from_data(data)
        text = message.text or ""

        response = service.handle_action(
            identity,
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
        identity = _identity_from_data(data)
        text = message.text or ""

        if text.strip().casefold() == "в главное меню":
            response = service.handle_action(
                identity,
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
                identity,
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
