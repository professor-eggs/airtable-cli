from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel
from .field import Field


class View(BaseModel):
    id: str
    name: str
    type: str


class Table(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    primaryFieldId: Optional[str] = None
    fields: list[Field] = []
    views: list[View] = []


class TableList(BaseModel):
    tables: list[Table]
