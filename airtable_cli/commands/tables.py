"""tables list / get / create"""

from __future__ import annotations

import json
from typing import Annotated, Optional

import typer

from ..client import BASE_URL_META, get, post
from ..config import load_config
from ..interactive.prompts import is_interactive, prompt_text
from ..interactive.resolvers import resolve_base_id, resolve_table_id
from ..output.console import err_console
from ..output.formatters import output_json, output_table, output_yaml

app = typer.Typer(help="Manage tables.")


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
    no_interactive = ctx.obj.get("no_interactive", False)
    if not base_id:
        if no_interactive:
            err_console.print("[red]--base is required.[/red]")
            raise typer.Exit(1)
        base_id = resolve_base_id(token)
    return base_id


@app.command("list")
def list_tables(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base", help="Base ID")] = None,
) -> None:
    """List all tables in a base."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    base_id = _get_base(ctx, base, token)

    data = get(f"{BASE_URL_META}/bases/{base_id}/tables", token)
    tables = data.get("tables", [])

    if fmt == "json":
        output_json(tables)
    elif fmt == "yaml":
        output_yaml(tables)
    else:
        output_table(
            ["ID", "Name", "Description", "Fields"],
            [[t["id"], t["name"], t.get("description", ""), str(len(t.get("fields", [])))] for t in tables],
            title=f"Tables in {base_id}",
        )


@app.command("get")
def get_table(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base", help="Base ID")] = None,
    table: Annotated[Optional[str], typer.Option("--table", help="Table ID")] = None,
) -> None:
    """Get details of a specific table."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)

    table_id = table
    if not table_id:
        if no_interactive:
            err_console.print("[red]--table is required.[/red]")
            raise typer.Exit(1)
        table_id = resolve_table_id(token, base_id)

    data = get(f"{BASE_URL_META}/bases/{base_id}/tables", token)
    tables = data.get("tables", [])
    tbl = next((t for t in tables if t["id"] == table_id or t["name"] == table_id), None)
    if not tbl:
        err_console.print(f"[red]Table '{table_id}' not found.[/red]")
        raise typer.Exit(1)

    if fmt == "json":
        output_json(tbl)
    elif fmt == "yaml":
        output_yaml(tbl)
    else:
        fields = tbl.get("fields", [])
        output_table(
            ["Field ID", "Name", "Type"],
            [[f["id"], f["name"], f["type"]] for f in fields],
            title=f"{tbl['name']} ({tbl['id']})",
        )


@app.command()
def create(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base", help="Base ID")] = None,
    name: Annotated[Optional[str], typer.Option("--name", help="Table name")] = None,
    description: Annotated[Optional[str], typer.Option("--description", help="Description")] = None,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Fields as JSON array")] = None,
) -> None:
    """Create a new table."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)

    if not name:
        if no_interactive:
            err_console.print("[red]--name is required.[/red]")
            raise typer.Exit(1)
        name = prompt_text("Table name:")

    body: dict = {"name": name}
    if description:
        body["description"] = description
    if fields:
        try:
            body["fields"] = json.loads(fields)
        except json.JSONDecodeError as e:
            err_console.print(f"[red]Invalid JSON for --fields: {e}[/red]")
            raise typer.Exit(1)

    result = post(f"{BASE_URL_META}/bases/{base_id}/tables", token, body)

    if fmt == "json":
        output_json(result)
    elif fmt == "yaml":
        output_yaml(result)
    else:
        output_table(
            ["ID", "Name"],
            [[result.get("id", ""), result.get("name", "")]],
            title="Created Table",
        )
