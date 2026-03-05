"""Shared types."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class Pagination(BaseModel):
    offset: Optional[str] = None


class AirtableError(BaseModel):
    type: str
    message: str
