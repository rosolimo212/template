# coding: utf-8
"""Тесты выдачи user_id без коллизий (noop-логгер)."""

from __future__ import annotations

from pathlib import Path

from core.logging.noop import NoopLogger


def test_noop_logger_incremental_ids(tmp_path: Path) -> None:
    counter_file = tmp_path / "user_counter.json"
    logger = NoopLogger(counter_path=counter_file)

    ids = [logger.allocate_user_id() for _ in range(5)]
    assert ids == [1, 2, 3, 4, 5]

    logger2 = NoopLogger(counter_path=counter_file)
    assert logger2.allocate_user_id() == 6
