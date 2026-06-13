# coding: utf-8
"""
Коллектор погоды через weatherapi.com.

Риски:
    Основное время обычно уходит на HTTP-запрос к API, не на наш код.
"""

from __future__ import annotations

import time
from typing import Any

import requests


def get_current_temperature_with_timing(
    api_key: str,
    base_url: str,
    method: str,
    city: str,
    timeout_sec: int = 10,
) -> tuple[str, dict[str, float]]:
    """
    Запрашивает current.json и возвращает текст + разбивку времени по этапам.

    :return: (текст для пользователя, словарь секунд по этапам)
    """
    timings: dict[str, float] = {}
    total_start = time.monotonic()

    t0 = time.monotonic()
    url = base_url.rstrip("/") + method
    params = {"key": api_key, "q": city}
    timings["build_request_sec"] = time.monotonic() - t0

    t0 = time.monotonic()
    try:
        response = requests.get(url, params=params, timeout=timeout_sec)
    except requests.RequestException as err:
        timings["http_request_sec"] = time.monotonic() - t0
        timings["total_sec"] = time.monotonic() - total_start
        return f"Не удалось получить погоду: проблема с сетью ({err}).", timings
    timings["http_request_sec"] = time.monotonic() - t0

    t0 = time.monotonic()
    if response.status_code != 200:
        timings["parse_response_sec"] = time.monotonic() - t0
        timings["total_sec"] = time.monotonic() - total_start
        return (
            f"Не удалось получить погоду: сервис вернул код {response.status_code}.",
            timings,
        )

    data = response.json()
    timings["parse_response_sec"] = time.monotonic() - t0

    t0 = time.monotonic()
    try:
        place = data["location"]["name"]
        temp_c = data["current"]["temp_c"]
        condition = data["current"]["condition"]["text"]
    except (KeyError, TypeError):
        timings["format_text_sec"] = time.monotonic() - t0
        timings["total_sec"] = time.monotonic() - total_start
        return "Не удалось разобрать ответ сервиса погоды.", timings

    temp_sign = "+" if temp_c > 0 else ""
    text = (
        f"В {place} сейчас {temp_sign}{temp_c}°C. "
        f"На улице: {condition}."
    )
    timings["format_text_sec"] = time.monotonic() - t0
    timings["total_sec"] = time.monotonic() - total_start
    return text, timings


def get_current_temperature(
    api_key: str,
    base_url: str,
    method: str,
    city: str,
    timeout_sec: int = 10,
) -> str:
    """Запрашивает current.json и возвращает только текст."""
    text, _ = get_current_temperature_with_timing(
        api_key=api_key,
        base_url=base_url,
        method=method,
        city=city,
        timeout_sec=timeout_sec,
    )
    return text


def format_weather_timings(timings: dict[str, Any]) -> str:
    """Форматирует тайминги для вывода в business_checks."""
    lines = ["Тайминг запроса погоды (сек):"]
    order = [
        "build_request_sec",
        "http_request_sec",
        "parse_response_sec",
        "format_text_sec",
        "total_sec",
    ]
    for key in order:
        if key in timings:
            lines.append(f"  {key}: {float(timings[key]):.3f}")
    return "\n".join(lines)
