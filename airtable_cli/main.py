"""Root Typer app — wires all command groups together."""

from __future__ import annotations

import sys
from typing import Annotated, Optional

import typer

from . import __version__
from .client import AirtableAPIError
from .commands import auth, bases, comments, fields, records, tables, webhooks
from .output.console import err_console

app = typer.Typer(
    name="airtable",
    help="Airtable CLI — manage your Airtable bases, tables, records, and more.",
    no_args_is_help=True,
)

app.add_typer(auth.app, name="auth")
app.add_typer(bases.app, name="bases")
app.add_typer(tables.app, name="tables")
app.add_typer(fields.app, name="fields")
app.add_typer(records.app, name="records")
app.add_typer(comments.app, name="comments")
app.add_typer(webhooks.app, name="webhooks")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"airtable-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base", help="Default base ID for this invocation", envvar="AIRTABLE_BASE_ID")] = None,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format: table, json, yaml")] = "table",
    no_interactive: Annotated[bool, typer.Option("--no-interactive", help="Disable interactive prompts")] = False,
    version: Annotated[Optional[bool], typer.Option("--version", callback=_version_callback, is_eager=True)] = None,
) -> None:
    """Airtable CLI."""
    ctx.ensure_object(dict)
    ctx.obj["base"] = base
    ctx.obj["output"] = output
    ctx.obj["no_interactive"] = no_interactive


def run() -> None:
    """Entry point that wraps app() with top-level error handling."""
    try:
        app()
    except AirtableAPIError as exc:
        err_console.print(
            f"[bold red]Airtable API Error[/bold red] [{exc.status_code}] "
            f"[yellow]{exc.error_type}[/yellow]: {exc.message}"
        )
        sys.exit(1)
