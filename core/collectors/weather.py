# coding: utf-8
"""
Коллектор погоды через weatherapi.com.

Цель:
    Получить текущую температуру для заданного города.

Вход:
    api_key, base_url, method, city из config.yaml.

Выход:
    Человекочитаемая строка с температурой.

Риски:
    При ошибке API возвращаем текст ошибки, не бросаем исключение наружу.
"""

from __future__ import annotations

import requests


def get_current_temperature(
    api_key: str,
    base_url: str,
    method: str,
    city: str,
    timeout_sec: int = 10,
) -> str:
    """
    Запрашивает current.json и возвращает температуру.

    :param api_key: ключ weatherapi
    :param base_url: http://api.weatherapi.com/v1
    :param method: /current.json
    :param city: название города
    :param timeout_sec: таймаут HTTP-запроса
    :return: текст для пользователя
    """
    url = base_url.rstrip("/") + method
    params = {
        "key": api_key,
        "q": city,
    }

    try:
        response = requests.get(url, params=params, timeout=timeout_sec)
    except requests.RequestException as err:
        return f"Не удалось получить погоду: проблема с сетью ({err})."

    if response.status_code != 200:
        return (
            f"Не удалось получить погоду: сервис вернул код {response.status_code}."
        )

    data = response.json()
    try:
        place = data["location"]["name"]
        temp_c = data["current"]["temp_c"]
        condition = data["current"]["condition"]["text"]
    except (KeyError, TypeError):
        return "Не удалось разобрать ответ сервиса погоды."

    temp_sign = "+" if temp_c > 0 else ""
    return (
        f"В {place} сейчас {temp_sign}{temp_c}°C. "
        f"На улице: {condition}."
    )
