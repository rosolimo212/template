# coding: utf-8
"""
Загрузка и проверка config.yaml.

Цель:
    Прочитать yaml-секции и вернуть единый dict для всего приложения.

Вход:
    Путь к yaml-файлу (обычно config.yaml в корне проекта).

Выход:
    dict с ключами app, weatherapi, telegram, logging.

Риски:
    При отсутствии обязательных ключей выбрасывается ValueError с текстом на русском.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ALLOWED_INTERFACES = ("streamlit", "telegram", "console")


def read_yaml_config(yaml_file: str | Path, section: str) -> dict[str, Any]:
    """
    Читает одну секцию из yaml-файла.

    :param yaml_file: путь к yaml
    :param section: имя секции верхнего уровня
    :return: содержимое секции как dict
    """
    path = Path(yaml_file)
    with path.open("r", encoding="utf-8") as yaml_stream:
        descriptor = yaml.full_load(yaml_stream)

    if section not in descriptor:
        raise ValueError(f"Секция {section!r} не найдена в файле {path!r}")

    section_data = descriptor[section]
    if not isinstance(section_data, dict):
        raise ValueError(f"Секция {section!r} должна быть словарём")

    return section_data


def load_app_config(yaml_file: str | Path = "config.yaml") -> dict[str, Any]:
    """
    Собирает и проверяет конфигурацию приложения.

    :param yaml_file: путь к config.yaml
    :return: проверенный конфиг
    """
    path = Path(yaml_file)
    if not path.exists():
        raise FileNotFoundError(
            f"Файл {path!r} не найден. Скопируйте config.example.yaml в config.yaml."
        )

    app_cfg = read_yaml_config(path, "app")
    weather_cfg = read_yaml_config(path, "weatherapi")
    telegram_cfg = read_yaml_config(path, "telegram")
    logging_cfg = read_yaml_config(path, "logging")

    interface = app_cfg.get("interface")
    if interface not in ALLOWED_INTERFACES:
        raise ValueError(
            f"app.interface должен быть одним из {ALLOWED_INTERFACES}, получено {interface!r}"
        )

    if "logging_enabled" not in app_cfg:
        raise ValueError("В секции app обязателен ключ logging_enabled")

    for key in ("url", "method", "api_key", "city"):
        if key not in weather_cfg:
            raise ValueError(f"В секции weatherapi обязателен ключ {key!r}")

    if interface == "telegram" and not telegram_cfg.get("token"):
        raise ValueError("Для interface=telegram нужен telegram.token в config.yaml")

    for key in ("host", "port", "database", "user", "password", "schema"):
        if key not in logging_cfg:
            raise ValueError(f"В секции logging обязателен ключ {key!r}")

    if logging_cfg.get("schema") != "template":
        raise ValueError("Схема логирования должна называться template")

    return {
        "app": app_cfg,
        "weatherapi": weather_cfg,
        "telegram": telegram_cfg,
        "logging": logging_cfg,
    }
