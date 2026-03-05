"""InquirerPy wrappers for interactive prompts."""

from __future__ import annotations

import sys
from typing import Optional

from InquirerPy import inquirer
from InquirerPy.base.control import Choice


def is_interactive() -> bool:
    return sys.stdin.isatty()


def prompt_text(message: str, default: str = "") -> str:
    return inquirer.text(message=message, default=default).execute()


def prompt_password(message: str) -> str:
    return inquirer.secret(message=message).execute()


def prompt_select(message: str, choices: list[Choice | str], default: Optional[str] = None) -> str:
    return inquirer.fuzzy(
        message=message,
        choices=choices,
        default=default,
        max_height="40%",
    ).execute()


def prompt_confirm(message: str, default: bool = False) -> bool:
    return inquirer.confirm(message=message, default=default).execute()
