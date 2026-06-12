# coding: utf-8
"""
Коллектор погоды через weatherapi.com.

Цель:
    Получить текущую температуру для заданного города.

Вход:
    api_key, base_url, method, city из config.yaml.

Выход:
    Человекочитаемая строка с температурой.

TODO:
    Реализовать запрос и разбор ответа в фазе 3.
"""

from __future__ import annotations


def get_current_temperature(
    api_key: str,
    base_url: str,
    method: str,
    city: str,
) -> str:
    """
    Заглушка: вернёт фиксированный текст до реализации API.

    :param api_key: ключ weatherapi
    :param base_url: http://api.weatherapi.com/v1
    :param method: /current.json
    :param city: название города
    :return: текст для пользователя
    """
    _ = (api_key, base_url, method)
    return f"Температура в {city} будет доступна после подключения API."
