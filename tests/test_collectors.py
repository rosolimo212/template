# coding: utf-8
"""Тесты коллекторов погоды и анекдотов."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.collectors.jokes import get_random_joke
from core.collectors.weather import get_current_temperature


def test_get_random_joke_from_file(tmp_path: Path) -> None:
    jokes_file = tmp_path / "jokes.json"
    jokes_file.write_text(
        json.dumps(["Первый анекдот", "Второй анекдот"], ensure_ascii=False),
        encoding="utf-8",
    )

    with patch("core.collectors.jokes.random.choice", return_value="Второй анекдот"):
        result = get_random_joke(jokes_file)

    assert result == "Второй анекдот"


def test_get_random_joke_missing_file() -> None:
    result = get_random_joke("/no/such/jokes.json")
    assert "не найден" in result.lower()


def test_get_current_temperature_success() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "location": {"name": "Moscow"},
        "current": {
            "temp_c": 12.5,
            "condition": {"text": "Partly cloudy"},
        },
    }

    with patch("core.collectors.weather.requests.get", return_value=mock_response):
        result = get_current_temperature(
            api_key="key",
            base_url="http://api.weatherapi.com/v1",
            method="/current.json",
            city="Moscow",
        )

    assert "Moscow" in result
    assert "+12.5" in result
    assert "Partly cloudy" in result


def test_get_current_temperature_api_error() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch("core.collectors.weather.requests.get", return_value=mock_response):
        result = get_current_temperature(
            api_key="bad",
            base_url="http://api.weatherapi.com/v1",
            method="/current.json",
            city="Moscow",
        )

    assert "401" in result


def test_get_current_temperature_special_chars_in_city() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "location": {"name": "O'Brien"},
        "current": {"temp_c": -3, "condition": {"text": "Clear"}},
    }

    with patch("core.collectors.weather.requests.get", return_value=mock_response):
        result = get_current_temperature(
            api_key="key",
            base_url="http://api.weatherapi.com/v1",
            method="/current.json",
            city="O'Brien",
        )

    assert "O'Brien" in result
    assert "-3" in result
