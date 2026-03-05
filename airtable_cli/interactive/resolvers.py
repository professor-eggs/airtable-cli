"""Resolve IDs interactively by fetching real API data."""

from __future__ import annotations

from typing import Optional

from InquirerPy.base.control import Choice

from ..client import BASE_URL_META, BASE_URL_V0, get
from .prompts import prompt_select


def resolve_base_id(token: str, current: Optional[str] = None) -> str:
    """Fuzzy-pick a base by name; return base ID."""
    if current:
        return current
    data = get(f"{BASE_URL_META}/bases", token)
    bases = data.get("bases", [])
    choices = [Choice(value=b["id"], name=f"{b['name']} ({b['id']})") for b in bases]
    return prompt_select("Select a base:", choices)


def resolve_table_id(token: str, base_id: str, current: Optional[str] = None) -> str:
    """Fuzzy-pick a table by name; return table ID."""
    if current:
        return current
    data = get(f"{BASE_URL_META}/bases/{base_id}/tables", token)
    tables = data.get("tables", [])
    choices = [Choice(value=t["id"], name=f"{t['name']} ({t['id']})") for t in tables]
    return prompt_select("Select a table:", choices)


def resolve_record_id(token: str, base_id: str, table_id: str, current: Optional[str] = None) -> str:
    """Fuzzy-pick a record; return record ID."""
    if current:
        return current
    data = get(f"{BASE_URL_V0}/{base_id}/{table_id}", token, params={"maxRecords": 100})
    records = data.get("records", [])
    choices = [
        Choice(value=r["id"], name=f"{r['id']} — {list(r.get('fields', {}).values())[:2]}")
        for r in records
    ]
    return prompt_select("Select a record:", choices)


def resolve_field_id(token: str, base_id: str, table_id: str, current: Optional[str] = None) -> str:
    """Fuzzy-pick a field; return field ID."""
    if current:
        return current
    data = get(f"{BASE_URL_META}/bases/{base_id}/tables", token)
    tables = data.get("tables", [])
    fields = []
    for t in tables:
        if t["id"] == table_id:
            fields = t.get("fields", [])
            break
    choices = [Choice(value=f["id"], name=f"{f['name']} ({f['id']})") for f in fields]
    return prompt_select("Select a field:", choices)
