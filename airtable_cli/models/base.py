from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class PermissionLevel(BaseModel):
    id: str
    name: str


class Base(BaseModel):
    id: str
    name: str
    permissionLevel: Optional[str] = None


class BaseList(BaseModel):
    bases: list[Base]
    offset: Optional[str] = None


class BaseSchema(BaseModel):
    tables: list[Any] = []
