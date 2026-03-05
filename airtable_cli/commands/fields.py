"""fields list / create / update"""

from __future__ import annotations

import json
from typing import Annotated, Optional

import typer

from ..client import BASE_URL_META, get, patch, post
from ..config import load_config
from ..interactive.prompts import is_interactive, prompt_text
from ..interactive.resolvers import resolve_base_id, resolve_field_id, resolve_table_id
from ..output.console import err_console
from ..output.formatters import output_json, output_table, output_yaml

app = typer.Typer(help="Manage fields.")


def _require_token(ctx: typer.Context):
    cfg = load_config()
    token = cfg.effective_token
    if not token:
        err_console.print("[red]No token. Run: airtable auth configure[/red]")
        raise typer.Exit(1)
    return token


def _get_base(ctx: typer.Context, base: Optional[str], token: str) -> str:
    cfg = load_config()
    base_id = base or ctx.obj.get("base") or cfg.effective_base_id
    if not base_id:
        if ctx.obj.get("no_interactive"):
            err_console.print("[red]--base is required.[/red]")
            raise typer.Exit(1)
        base_id = resolve_base_id(token)
    return base_id


def _get_table(ctx: typer.Context, table: Optional[str], token: str, base_id: str) -> str:
    if not table:
        if ctx.obj.get("no_interactive"):
            err_console.print("[red]--table is required.[/red]")
            raise typer.Exit(1)
        table = resolve_table_id(token, base_id)
    return table


@app.command("list")
def list_fields(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
) -> None:
    """List all fields in a table."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)

    data = get(f"{BASE_URL_META}/bases/{base_id}/tables", token)
    tables = data.get("tables", [])
    tbl = next((t for t in tables if t["id"] == table_id or t["name"] == table_id), None)
    if not tbl:
        err_console.print(f"[red]Table '{table_id}' not found.[/red]")
        raise typer.Exit(1)

    fields = tbl.get("fields", [])
    if fmt == "json":
        output_json(fields)
    elif fmt == "yaml":
        output_yaml(fields)
    else:
        output_table(
            ["ID", "Name", "Type"],
            [[f["id"], f["name"], f["type"]] for f in fields],
            title=f"Fields in {tbl['name']}",
        )


@app.command()
def create(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    name: Annotated[Optional[str], typer.Option("--name")] = None,
    field_type: Annotated[Optional[str], typer.Option("--type")] = None,
    options: Annotated[Optional[str], typer.Option("--options", help="Field options as JSON")] = None,
) -> None:
    """Create a new field in a table."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)

    if not name:
        if no_interactive:
            err_console.print("[red]--name is required.[/red]")
            raise typer.Exit(1)
        name = prompt_text("Field name:")

    if not field_type:
        if no_interactive:
            err_console.print("[red]--type is required.[/red]")
            raise typer.Exit(1)
        field_type = prompt_text("Field type (e.g. singleLineText):", default="singleLineText")

    body: dict = {"name": name, "type": field_type}
    if options:
        try:
            body["options"] = json.loads(options)
        except json.JSONDecodeError as e:
            err_console.print(f"[red]Invalid JSON for --options: {e}[/red]")
            raise typer.Exit(1)

    result = post(f"{BASE_URL_META}/bases/{base_id}/tables/{table_id}/fields", token, body)

    if fmt == "json":
        output_json(result)
    elif fmt == "yaml":
        output_yaml(result)
    else:
        output_table(
            ["ID", "Name", "Type"],
            [[result.get("id", ""), result.get("name", ""), result.get("type", "")]],
            title="Created Field",
        )


@app.command()
def update(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    field: Annotated[Optional[str], typer.Option("--field")] = None,
    name: Annotated[Optional[str], typer.Option("--name")] = None,
    options: Annotated[Optional[str], typer.Option("--options", help="Field options as JSON")] = None,
) -> None:
    """Update a field."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)

    field_id = field
    if not field_id:
        if no_interactive:
            err_console.print("[red]--field is required.[/red]")
            raise typer.Exit(1)
        field_id = resolve_field_id(token, base_id, table_id)

    body: dict = {}
    if name:
        body["name"] = name
    if options:
        try:
            body["options"] = json.loads(options)
        except json.JSONDecodeError as e:
            err_console.print(f"[red]Invalid JSON for --options: {e}[/red]")
            raise typer.Exit(1)

    if not body:
        err_console.print("[yellow]Nothing to update.[/yellow]")
        raise typer.Exit(0)

    result = patch(f"{BASE_URL_META}/bases/{base_id}/tables/{table_id}/fields/{field_id}", token, body)

    if fmt == "json":
        output_json(result)
    elif fmt == "yaml":
        output_yaml(result)
    else:
        output_table(
            ["ID", "Name", "Type"],
            [[result.get("id", ""), result.get("name", ""), result.get("type", "")]],
            title="Updated Field",
        )
