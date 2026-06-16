# coding: utf-8
"""Проверка отсутствия типичных Streamlit warnings (статика + import)."""

from __future__ import annotations

import importlib
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_app_import_no_user_warnings() -> None:
    """Импорт модуля не должен эмитить UserWarning/DeprecationWarning."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import ui.streamlit_app as app

        importlib.reload(app)

    relevant = [
        w
        for w in caught
        if issubclass(w.category, (UserWarning, DeprecationWarning))
        and "streamlit" in str(w.message).lower()
    ]
    assert relevant == [], [str(w.message) for w in relevant]


def test_no_cached_widget_antipattern_in_sources() -> None:
    """CachedWidgetWarning: виджеты внутри @st.cache_*."""
    app_src = (ROOT / "ui" / "streamlit_app.py").read_text(encoding="utf-8")
    cookies_src = (ROOT / "ui" / "streamlit_cookies.py").read_text(encoding="utf-8")
    combined = app_src + cookies_src
    assert "@st.cache_resource" not in combined
    assert "@st.cache_data" not in combined
    assert "CookieManager" not in combined


@pytest.mark.skipif(
    not (ROOT / "config.yaml").exists(),
    reason="config.yaml нужен для smoke-import build_app_service",
)
def test_build_app_service_import_with_streamlit_stack() -> None:
    """Smoke: конфиг + сервис поднимаются без warnings при импорте UI."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from core.config import load_app_config
        from ui.base import build_app_service

        build_app_service(load_app_config(ROOT / "config.yaml"))

    assert not any(
        issubclass(w.category, UserWarning) and "CachedWidget" in str(w.message)
        for w in caught
    )
