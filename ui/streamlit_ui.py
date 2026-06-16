# coding: utf-8
"""
Контракт виджетов Streamlit UI.

Используется в тестах: ключи виджетов и ожидаемые элементы по экранам.
При изменении streamlit_app.py обновите этот файл или тесты упадут.
"""

from __future__ import annotations

from core.models import Screen

# Ключи st.*_input / st.button — уникальны в приложении.
START_WIDGET_KEYS = ("name_input", "btn_start")
DIARY_WIDGET_KEYS = ("diary_input", "btn_diary_save", "btn_diary_back")
MAIN_MENU_BUTTON_KEY_PREFIX = "btn_menu_"
MAIN_MENU_BUTTON_COUNT = 3

# Имена сообщений из dialog_messages.json для подписей Streamlit.
START_MESSAGE_NAMES = ("browser_name_label", "browser_btn_continue")
DIARY_MESSAGE_NAMES = ("browser_diary_label", "browser_btn_save")
HEADER_MESSAGE_NAMES = ("browser_page_title", "browser_title")
BACK_TO_MENU_BUTTON_NAME = "back_to_menu"

# Экраны, для которых в app.py есть отдельные ветки рендера.
SCREENS_WITH_DEDICATED_BRANCH = (
    Screen.START.value,
    Screen.DIARY_WAIT.value,
)

# Паттерны, которые приводят к CachedWidgetWarning или нестабильным cookie.
FORBIDDEN_STREAMLIT_PATTERNS = (
    "@st.cache_resource",
    "CookieManager",
    "extra_streamlit_components",
)

# Официальный способ чтения cookie в Streamlit >= 1.37.
REQUIRED_COOKIE_READ = "st.context.cookies"
