"""Tests for config load/save/mask."""

import os
from pathlib import Path

import pytest

from airtable_cli.config import Config, AuthConfig, DefaultsConfig, mask_token, load_config, save_config


def test_mask_token_short():
    assert mask_token("abc") == "***"


def test_mask_token_normal():
    result = mask_token("patXXXXXXXXXXXXXX")
    assert result.startswith("patX")
    assert result.endswith("XXXX")
    assert "***" in result


def test_config_env_var_override(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRTABLE_PAT", "env_token_value")
    monkeypatch.setenv("AIRTABLE_BASE_ID", "appENV123")
    cfg = Config()
    assert cfg.effective_token == "env_token_value"
    assert cfg.effective_base_id == "appENV123"


def test_config_save_load(tmp_path, monkeypatch):
    monkeypatch.setattr("airtable_cli.config.CONFIG_FILE", tmp_path / "config.toml")
    monkeypatch.setattr("airtable_cli.config.CONFIG_DIR", tmp_path)
    from airtable_cli import config as cfg_module
    monkeypatch.setattr(cfg_module, "CONFIG_FILE", tmp_path / "config.toml")
    monkeypatch.setattr(cfg_module, "CONFIG_DIR", tmp_path)

    cfg = Config(auth=AuthConfig(token="patABC"), defaults=DefaultsConfig(base_id="appXYZ"))
    save_config(cfg)

    loaded = load_config()
    assert loaded.auth.token == "patABC"
    assert loaded.defaults.base_id == "appXYZ"


def test_config_has_token():
    cfg = Config(auth=AuthConfig(token="patXXX"))
    assert cfg.has_token() is True

    cfg2 = Config()
    assert cfg2.has_token() is False
