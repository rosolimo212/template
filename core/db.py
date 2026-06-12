# coding: utf-8
"""
Подключение к postgres.

Цель:
    Единые функции для SQLAlchemy engine и psycopg2-соединения.
    Стиль как в weather/data_load.py.

Вход:
    Секция logging из config.yaml.

Выход:
    engine или connection для записи в схему template.
"""

from __future__ import annotations

from typing import Any

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_engine(logging_config: dict[str, Any]) -> Engine:
    """
    Создаёт SQLAlchemy engine для pandas.to_sql.

    :param logging_config: секция logging из config.yaml
    :return: sqlalchemy Engine
    """
    url = (
        "postgresql://"
        f"{logging_config['user']}:{logging_config['password']}"
        f"@{logging_config['host']}:{logging_config['port']}"
        f"/{logging_config['database']}"
    )
    return create_engine(url)


def get_connection(logging_config: dict[str, Any]):
    """
    Открывает psycopg2-соединение для точечных SQL-запросов.

    :param logging_config: секция logging из config.yaml
    :return: psycopg2 connection
    """
    return psycopg2.connect(
        host=logging_config["host"],
        port=logging_config["port"],
        database=logging_config["database"],
        user=logging_config["user"],
        password=logging_config["password"],
    )
