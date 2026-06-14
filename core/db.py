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

Риски:
    get_connection() возвращает «сырое» соединение — вызывающий обязан conn.close().
    Предпочтительно: with postgres_connection(...) as conn — закрытие и commit/rollback автоматически.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

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

    Вызывающий код обязан закрыть соединение (conn.close()) или использовать
    postgres_connection() как context manager.

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


@contextmanager
def postgres_connection(
    logging_config: dict[str, Any],
) -> Generator[Any, None, None]:
    """
    Context manager: commit при успехе, rollback при ошибке, close в finally.

    Пример:
        with postgres_connection(cfg) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

    :param logging_config: секция logging из config.yaml
    :yield: psycopg2 connection
    """
    conn = get_connection(logging_config)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
