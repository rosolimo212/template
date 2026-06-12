# coding: utf-8
"""
Слой 2 тестирования — бизнес-проверки.

Цель:
    Простые проверки, которые дополняются по словесному описанию.
    Запускаются перед коммитом вместе с pytest.

Вход:
    Импорты из core / ui по мере появления логики.

Выход:
    Ненулевой код выхода при первой неудачной проверке.

TODO:
    Добавить проверки из task.md по мере реализации MVP.
"""


def check_project_scaffold_exists() -> None:
    """Каркас проекта: ключевые модули на месте."""
    from pathlib import Path

    root = Path(__file__).resolve().parent
    required = [
        "core/app.py",
        "core/brain.py",
        "core/config.py",
        "core/db.py",
        "core/logging/postgres.py",
        "ui/streamlit_app.py",
        "sql/001_init.sql",
        "data/jokes.json",
    ]
    missing = [p for p in required if not (root / p).exists()]
    if missing:
        raise AssertionError("Не найдены файлы каркаса: " + ", ".join(missing))


def check_logger_factory_builds() -> None:
    """Фабрика логгера создаёт postgres или noop без ошибок."""
    from core.logging.factory import build_logger

    noop_cfg = {
        "app": {"logging_enabled": False},
        "logging": {"schema": "template"},
    }
    pg_cfg = {
        "app": {"logging_enabled": True},
        "logging": {
            "host": "localhost",
            "port": 5432,
            "database": "db",
            "user": "u",
            "password": "p",
            "schema": "template",
        },
    }

    build_logger(noop_cfg)
    build_logger(pg_cfg)


def run_all_checks() -> None:
    check_project_scaffold_exists()
    check_logger_factory_builds()
    print("business_checks: OK")


if __name__ == "__main__":
    run_all_checks()
