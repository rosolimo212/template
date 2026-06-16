# coding: utf-8
"""Streamlit-клиент."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.brain import on_name_entered, on_option_3_prompt, on_start
from core.messages import button, message
from core.models import ACTION_DIARY_TEXT, ACTION_NAME_ENTERED, Screen
from ui.base import build_app_service
from ui.helpers import (
    apply_response,
    build_payload,
    get_identity,
    init_user_identity,
)
from ui.streamlit_cookies import (
    COOKIE_NAME,
    apply_cookie_to_state,
    cookie_expires_at,
    decode_session_cookie,
    encode_session_cookie,
    session_cookie_payload,
)


def _get_cookie_manager():
    """Один CookieManager на процесс Streamlit."""
    import extra_streamlit_components as stx
    import streamlit as st

    @st.cache_resource
    def _manager():
        return stx.CookieManager(key="template_cookie_manager")

    return _manager()


def _read_session_cookie(cookie_manager) -> dict[str, str]:
    """
    Читает cookie браузера.

    На первом рендере CookieManager может вернуть None — нужен st.stop() и rerun.
    """
    raw = cookie_manager.get(cookie=COOKIE_NAME)
    return decode_session_cookie(raw)


def _write_session_cookie(cookie_manager, state) -> None:
    """Сохраняет session state в cookie браузера."""
    payload = session_cookie_payload(state)
    if not payload.get("external_user_id"):
        return
    cookie_manager.set(
        COOKIE_NAME,
        encode_session_cookie(payload),
        expires_at=cookie_expires_at(),
    )


def _restore_ui_for_returning_user(
    service,
    state,
    identity,
    *,
    db_user_name: str,
) -> None:
    """
    Восстанавливает экран из cookie + имя из БД.

    Если cookie потерян, но пользователь зарегистрирован — главное меню.
    """
    screen = state.get("screen", Screen.START.value)
    user_name = state.get("user_name") or db_user_name
    reg_date = state.get("registration_date")

    if screen == Screen.DIARY_WAIT.value:
        response = on_option_3_prompt("streamlit")
    elif screen == Screen.MAIN_MENU.value or db_user_name:
        response = on_name_entered(user_name, "streamlit")
    else:
        response = on_start("streamlit")

    apply_response(
        state,
        response,
        user_name=user_name if db_user_name or user_name else None,
        registration_date=reg_date,
    )


def _init_session(service, state, cookie_manager) -> None:
    """
    Первый прогон сессии Streamlit: cookie → identity → экран.

    Streamlit иногда гоняет скрипт дважды — флаг initialized ставим сразу.
    """
    if state.get("initialized"):
        return
    state["initialized"] = True

    cookie_data = _read_session_cookie(cookie_manager)
    apply_cookie_to_state(state, cookie_data)

    identity = init_user_identity(service, state, "streamlit")

    profile = service.logger.get_user_profile(identity)
    db_user_name = (profile or {}).get("user_name", "").strip()

    if db_user_name:
        if profile and profile.get("registration_date") and not state.get(
            "registration_date"
        ):
            reg = profile["registration_date"]
            if isinstance(reg, datetime):
                state["registration_date"] = reg.isoformat()
            else:
                state["registration_date"] = str(reg)
        _restore_ui_for_returning_user(
            service,
            state,
            identity,
            db_user_name=db_user_name,
        )
    else:
        response = service.handle_start(identity, "streamlit")
        apply_response(state, response)

    _write_session_cookie(cookie_manager, state)


def _registered_payload(state) -> dict[str, Any]:
    return build_payload(
        user_name=getattr(state, "user_name", None),
        registration_date=getattr(state, "registration_date", None),
    )


def _handle_user_input(service, state, cookie_manager, text: str) -> None:
    identity = get_identity(state)
    screen = getattr(state, "screen", Screen.START.value)

    if screen == Screen.START.value:
        response = service.handle_action(
            identity,
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
        _write_session_cookie(cookie_manager, state)
        return

    if screen == Screen.DIARY_WAIT.value:
        response = service.handle_action(
            identity,
            "streamlit",
            ACTION_DIARY_TEXT,
            {**_registered_payload(state), **build_payload(text=text, screen=screen)},
        )
        apply_response(state, response)
        _write_session_cookie(cookie_manager, state)
        return

    response = service.handle_action(
        identity,
        "streamlit",
        "raw",
        {
            **_registered_payload(state),
            **build_payload(text=text, screen=screen),
        },
    )
    apply_response(state, response)
    _write_session_cookie(cookie_manager, state)


def run_streamlit(config: dict[str, Any]) -> None:
    import streamlit as st

    st.set_page_config(
        page_title=message("browser_page_title", "streamlit"),
        page_icon="🧪",
    )

    cookie_manager = _get_cookie_manager()
    # CookieManager подгружает document.cookie асинхронно — первый run может быть пустым.
    if cookie_manager.get_all() is None:
        st.stop()

    service = build_app_service(config)
    state = st.session_state

    if not state.get("initialized"):
        _init_session(service, state, cookie_manager)

    st.title(message("browser_title", "streamlit"))
    st.caption(
        f"user_id: {state.user_id[:12]}… | "
        f"internal: {state.internal_user_id} | "
        f"external: {state.external_user_id[:8]}… | "
        f"экран: {state.screen}"
    )
    st.markdown(state.get("last_text", ""))

    screen = state.get("screen", Screen.START.value)

    if screen == Screen.START.value:
        name = st.text_input(message("browser_name_label", "streamlit"), key="name_input")
        if st.button(message("browser_btn_continue", "streamlit"), key="btn_start"):
            _handle_user_input(service, state, cookie_manager, name)
            st.rerun()

    elif screen == Screen.DIARY_WAIT.value:
        diary = st.text_area(message("browser_diary_label", "streamlit"), key="diary_input")
        cols = st.columns(2)
        with cols[0]:
            if st.button(message("browser_btn_save", "streamlit"), key="btn_diary_save"):
                _handle_user_input(service, state, cookie_manager, diary)
                st.rerun()
        with cols[1]:
            if st.button(button("back_to_menu", "streamlit"), key="btn_diary_back"):
                _handle_user_input(
                    service,
                    state,
                    cookie_manager,
                    button("back_to_menu", "streamlit"),
                )
                st.rerun()

    else:
        buttons = state.get("buttons", [])
        for idx, label in enumerate(buttons):
            if st.button(label, key=f"btn_menu_{idx}"):
                _handle_user_input(service, state, cookie_manager, label)
                st.rerun()


if __name__ == "__main__":
    from core.config import load_app_config

    run_streamlit(load_app_config(ROOT / "config.yaml"))
