"""webhooks list / create / update / delete / payloads"""

from __future__ import annotations

import json
from typing import Annotated, Optional

import typer

from ..client import BASE_URL_BASES, delete as http_delete, get, patch, post
from ..config import load_config
from ..interactive.prompts import is_interactive, prompt_confirm, prompt_text
from ..interactive.resolvers import resolve_base_id
from ..output.console import console, err_console
from ..output.formatters import output_json, output_table, output_yaml

app = typer.Typer(help="Manage webhooks.")


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


def _get_webhook(ctx, webhook, token, base_id):
    webhook_id = webhook
    if not webhook_id:
        if ctx.obj.get("no_interactive"):
            err_console.print("[red]--webhook is required.[/red]")
            raise typer.Exit(1)
        data = get(f"{BASE_URL_BASES}/{base_id}/webhooks", token)
        webhooks = data.get("webhooks", [])
        from InquirerPy.base.control import Choice
        from ..interactive.prompts import prompt_select
        choices = [
            Choice(value=w["id"], name=f"{w['id']} {w.get('notificationUrl','')}")
            for w in webhooks
        ]
        webhook_id = prompt_select("Select webhook:", choices)
    return webhook_id


@app.command("list")
def list_webhooks(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
) -> None:
    """List all webhooks for a base."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    base_id = _get_base(ctx, base, token)

    data = get(f"{BASE_URL_BASES}/{base_id}/webhooks", token)
    webhooks = data.get("webhooks", [])

    if fmt == "json":
        output_json(webhooks)
    elif fmt == "yaml":
        output_yaml(webhooks)
    else:
        output_table(
            ["ID", "URL", "Enabled", "Expiration"],
            [
                [
                    w["id"],
                    w.get("notificationUrl", ""),
                    str(w.get("isHookEnabled", "")),
                    w.get("expirationTime", ""),
                ]
                for w in webhooks
            ],
            title=f"Webhooks for {base_id}",
        )


@app.command()
def create(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    url: Annotated[Optional[str], typer.Option("--url", help="Notification URL")] = None,
    filters: Annotated[Optional[str], typer.Option("--filters", help="Filters as JSON")] = None,
    specification: Annotated[Optional[str], typer.Option("--specification", help="Spec as JSON")] = None,
) -> None:
    """Create a webhook."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)

    if not url:
        if no_interactive:
            err_console.print("[red]--url is required.[/red]")
            raise typer.Exit(1)
        url = prompt_text("Notification URL:")

    body: dict = {"notificationUrl": url}
    if specification:
        try:
            body["specification"] = json.loads(specification)
        except json.JSONDecodeError as e:
            err_console.print(f"[red]Invalid JSON for --specification: {e}[/red]")
            raise typer.Exit(1)
    if filters:
        try:
            # filters goes inside specification.filters
            body.setdefault("specification", {})["filters"] = json.loads(filters)
        except json.JSONDecodeError as e:
            err_console.print(f"[red]Invalid JSON for --filters: {e}[/red]")
            raise typer.Exit(1)

    result = post(f"{BASE_URL_BASES}/{base_id}/webhooks", token, body)

    console.print("[green]Webhook created.[/green]")
    if fmt == "json":
        output_json(result)
    elif fmt == "yaml":
        output_yaml(result)
    else:
        output_table(
            ["ID", "Expiration"],
            [[result.get("id", ""), result.get("expirationTime", "")]],
            title="Created Webhook",
        )


@app.command()
def update(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    webhook: Annotated[Optional[str], typer.Option("--webhook")] = None,
    enable: Annotated[Optional[bool], typer.Option("--enable/--disable")] = None,
    refresh_expiry: Annotated[bool, typer.Option("--refresh-expiry/--no-refresh-expiry")] = False,
) -> None:
    """Enable/disable a webhook or refresh its expiry."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    base_id = _get_base(ctx, base, token)
    webhook_id = _get_webhook(ctx, webhook, token, base_id)

    body: dict = {}
    if enable is not None:
        body["isHookEnabled"] = enable
    if refresh_expiry:
        body["refreshExpiry"] = True

    if not body:
        err_console.print("[yellow]Nothing to update.[/yellow]")
        raise typer.Exit(0)

    result = patch(f"{BASE_URL_BASES}/{base_id}/webhooks/{webhook_id}", token, body)

    console.print("[green]Webhook updated.[/green]")
    if fmt == "json":
        output_json(result)
    elif fmt == "yaml":
        output_yaml(result)


@app.command("delete")
def delete_webhook(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    webhook: Annotated[Optional[str], typer.Option("--webhook")] = None,
    confirm: Annotated[bool, typer.Option("--confirm/--no-confirm")] = True,
) -> None:
    """Delete a webhook."""
    token = _require_token(ctx)
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)
    webhook_id = _get_webhook(ctx, webhook, token, base_id)

    if confirm and not no_interactive and is_interactive():
        ok = prompt_confirm(f"Delete webhook {webhook_id}?")
        if not ok:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    http_delete(f"{BASE_URL_BASES}/{base_id}/webhooks/{webhook_id}", token)
    console.print(f"[green]Deleted webhook {webhook_id}.[/green]")


@app.command()
def payloads(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    webhook: Annotated[Optional[str], typer.Option("--webhook")] = None,
    cursor: Annotated[Optional[int], typer.Option("--cursor")] = None,
) -> None:
    """Fetch payloads for a webhook."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    base_id = _get_base(ctx, base, token)
    webhook_id = _get_webhook(ctx, webhook, token, base_id)

    params: dict = {}
    if cursor is not None:
        params["cursor"] = cursor

    data = get(f"{BASE_URL_BASES}/{base_id}/webhooks/{webhook_id}/payloads", token, params=params)
    payload_list = data.get("payloads", [])

    if fmt == "json":
        output_json(data)
    elif fmt == "yaml":
        output_yaml(data)
    else:
        output_table(
            ["Timestamp", "Transaction #", "Summary"],
            [
                [
                    p.get("timestamp", ""),
                    str(p.get("baseTransactionNumber", "")),
                    str(list(p.keys())[:4]),
                ]
                for p in payload_list
            ],
            title=f"Payloads for {webhook_id}",
        )
        if data.get("mightHaveMore"):
            console.print(f"[yellow]More payloads available. Next cursor: {data.get('cursor')}[/yellow]")
