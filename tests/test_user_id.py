# coding: utf-8
"""Тесты выдачи internal_user_id без коллизий."""

from __future__ import annotations

from pathlib import Path

from core.identity import make_user_id
from core.logging.noop import NoopLogger


def test_noop_logger_incremental_internal_ids(tmp_path: Path) -> None:
    counter_file = tmp_path / "user_counter.json"
    logger = NoopLogger(counter_path=counter_file)

    a = logger.ensure_user("streamlit", "session-a")
    b = logger.ensure_user("streamlit", "session-b")

    assert a.internal_user_id != b.internal_user_id
    assert a.user_id != b.user_id
    assert make_user_id("streamlit", "session-a") == a.user_id


def test_noop_same_external_reuses_identity(tmp_path: Path) -> None:
    counter_file = tmp_path / "user_counter.json"
    logger = NoopLogger(counter_path=counter_file)

    first = logger.ensure_user("console", "same-id")
    second = logger.ensure_user("console", "same-id")
    assert first == second
