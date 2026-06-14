# coding: utf-8
"""Тесты логирования."""

from __future__ import annotations

from datetime import datetime
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from core.identity import make_user_id
from core.logging.postgres import PostgresLogger
from core.models import UserIdentity


LOGGING_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "test_db",
    "user": "test_user",
    "password": "test_pass",
    "schema": "template",
}


def test_postgres_allocate_internal_id_uses_sequence() -> None:
    logger = PostgresLogger(LOGGING_CONFIG)

    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [("template.users_internal_user_id_seq",), (42,)]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    @contextmanager
    def _fake_scope(_cfg):
        yield mock_conn

    with patch("core.logging.postgres.postgres_connection", _fake_scope):
        internal = logger._allocate_internal_user_id()

    assert internal == 42


def test_postgres_ensure_user_returns_existing() -> None:
    logger = PostgresLogger(LOGGING_CONFIG)
    user_id = make_user_id("telegram", "999")

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (user_id, 7, "999")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    @contextmanager
    def _fake_scope(_cfg):
        yield mock_conn

    with patch("core.logging.postgres.postgres_connection", _fake_scope):
        identity = logger.ensure_user("telegram", "999")

    assert identity.user_id == user_id
    assert identity.internal_user_id == 7
    assert identity.external_user_id == "999"


def test_postgres_log_event_writes_dataframe() -> None:
    logger = PostgresLogger(LOGGING_CONFIG)
    identity = UserIdentity(
        user_id=make_user_id("console", "x"),
        internal_user_id=1,
        external_user_id="x",
    )
    mock_engine = MagicMock()

    with patch("core.logging.postgres.get_engine", return_value=mock_engine):
        with patch("core.logging.postgres.pd.DataFrame.to_sql") as mock_to_sql:
            logger.log_event(
                identity=identity,
                event_name="start_screen_visit",
                channel="console",
                event_parameters={"step": 1},
            )

    mock_to_sql.assert_called_once()
    _, kwargs = mock_to_sql.call_args
    assert kwargs["schema"] == "template"
