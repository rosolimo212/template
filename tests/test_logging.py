# coding: utf-8
"""Тесты логирования (noop и postgres с mock)."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

from core.logging.postgres import PostgresLogger


LOGGING_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "test_db",
    "user": "test_user",
    "password": "test_pass",
    "schema": "template",
}


def test_postgres_allocate_user_id_uses_sequence() -> None:
    logger = PostgresLogger(LOGGING_CONFIG)

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (42,)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("core.logging.postgres.get_connection", return_value=mock_conn):
        user_id = logger.allocate_user_id()

    assert user_id == 42
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_postgres_upsert_user_executes_sql() -> None:
    logger = PostgresLogger(LOGGING_CONFIG)

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    now = datetime(2026, 6, 12, 12, 0, 0)

    with patch("core.logging.postgres.get_connection", return_value=mock_conn):
        logger.upsert_user(
            user_id=1,
            user_name="Роман",
            registration_date=now,
            registration_channel="console",
            last_active_at=now,
        )

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_postgres_log_event_writes_dataframe() -> None:
    logger = PostgresLogger(LOGGING_CONFIG)
    mock_engine = MagicMock()

    with patch("core.logging.postgres.get_engine", return_value=mock_engine):
        with patch("core.logging.postgres.pd.DataFrame.to_sql") as mock_to_sql:
            logger.log_event(
                user_id=1,
                event_name="start_screen_visit",
                channel="console",
                event_parameters={"step": 1},
            )

    mock_to_sql.assert_called_once()
    _, kwargs = mock_to_sql.call_args
    assert kwargs["schema"] == "template"
    assert kwargs["if_exists"] == "append"
