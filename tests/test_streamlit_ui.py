# coding: utf-8
"""Контракт UI Streamlit: виджеты на месте, без опасных паттернов."""

from __future__ import annotations

import re
from pathlib import Path

from core.messages import menu_buttons
from ui import streamlit_app
from ui.streamlit_ui import (
    DIARY_MESSAGE_NAMES,
    DIARY_WIDGET_KEYS,
    FORBIDDEN_STREAMLIT_PATTERNS,
    HEADER_MESSAGE_NAMES,
    MAIN_MENU_BUTTON_COUNT,
    MAIN_MENU_BUTTON_KEY_PREFIX,
    REQUIRED_COOKIE_READ,
    START_MESSAGE_NAMES,
    START_WIDGET_KEYS,
)


def _app_source() -> str:
    return Path(streamlit_app.__file__).read_text(encoding="utf-8")


def test_start_screen_widgets_present() -> None:
    source = _app_source()
    for key in START_WIDGET_KEYS:
        assert f'key="{key}"' in source


def test_diary_screen_widgets_present() -> None:
    source = _app_source()
    for key in DIARY_WIDGET_KEYS:
        assert f'key="{key}"' in source


def test_main_menu_dynamic_buttons_pattern() -> None:
    source = _app_source()
    assert MAIN_MENU_BUTTON_KEY_PREFIX in source
    assert "state.get(\"buttons\"" in source or "state.get('buttons'" in source
    labels = menu_buttons("streamlit")
    assert len(labels) == MAIN_MENU_BUTTON_COUNT


def test_start_screen_uses_dialog_messages() -> None:
    source = _app_source()
    for name in START_MESSAGE_NAMES:
        assert f'message("{name}", "streamlit")' in source


def test_diary_screen_uses_dialog_messages() -> None:
    source = _app_source()
    for name in DIARY_MESSAGE_NAMES:
        assert f'message("{name}", "streamlit")' in source
    assert 'button("back_to_menu", "streamlit")' in source


def test_header_uses_dialog_messages() -> None:
    source = _app_source()
    for name in HEADER_MESSAGE_NAMES:
        assert f'message("{name}", "streamlit")' in source


def test_screen_branches_exist() -> None:
    source = _app_source()
    assert "Screen.START.value" in source
    assert "Screen.DIARY_WAIT.value" in source
    assert "else:" in source  # main menu branch


def test_no_forbidden_streamlit_patterns() -> None:
    """Регрессия: CachedWidgetWarning / нестабильный CookieManager."""
    source = _app_source()
    for pattern in FORBIDDEN_STREAMLIT_PATTERNS:
        assert pattern not in source


def test_uses_official_context_cookies_for_read() -> None:
    source = _app_source()
    assert REQUIRED_COOKIE_READ in source


def test_persist_cookie_at_end_of_run() -> None:
    source = _app_source()
    assert "persist_external_id_cookie" in source


def test_init_uses_handle_start_not_manual_screen_restore() -> None:
    """Регрессия: после регистрации меню из handle_start, не из cookie screen."""
    source = _app_source()
    assert "service.handle_start(identity, \"streamlit\")" in source
    assert "_restore_ui_for_returning_user" not in source
    assert "apply_cookie_to_state" not in source


def test_streamlit_import_has_no_syntax_errors() -> None:
    import importlib

    importlib.import_module("ui.streamlit_app")


def test_streamlit_module_level_no_obvious_warnings_in_source() -> None:
    """
    Статическая проверка до запуска: нет set_page_config после виджетов и т.п.

    set_page_config должен быть в начале run_streamlit.
    """
    source = _app_source()
    config_idx = source.index("st.set_page_config")
    title_idx = source.index("st.title(")
    assert config_idx < title_idx
