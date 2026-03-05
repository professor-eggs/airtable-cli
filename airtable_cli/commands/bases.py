"""bases list / schema"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from ..client import BASE_URL_META, get
from ..config import load_config
from ..interactive.resolvers import resolve_base_id
from ..output.console import err_console
from ..output.formatters import output_json, output_table, output_yaml

app = typer.Typer(help="Manage Airtable bases.")


def _require_token(ctx: typer.Context):
    cfg = load_config()
    token = cfg.effective_token
    if not token:
        err_console.print("[red]No token. Run: airtable auth configure[/red]")
        raise typer.Exit(1)
    return token


@app.command("list")
def list_bases(ctx: typer.Context) -> None:
    """List all accessible bases."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")

    data = get(f"{BASE_URL_META}/bases", token)
    bases = data.get("bases", [])

    if fmt == "json":
        output_json(bases)
    elif fmt == "yaml":
        output_yaml(bases)
    else:
        output_table(
            ["ID", "Name", "Permission Level"],
            [[b["id"], b["name"], b.get("permissionLevel", "")] for b in bases],
            title="Bases",
        )


@app.command()
def schema(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base", help="Base ID")] = None,
) -> None:
    """Show schema (tables and fields) for a base."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    no_interactive: bool = ctx.obj.get("no_interactive", False)

    base_id = base or ctx.obj.get("base")
    if not base_id:
        if no_interactive:
            err_console.print("[red]--base is required.[/red]")
            raise typer.Exit(1)
        base_id = resolve_base_id(token)

    data = get(f"{BASE_URL_META}/bases/{base_id}/tables", token)
    tables = data.get("tables", [])

    if fmt == "json":
        output_json(tables)
    elif fmt == "yaml":
        output_yaml(tables)
    else:
        for table in tables:
            fields = table.get("fields", [])
            output_table(
                ["Field ID", "Name", "Type"],
                [[f["id"], f["name"], f["type"]] for f in fields],
                title=f"Table: {table['name']} ({table['id']})",
            )
