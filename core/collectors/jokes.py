# coding: utf-8
"""
Коллектор анекдотов из локального json.

Цель:
    Вернуть случайную строку из data/jokes.json.

Вход:
    Путь к json-файлу.

Выход:
    Текст анекдота.

TODO:
    Реализовать чтение json в фазе 3.
"""

from __future__ import annotations

from pathlib import Path


def get_random_joke(jokes_path: str | Path) -> str:
    """
    Заглушка до реализации чтения json.

    :param jokes_path: путь к jokes.json
    :return: текст анекдота
    """
    _ = jokes_path
    return "Анекдот будет доступен после подключения jokes.json."
