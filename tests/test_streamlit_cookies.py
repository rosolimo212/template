# coding: utf-8
"""Тесты cookie-сессии Streamlit (без Streamlit runtime)."""

from __future__ import annotations

from ui.streamlit_cookies import (
    apply_cookie_to_state,
    decode_session_cookie,
    encode_session_cookie,
    session_cookie_payload,
)


def test_encode_decode_roundtrip() -> None:
    raw = encode_session_cookie(
        {
            "external_user_id": "abc-123",
            "screen": "main_menu",
            "user_name": "Роман",
        }
    )
    data = decode_session_cookie(raw)
    assert data["external_user_id"] == "abc-123"
    assert data["screen"] == "main_menu"
    assert data["user_name"] == "Роман"


def test_decode_invalid_returns_empty() -> None:
    assert decode_session_cookie("not-json") == {}
    assert decode_session_cookie(None) == {}


def test_apply_cookie_to_state() -> None:
    state: dict = {}
    apply_cookie_to_state(
        state,
        {
            "external_user_id": "uuid-1",
            "screen": "diary_wait",
            "user_name": "Anna",
            "registration_date": "2026-06-16T10:00:00",
        },
    )
    assert state["external_user_id"] == "uuid-1"
    assert state["screen"] == "diary_wait"
    assert state["user_name"] == "Anna"


def test_session_cookie_payload_skips_empty() -> None:
    payload = session_cookie_payload({"external_user_id": "x", "screen": ""})
    assert payload == {"external_user_id": "x"}
