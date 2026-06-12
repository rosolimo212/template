# coding: utf-8
"""
Streamlit-клиент (тестовый браузерный интерфейс).

Цель:
    Тонкий адаптер над AppService для локального stage.

Вход:
    config из config.yaml.

Выход:
    Интерактивный браузерный сценарий MVP.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.models import ACTION_DIARY_TEXT, ACTION_NAME_ENTERED, Screen
from ui.base import build_app_service
from ui.helpers import apply_response, build_payload


def _init_session(service, state) -> None:
    """Первый визит: user_id и стартовый экран."""
    state.user_id = service.logger.allocate_user_id()
    response = service.handle_start(state.user_id, "streamlit")
    apply_response(state, response)
    state.initialized = True


def _registered_payload(state) -> dict[str, Any]:
    return build_payload(
        user_name=getattr(state, "user_name", None),
        registration_date=getattr(state, "registration_date", None),
    )


def _handle_user_input(service, state, text: str) -> None:
    """Отправляет ввод пользователя в AppService."""
    screen = getattr(state, "screen", Screen.START.value)

    if screen == Screen.START.value:
        response = service.handle_action(
            state.user_id,
            "streamlit",
            ACTION_NAME_ENTERED,
            build_payload(text=text),
        )
        user_name = None
        reg_date = None
        if response.screen == Screen.MAIN_MENU:
            user_name = text.strip()
            reg_date = datetime.now().isoformat()
        apply_response(
            state,
            response,
            user_name=user_name,
            registration_date=reg_date,
        )
        return

    if screen == Screen.DIARY_WAIT.value:
        response = service.handle_action(
            state.user_id,
            "streamlit",
            ACTION_DIARY_TEXT,
            {**_registered_payload(state), **build_payload(text=text, screen=screen)},
        )
        apply_response(state, response)
        return

    response = service.handle_action(
        state.user_id,
        "streamlit",
        "raw",
        {
            **_registered_payload(state),
            **build_payload(text=text, screen=screen),
        },
    )
    apply_response(state, response)


def run_streamlit(config: dict[str, Any]) -> None:
    """
    Запускает streamlit-приложение.

    :param config: конфиг из config.yaml
    """
    import streamlit as st

    st.set_page_config(page_title="Template App", page_icon="🧪")
    service = build_app_service(config)
    state = st.session_state

    if not state.get("initialized"):
        _init_session(service, state)

    st.title("Template")
    st.caption(f"user_id: {state.user_id} | экран: {state.screen}")
    st.markdown(state.get("last_text", ""))

    screen = state.get("screen", Screen.START.value)

    if screen == Screen.START.value:
        name = st.text_input("Ваше имя", key="name_input")
        if st.button("Продолжить", key="btn_start"):
            _handle_user_input(service, state, name)
            st.rerun()

    elif screen == Screen.DIARY_WAIT.value:
        diary = st.text_area("Запись в дневник", key="diary_input")
        cols = st.columns(2)
        with cols[0]:
            if st.button("Сохранить", key="btn_diary_save"):
                _handle_user_input(service, state, diary)
                st.rerun()
        with cols[1]:
            if st.button("В главное меню", key="btn_diary_back"):
                _handle_user_input(service, state, "В главное меню")
                st.rerun()

    else:
        buttons = state.get("buttons", [])
        for idx, label in enumerate(buttons):
            if st.button(label, key=f"btn_menu_{idx}"):
                _handle_user_input(service, state, label)
                st.rerun()


if __name__ == "__main__":
    from pathlib import Path
    import sys

    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT))

    from core.config import load_app_config

    run_streamlit(load_app_config(ROOT / "config.yaml"))
