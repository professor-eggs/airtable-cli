"""records list / get / create / update / delete"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, List, Optional

import typer

from ..client import BASE_URL_V0, delete as http_delete, get, paginate, patch, post, put
from ..config import load_config
from ..interactive.prompts import is_interactive, prompt_confirm, prompt_text
from ..interactive.resolvers import resolve_base_id, resolve_record_id, resolve_table_id
from ..output.console import console, err_console
from ..output.formatters import output_json, output_table, output_yaml

app = typer.Typer(help="Manage records.")

BATCH_SIZE = 10


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


def _load_fields_data(fields_json: Optional[str], fields_file: Optional[Path]) -> Optional[dict | list]:
    if fields_file:
        try:
            return json.loads(fields_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            err_console.print(f"[red]Error reading --fields-file: {e}[/red]")
            raise typer.Exit(1)
    if fields_json:
        try:
            return json.loads(fields_json)
        except json.JSONDecodeError as e:
            err_console.print(f"[red]Invalid JSON for --fields: {e}[/red]")
            raise typer.Exit(1)
    return None


@app.command("list")
def list_records(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    view: Annotated[Optional[str], typer.Option("--view")] = None,
    filter_formula: Annotated[Optional[str], typer.Option("--filter")] = None,
    sort: Annotated[Optional[List[str]], typer.Option("--sort")] = None,
    max_records: Annotated[Optional[int], typer.Option("--max-records")] = None,
    fields: Annotated[Optional[List[str]], typer.Option("--fields")] = None,
    all_pages: Annotated[bool, typer.Option("--all-pages/--no-all-pages")] = False,
    cell_format: Annotated[str, typer.Option("--cell-format")] = "json",
) -> None:
    """List records in a table."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)

    params: dict = {}
    if view:
        params["view"] = view
    if filter_formula:
        params["filterByFormula"] = filter_formula
    if max_records:
        params["maxRecords"] = max_records
    if fields:
        for i, f in enumerate(fields):
            params[f"fields[{i}]"] = f
    if sort:
        for i, s in enumerate(sort):
            parts = s.split(":", 1)
            params[f"sort[{i}][field]"] = parts[0]
            if len(parts) > 1:
                params[f"sort[{i}][direction]"] = parts[1]
    if cell_format != "json":
        params["cellFormat"] = cell_format

    url = f"{BASE_URL_V0}/{base_id}/{table_id}"
    all_records = []

    if all_pages:
        for page in paginate(url, token, params=params):
            all_records.extend(page.get("records", []))
    else:
        data = get(url, token, params=params)
        all_records = data.get("records", [])

    if fmt == "json":
        output_json(all_records)
    elif fmt == "yaml":
        output_yaml(all_records)
    else:
        # Collect all field names for columns
        all_field_names: list[str] = []
        for r in all_records:
            for k in r.get("fields", {}):
                if k not in all_field_names:
                    all_field_names.append(k)
        columns = ["ID", "Created"] + all_field_names
        rows = [
            [r["id"], r.get("createdTime", "")] + [str(r.get("fields", {}).get(k, "")) for k in all_field_names]
            for r in all_records
        ]
        output_table(columns, rows, title=f"Records ({len(all_records)})")


@app.command("get")
def get_record(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    record: Annotated[Optional[str], typer.Option("--record")] = None,
) -> None:
    """Get a single record."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)

    record_id = record
    if not record_id:
        if no_interactive:
            err_console.print("[red]--record is required.[/red]")
            raise typer.Exit(1)
        record_id = resolve_record_id(token, base_id, table_id)

    data = get(f"{BASE_URL_V0}/{base_id}/{table_id}/{record_id}", token)

    if fmt == "json":
        output_json(data)
    elif fmt == "yaml":
        output_yaml(data)
    else:
        f = data.get("fields", {})
        output_table(
            ["Field", "Value"],
            [[k, str(v)] for k, v in f.items()],
            title=f"Record {data.get('id', '')}",
        )


@app.command()
def create(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    fields: Annotated[Optional[str], typer.Option("--fields", help="Fields as JSON object or array")] = None,
    fields_file: Annotated[Optional[Path], typer.Option("--fields-file")] = None,
    typecast: Annotated[bool, typer.Option("--typecast/--no-typecast")] = False,
) -> None:
    """Create one or more records."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)

    data = _load_fields_data(fields, fields_file)
    if data is None:
        err_console.print("[red]--fields or --fields-file is required.[/red]")
        raise typer.Exit(1)

    # Normalize to list of field objects
    if isinstance(data, dict):
        records_data = [{"fields": data}]
    elif isinstance(data, list):
        # Accept either list of field dicts or list of record objects
        if data and isinstance(data[0], dict) and "fields" not in data[0]:
            records_data = [{"fields": item} for item in data]
        else:
            records_data = data
    else:
        err_console.print("[red]--fields must be a JSON object or array.[/red]")
        raise typer.Exit(1)

    url = f"{BASE_URL_V0}/{base_id}/{table_id}"
    created = []

    # Batch in groups of BATCH_SIZE
    for i in range(0, len(records_data), BATCH_SIZE):
        batch = records_data[i : i + BATCH_SIZE]
        body: dict = {"records": batch}
        if typecast:
            body["typecast"] = True
        result = post(url, token, body)
        created.extend(result.get("records", []))

    console.print(f"[green]Created {len(created)} record(s).[/green]")
    if fmt == "json":
        output_json(created)
    elif fmt == "yaml":
        output_yaml(created)
    else:
        output_table(
            ["ID", "Created Time"],
            [[r["id"], r.get("createdTime", "")] for r in created],
            title="Created Records",
        )


@app.command()
def update(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    record: Annotated[Optional[List[str]], typer.Option("--record")] = None,
    fields: Annotated[Optional[str], typer.Option("--fields")] = None,
    fields_file: Annotated[Optional[Path], typer.Option("--fields-file")] = None,
    mode: Annotated[str, typer.Option("--mode", help="patch or put")] = "patch",
    typecast: Annotated[bool, typer.Option("--typecast/--no-typecast")] = False,
) -> None:
    """Update one or more records."""
    token = _require_token(ctx)
    fmt: str = ctx.obj.get("output", "table")
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)

    record_ids = list(record or [])
    if not record_ids:
        if no_interactive:
            err_console.print("[red]--record is required.[/red]")
            raise typer.Exit(1)
        rid = resolve_record_id(token, base_id, table_id)
        record_ids = [rid]

    data = _load_fields_data(fields, fields_file)
    if data is None:
        err_console.print("[red]--fields or --fields-file is required.[/red]")
        raise typer.Exit(1)

    field_data = data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}

    url = f"{BASE_URL_V0}/{base_id}/{table_id}"
    http_fn = patch if mode == "patch" else put
    updated = []

    for i in range(0, len(record_ids), BATCH_SIZE):
        batch_ids = record_ids[i : i + BATCH_SIZE]
        records_batch = [{"id": rid, "fields": field_data} for rid in batch_ids]
        body: dict = {"records": records_batch}
        if typecast:
            body["typecast"] = True
        result = http_fn(url, token, body)
        updated.extend(result.get("records", []))

    console.print(f"[green]Updated {len(updated)} record(s).[/green]")
    if fmt == "json":
        output_json(updated)
    elif fmt == "yaml":
        output_yaml(updated)


@app.command()
def delete(
    ctx: typer.Context,
    base: Annotated[Optional[str], typer.Option("--base")] = None,
    table: Annotated[Optional[str], typer.Option("--table")] = None,
    record: Annotated[Optional[List[str]], typer.Option("--record")] = None,
    confirm: Annotated[bool, typer.Option("--confirm/--no-confirm")] = True,
) -> None:
    """Delete one or more records."""
    token = _require_token(ctx)
    no_interactive = ctx.obj.get("no_interactive", False)
    base_id = _get_base(ctx, base, token)
    table_id = _get_table(ctx, table, token, base_id)

    record_ids = list(record or [])
    if not record_ids:
        if no_interactive:
            err_console.print("[red]--record is required.[/red]")
            raise typer.Exit(1)
        rid = resolve_record_id(token, base_id, table_id)
        record_ids = [rid]

    if confirm and not no_interactive and is_interactive():
        ok = prompt_confirm(f"Delete {len(record_ids)} record(s)?")
        if not ok:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    url = f"{BASE_URL_V0}/{base_id}/{table_id}"
    deleted = []

    for i in range(0, len(record_ids), BATCH_SIZE):
        batch_ids = record_ids[i : i + BATCH_SIZE]
        params = {f"records[{j}]": rid for j, rid in enumerate(batch_ids)}
        result = http_delete(url, token, params=params)
        deleted.extend(result.get("records", []))

    console.print(f"[green]Deleted {len(deleted)} record(s).[/green]")
