# coding: utf-8
"""
AppService — оркестратор ядра.

Цель:
    Связать brain, collectors и logging в единую точку для UI-клиентов.

Вход:
    user_id, channel, действие пользователя.

Выход:
    AppResponse для отображения клиентом.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from core.brain import (
    is_back_to_menu,
    match_menu_button,
    on_diary_empty,
    on_diary_saved,
    on_empty_name,
    on_main_menu_reminder,
    on_name_entered,
    on_option_1_result,
    on_option_2_result,
    on_option_3_prompt,
    on_start,
)
from core.collectors.jokes import get_random_joke
from core.collectors.weather import get_current_temperature
from core.logging.base import EventLogger
from core.models import (
    ACTION_BACK_TO_MENU,
    ACTION_DIARY_TEXT,
    ACTION_NAME_ENTERED,
    ACTION_OPTION_1,
    ACTION_OPTION_2,
    ACTION_OPTION_3,
    AppResponse,
    Screen,
)


class AppService:
    """Единая точка входа бизнес-логики для всех интерфейсов."""

    def __init__(self, logger: EventLogger, config: dict[str, Any]) -> None:
        self.logger = logger
        self.config = config
        self.jokes_path = config.get("paths", {}).get("jokes_file", "data/jokes.json")

    def handle_start(self, user_id: int, channel: str) -> AppResponse:
        """
        Первый визит / команда start.

        :param user_id: внутренний идентификатор пользователя
        :param channel: streamlit | telegram | console
        :return: ответ для UI
        """
        # events.user_id ссылается на users — строка нужна до start_screen_visit.
        # Имя и дата регистрации обновятся при вводе user_name.
        self._ensure_user_stub(user_id, channel)
        self.logger.log_event(
            user_id=user_id,
            event_name="start_screen_visit",
            channel=channel,
            event_parameters=None,
        )
        return on_start()

    def _ensure_user_stub(self, user_id: int, channel: str) -> None:
        """
        Создаёт или обновляет заглушку пользователя до регистрации.

        user_name пустой до ввода имени; registration_date перезапишется при регистрации.
        """
        now = datetime.now()
        self.logger.upsert_user(
            user_id=user_id,
            user_name="",
            registration_date=now,
            registration_channel=channel,
            last_active_at=now,
        )

    def handle_action(
        self,
        user_id: int,
        channel: str,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> AppResponse:
        """
        Обрабатывает действие пользователя на текущем экране.

        :param user_id: внутренний идентификатор
        :param channel: канал интерфейса
        :param action: тип действия (см. models.ACTION_*)
        :param payload: user_name, registration_date (iso), text и др.
        :return: ответ для UI
        """
        payload = payload or {}

        if action == ACTION_NAME_ENTERED:
            return self._handle_name_entered(user_id, channel, payload)

        if action == ACTION_OPTION_1:
            return self._handle_option_1(user_id, channel, payload)

        if action == ACTION_OPTION_2:
            return self._handle_option_2(user_id, channel, payload)

        if action == ACTION_OPTION_3:
            return self._handle_option_3(user_id, channel, payload)

        if action == ACTION_DIARY_TEXT:
            return self._handle_diary_text(user_id, channel, payload)

        if action == ACTION_BACK_TO_MENU:
            return self._handle_back_to_menu(user_id, channel, payload)

        # UI может передать сырой текст кнопки — разбираем здесь
        raw_text = str(payload.get("text", "")).strip()
        if raw_text:
            return self._handle_raw_text(user_id, channel, payload, raw_text)

        return on_main_menu_reminder()

    def _handle_raw_text(
        self,
        user_id: int,
        channel: str,
        payload: dict[str, Any],
        raw_text: str,
    ) -> AppResponse:
        """Разбор текста кнопки или ввода по текущему контексту экрана."""
        screen = payload.get("screen")

        if screen == Screen.START.value or screen == Screen.START:
            payload_with_text = dict(payload)
            payload_with_text["text"] = raw_text
            return self._handle_name_entered(user_id, channel, payload_with_text)

        if screen == Screen.DIARY_WAIT.value or screen == Screen.DIARY_WAIT:
            if is_back_to_menu(raw_text):
                return self._handle_back_to_menu(user_id, channel, payload)
            payload_with_text = dict(payload)
            payload_with_text["text"] = raw_text
            return self._handle_diary_text(user_id, channel, payload_with_text)

        matched = match_menu_button(raw_text)
        if matched == "option_1":
            return self._handle_option_1(user_id, channel, payload)
        if matched == "option_2":
            return self._handle_option_2(user_id, channel, payload)
        if matched == "option_3":
            return self._handle_option_3(user_id, channel, payload)

        self._touch_user(user_id, channel, payload)
        return on_main_menu_reminder()

    def _handle_name_entered(
        self,
        user_id: int,
        channel: str,
        payload: dict[str, Any],
    ) -> AppResponse:
        user_name = str(payload.get("text", "")).strip()
        if not user_name:
            return on_empty_name()

        now = datetime.now()
        self.logger.upsert_user(
            user_id=user_id,
            user_name=user_name,
            registration_date=now,
            registration_channel=channel,
            last_active_at=now,
        )
        self.logger.log_event(
            user_id=user_id,
            event_name="registration",
            channel=channel,
            event_parameters={"user_name": user_name},
        )
        self.logger.log_event(
            user_id=user_id,
            event_name="main_menu_visit",
            channel=channel,
            event_parameters=None,
        )
        return on_name_entered(user_name)

    def _handle_option_1(
        self,
        user_id: int,
        channel: str,
        payload: dict[str, Any],
    ) -> AppResponse:
        self._touch_user(user_id, channel, payload)
        self.logger.log_event(
            user_id=user_id,
            event_name="option1_visit",
            channel=channel,
            event_parameters=None,
        )

        weather_cfg = self.config["weatherapi"]
        weather_text = get_current_temperature(
            api_key=weather_cfg["api_key"],
            base_url=weather_cfg["url"],
            method=weather_cfg["method"],
            city=weather_cfg["city"],
        )
        return on_option_1_result(weather_text)

    def _handle_option_2(
        self,
        user_id: int,
        channel: str,
        payload: dict[str, Any],
    ) -> AppResponse:
        self._touch_user(user_id, channel, payload)
        self.logger.log_event(
            user_id=user_id,
            event_name="option2_visit",
            channel=channel,
            event_parameters=None,
        )

        jokes_path = Path(self.jokes_path)
        joke_text = get_random_joke(jokes_path)
        return on_option_2_result(joke_text)

    def _handle_option_3(
        self,
        user_id: int,
        channel: str,
        payload: dict[str, Any],
    ) -> AppResponse:
        self._touch_user(user_id, channel, payload)
        self.logger.log_event(
            user_id=user_id,
            event_name="option3_visit",
            channel=channel,
            event_parameters=None,
        )
        return on_option_3_prompt()

    def _handle_diary_text(
        self,
        user_id: int,
        channel: str,
        payload: dict[str, Any],
    ) -> AppResponse:
        diary_text = str(payload.get("text", "")).strip()
        if not diary_text:
            return on_diary_empty()

        self._touch_user(user_id, channel, payload)
        self.logger.log_event(
            user_id=user_id,
            event_name="diary_message_sent",
            channel=channel,
            event_parameters={"text": diary_text},
        )
        return on_diary_saved()

    def _handle_back_to_menu(
        self,
        user_id: int,
        channel: str,
        payload: dict[str, Any],
    ) -> AppResponse:
        self._touch_user(user_id, channel, payload)
        self.logger.log_event(
            user_id=user_id,
            event_name="main_menu_visit",
            channel=channel,
            event_parameters=None,
        )
        return on_main_menu_reminder()

    def _touch_user(
        self,
        user_id: int,
        channel: str,
        payload: dict[str, Any],
    ) -> None:
        """
        Обновляет last_active_at и перезаписывает поля users.

        UI после регистрации передаёт user_name и registration_date в payload.
        """
        user_name = payload.get("user_name")
        if not user_name:
            return

        registration_date = self._parse_registration_date(payload)
        now = datetime.now()

        self.logger.upsert_user(
            user_id=user_id,
            user_name=str(user_name),
            registration_date=registration_date,
            registration_channel=channel,
            last_active_at=now,
        )

    def _parse_registration_date(self, payload: dict[str, Any]) -> datetime:
        raw = payload.get("registration_date")
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, str) and raw:
            return datetime.fromisoformat(raw)
        return datetime.now()
