# coding: utf-8
"""Тесты user_id hash."""

from __future__ import annotations

from core.identity import make_user_id


def test_make_user_id_stable() -> None:
    a = make_user_id("streamlit", "abc-123")
    b = make_user_id("streamlit", "abc-123")
    assert a == b
    assert len(a) == 64


def test_make_user_id_channel_matters() -> None:
    a = make_user_id("streamlit", "same")
    b = make_user_id("telegram", "same")
    assert a != b
