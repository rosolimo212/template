# coding: utf-8
"""Тесты загрузки конфигурации."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.config import load_app_config, read_yaml_config

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_CONFIG = ROOT / "config.example.yaml"


def test_read_yaml_config_app_section() -> None:
    app_cfg = read_yaml_config(EXAMPLE_CONFIG, "app")
    assert app_cfg["interface"] in ("streamlit", "telegram", "console")
    assert "logging_enabled" in app_cfg


def test_load_app_config_example() -> None:
    config = load_app_config(EXAMPLE_CONFIG)
    assert config["logging"]["schema"] == "template"
    assert "weatherapi" in config


def test_load_app_config_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_app_config(ROOT / "no_such_config.yaml")
