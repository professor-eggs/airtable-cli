"""comments list / create / delete"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from ..client import BASE_URL_V0, delete as http_delete, get, post
from ..config import load_config
from ..interactive.prompts import is_interactive, prompt_confirm, prompt_text
from ..interactive.resolvers import resolve_base_id, resolve_record_id, resolve_table_id
from ..output.console import console, err_console
from ..output.formatters import output_json, output_table, output_yaml

app = typer.Typer(help="Manage comments on records.")


def _require_token(ctx: typer.Context):
    cfg = load_config()
    token = cfg.effective_token
    if not token:
        err_console.print("[red]No token. Run: airtable auth configure[/red]")
        raise typer.Exit(1)
    return token


def _get_base(ctx, base, token):
    cfg = load_config()
    base_id = base or ctx.obj.get("base") or cfg.effective_base_id
    if not base_id:
        if ctx.obj.get("no_interactive"):
            err_console.print("[red]--base is required.[/red]")
            raise typer.Exit(1)
        base_id = resolve_base_id(token)
    return base_id


def _get_table(ctx, table, token, base_id):
    if not table:
        if ctx.obj.get("no_interactive"):
            err_console.print("[red]--table is required.[/red]")
            raise typer.Exit(1)
        table = resolve_table_id(token, base_id)
    return table


def _get_record(ctx, record, token, base_id, table_id):
    if not record:
        if ctx.obj.get("no_interactive"):
            err_console.print("[red]--record is required.[/red]")
            raise typer.Exit(1)
        record = resolve_record_id(token, base_id, table_id)
    return record


@app.command("list")
def list_comments(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    record: Annotated[Optional[str], typer.Option("--record")] = None,
) -> None:
    """List all comments on a record."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)
    record_id = _get_record(ctx, record, token, base_id, table_id)

    data = get(f"{BASE_URL_V0}/{base_id}/{table_id}/{record_id}/comments", token)
    comments = data.get("comments", [])

    if fmt == "json":
        output_json(comments)
    elif fmt == "yaml":
        output_yaml(comments)
    else:
        output_table(
            ["ID", "Author", "Text", "Created"],
            [
                [
                    c["id"],
                    c.get("author", {}).get("name", "") if c.get("author") else "",
                    c.get("text", "")[:80],
                    c.get("createdTime", ""),
                ]
                for c in comments
            ],
            title=f"Comments on {record_id}",
        )


@app.command()
def create(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    record: Annotated[Optional[str], typer.Option("--record")] = None,
    text: Annotated[Optional[str], typer.Option("--text")] = None,
) -> None:
    """Add a comment to a record."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)
    record_id = _get_record(ctx, record, token, base_id, table_id)

    if not text:
        if no_interactive:
            err_console.print("[red]--text is required.[/red]")
            raise typer.Exit(1)
        text = prompt_text("Comment text:")

    result = post(
        f"{BASE_URL_V0}/{base_id}/{table_id}/{record_id}/comments",
        token,
        {"text": text},
    )

    console.print("[green]Comment created.[/green]")
    if fmt == "json":
        output_json(result)
    elif fmt == "yaml":
        output_yaml(result)
    else:
        output_table(
            ["ID", "Text"],
            [[result.get("id", ""), result.get("text", "")]],
            title="Created Comment",
        )


@app.command("delete")
def delete_comment(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    record: Annotated[Optional[str], typer.Option("--record")] = None,
    comment: Annotated[Optional[str], typer.Option("--comment")] = None,
    confirm: Annotated[bool, typer.Option("--confirm/--no-confirm")] = True,
) -> None:
    """Delete a comment."""
    token = _require_token(ctx)
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)
    record_id = _get_record(ctx, record, token, base_id, table_id)

    comment_id = comment
    if not comment_id:
        if no_interactive:
            err_console.print("[red]--comment is required.[/red]")
            raise typer.Exit(1)
        # List comments for selection
        data = get(f"{BASE_URL_V0}/{base_id}/{table_id}/{record_id}/comments", token)
        comments = data.get("comments", [])
        from ..interactive.prompts import prompt_select
        from InquirerPy.base.control import Choice
        choices = [Choice(value=c["id"], name=f"{c['id']}: {c.get('text','')[:60]}") for c in comments]
        comment_id = prompt_select("Select comment to delete:", choices)

    if confirm and not no_interactive and is_interactive():
        ok = prompt_confirm(f"Delete comment {comment_id}?")
        if not ok:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    http_delete(
        f"{BASE_URL_V0}/{base_id}/{table_id}/{record_id}/comments/{comment_id}",
        token,
    )
    console.print(f"[green]Deleted comment {comment_id}.[/green]")
