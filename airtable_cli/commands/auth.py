"""auth configure / show / revoke"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from ..config import load_config, mask_token, save_config
from ..interactive.prompts import is_interactive, prompt_password, prompt_text
from ..output.console import console, err_console

app = typer.Typer(help="Manage Airtable authentication.")


@app.command()
def configure(
    ctx: typer.Context,
    token: Annotated[Optional[str], typer.Option("--token", help="Personal Access Token")] = None,
    default_base: Annotated[Optional[str], typer.Option("--default-base", help="Default base ID")] = None,
) -> None:
    """Set up authentication and defaults."""
    no_interactive: bool = ctx.obj.get("no_interactive", False)
    cfg = load_config()

    if not token:
        if no_interactive:
            err_console.print("[red]--token is required in non-interactive mode.[/red]")
            raise typer.Exit(1)
        token = prompt_password("Enter your Airtable Personal Access Token:")

    if not default_base and not no_interactive and is_interactive():
        default_base = prompt_text("Default base ID (leave blank to skip):", default="")

    cfg.auth.token = token
    if default_base:
        cfg.defaults.base_id = default_base

    save_config(cfg)
    console.print(f"[green]Token saved:[/green] {mask_token(token)}")
    if default_base:
        console.print(f"[green]Default base:[/green] {default_base}")


@app.command()
def show(ctx: typer.Context) -> None:
    """Show current auth config."""
    cfg = load_config()
    token = cfg.effective_token
    if token:
        console.print(f"Token: {mask_token(token)}")
        console.print(f"Default base: {cfg.effective_base_id or '(none)'}")
        console.print(f"Output format: {cfg.output.format}")
    else:
        console.print("[yellow]No token configured. Run: airtable auth configure[/yellow]")


@app.command()
def revoke(ctx: typer.Context) -> None:
    """Remove saved token from config."""
    cfg = load_config()
    cfg.auth.token = ""
    save_config(cfg)
    console.print("[green]Token removed from config.[/green]")
