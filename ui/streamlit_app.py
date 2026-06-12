# coding: utf-8
"""
Streamlit-клиент (тестовый браузерный интерфейс).

Цель:
    Тонкий адаптер над AppService для локального stage.

TODO:
    Полный сценарий MVP в фазе 5.
"""

from __future__ import annotations

from typing import Any

from ui.base import build_app_service


def run_streamlit(config: dict[str, Any]) -> None:
    """
    Запускает streamlit-приложение.

    :param config: конфиг из config.yaml
    """
    import streamlit as st

    st.set_page_config(page_title="Template App", page_icon="🧪")
    service = build_app_service(config)

    if "user_id" not in st.session_state:
        st.session_state.user_id = service.logger.allocate_user_id()
        response = service.handle_start(st.session_state.user_id, "streamlit")
        st.session_state.screen = response.screen.value

    st.title("Template — stage UI")
    st.info("Каркас фазы 0. Полный сценарий будет в фазе 5.")
    st.write(f"user_id: {st.session_state.user_id}")
