from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class Record(BaseModel):
    id: str
    fields: dict[str, Any] = {}
    createdTime: Optional[str] = None


class RecordList(BaseModel):
    records: list[Record]
    offset: Optional[str] = None
