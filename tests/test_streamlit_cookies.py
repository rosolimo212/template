# coding: utf-8
"""Тесты cookie Streamlit (без Streamlit runtime)."""

from __future__ import annotations

import base64
import json

from ui.streamlit_cookies import (
    EXTERNAL_COOKIE_NAME,
    is_valid_external_id,
    new_streamlit_external_id,
    read_external_id_from_cookies,
    resolve_external_user_id,
)


def test_is_valid_external_id() -> None:
    assert is_valid_external_id(new_streamlit_external_id())
    assert not is_valid_external_id("not-uuid")


def test_read_external_id_direct() -> None:
    uid = "d358d3b8-4e6d-421c-89bf-eaef895df2f3"
    assert read_external_id_from_cookies({EXTERNAL_COOKIE_NAME: uid}) == uid


def test_read_external_id_from_legacy_json() -> None:
    uid = "50296149-d145-41eb-a34c-b2da979d2b16"
    blob = base64.urlsafe_b64encode(
        json.dumps({"external_user_id": uid, "screen": "start"}).encode()
    ).decode()
    assert read_external_id_from_cookies({"template_browser_session": blob}) == uid


def test_resolve_uses_cookie_not_new_uuid() -> None:
    uid = "d358d3b8-4e6d-421c-89bf-eaef895df2f3"
    state: dict = {}
    resolved = resolve_external_user_id(state, {EXTERNAL_COOKIE_NAME: uid})
    assert resolved == uid
    assert state["external_user_id"] == uid


def test_resolve_generates_when_no_cookie() -> None:
    state: dict = {}
    resolved = resolve_external_user_id(state, {})
    assert is_valid_external_id(resolved)
    assert state["external_user_id"] == resolved


def test_resolve_does_not_restore_screen_from_legacy() -> None:
    """Регрессия: screen в legacy cookie не должен попадать в state."""
    uid = "d358d3b8-4e6d-421c-89bf-eaef895df2f3"
    legacy = json.dumps({"external_user_id": uid, "screen": "start"})
    state: dict = {}
    resolve_external_user_id(state, {"template_browser_session": legacy})
    assert state["external_user_id"] == uid
    assert "screen" not in state
