# coding: utf-8
"""
Фабрика логгера по настройкам app.logging_enabled.
"""

from __future__ import annotations

from typing import Any

from iter_core.logging.base import EventLogger
from iter_core.logging.noop import NoopLogger
from iter_core.logging.postgres import PostgresLogger


def build_logger(config: dict[str, Any]) -> EventLogger:
    """
    Создаёт postgres-логгер или noop в зависимости от флага.

    :param config: полный конфиг из load_app_config
    :return: реализация EventLogger
    """
    if config["app"].get("logging_enabled"):
        return PostgresLogger(config["logging"])
    return NoopLogger()
