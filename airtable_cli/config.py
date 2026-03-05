"""Config management: read/write ~/.config/airtable-cli/config.toml with env var override."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]
from typing import Optional

import tomli_w  # type: ignore
from pydantic import BaseModel, field_validator


CONFIG_DIR = Path.home() / ".config" / "airtable-cli"
CONFIG_FILE = CONFIG_DIR / "config.toml"
ENV_TOKEN = "AIRTABLE_PAT"
ENV_BASE = "AIRTABLE_BASE_ID"


class AuthConfig(BaseModel):
    token: str = ""


class DefaultsConfig(BaseModel):
    base_id: str = ""


class OutputConfig(BaseModel):
    format: str = "table"
    color: bool = True


class Config(BaseModel):
    auth: AuthConfig = AuthConfig()
    defaults: DefaultsConfig = DefaultsConfig()
    output: OutputConfig = OutputConfig()

    @field_validator("auth", mode="before")
    @classmethod
    def _default_auth(cls, v):
        return v or {}

    @field_validator("defaults", mode="before")
    @classmethod
    def _default_defaults(cls, v):
        return v or {}

    @field_validator("output", mode="before")
    @classmethod
    def _default_output(cls, v):
        return v or {}

    @property
    def effective_token(self) -> str:
        return os.environ.get(ENV_TOKEN, self.auth.token)

    @property
    def effective_base_id(self) -> str:
        return os.environ.get(ENV_BASE, self.defaults.base_id)

    def has_token(self) -> bool:
        return bool(self.effective_token)


def load_config() -> Config:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        return Config.model_validate(data)
    return Config()


def save_config(config: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if config.auth.token:
        data["auth"] = {"token": config.auth.token}
    if config.defaults.base_id:
        data["defaults"] = {"base_id": config.defaults.base_id}
    if config.output.format != "table" or not config.output.color:
        data["output"] = {
            "format": config.output.format,
            "color": config.output.color,
        }
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(data, f)


def mask_token(token: str) -> str:
    if len(token) <= 8:
        return "***"
    return token[:4] + "***" + token[-4:]
