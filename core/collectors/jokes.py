# coding: utf-8
"""
Коллектор анекдотов из локального json.

Цель:
    Вернуть случайную строку из data/jokes.json.

Вход:
    Путь к json-файлу (массив строк).

Выход:
    Текст анекдота.

Риски:
    Пустой или битый файл — возвращаем понятное сообщение без падения.
"""

from __future__ import annotations

import json
import random
from pathlib import Path


def get_random_joke(jokes_path: str | Path) -> str:
    """
    Читает json-массив и выбирает случайный анекдот.

    :param jokes_path: путь к jokes.json
    :return: текст анекдота
    """
    path = Path(jokes_path)

    if not path.exists():
        return "Анекдоты пока не загружены: файл jokes.json не найден."

    try:
        with path.open("r", encoding="utf-8") as f:
            jokes = json.load(f)
    except (json.JSONDecodeError, OSError):
        return "Анекдоты пока недоступны: не удалось прочитать jokes.json."

    if not isinstance(jokes, list) or len(jokes) == 0:
        return "Анекдоты пока не загружены: список пуст."

    joke = random.choice(jokes)
    if not isinstance(joke, str) or not joke.strip():
        return "Анекдоты пока недоступны: некорректная запись в jokes.json."

    return joke
