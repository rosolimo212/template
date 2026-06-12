# coding: utf-8
"""
Слой 2 тестирования — бизнес-проверки.

Цель:
    Простые проверки, которые дополняются по словесному описанию.
    Запускаются перед коммитом вместе с pytest.

Вход:
    Импорты из iter_core / iter_ui по мере появления логики.

Выход:
    Ненулевой код выхода при первой неудачной проверке.

TODO:
    Добавить проверки из task.md по мере реализации MVP.
"""


def check_project_scaffold_exists() -> None:
    """Каркас фазы 0: ключевые модули на месте."""
    from pathlib import Path

    root = Path(__file__).resolve().parent
    required = [
        "iter_core/app.py",
        "iter_core/brain.py",
        "iter_core/config.py",
        "iter_ui/streamlit_app.py",
        "sql/001_init.sql",
        "data/jokes.json",
    ]
    missing = [p for p in required if not (root / p).exists()]
    if missing:
        raise AssertionError("Не найдены файлы каркаса: " + ", ".join(missing))


def run_all_checks() -> None:
    check_project_scaffold_exists()
    print("business_checks: OK")


if __name__ == "__main__":
    run_all_checks()
