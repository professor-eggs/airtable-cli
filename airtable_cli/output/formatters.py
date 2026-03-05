"""Rich table/JSON/YAML renderers."""

from __future__ import annotations

import json
from typing import Any

import yaml
from rich.syntax import Syntax
from rich.table import Table

from .console import console


def output_json(data: Any) -> None:
    text = json.dumps(data, indent=2, default=str)
    console.print(Syntax(text, "json", theme="monokai"))


def output_yaml(data: Any) -> None:
    text = yaml.dump(data, default_flow_style=False, allow_unicode=True)
    console.print(Syntax(text, "yaml", theme="monokai"))


def output_table(columns: list[str], rows: list[list[str]], title: str = "") -> None:
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def render(data: Any, fmt: str, *, table_columns: list[str] = (), table_rows: list[list[str]] = (), title: str = "") -> None:
    if fmt == "json":
        output_json(data)
    elif fmt == "yaml":
        output_yaml(data)
    else:
        if table_columns and table_rows is not None:
            output_table(list(table_columns), list(table_rows), title=title)
        else:
            output_json(data)
