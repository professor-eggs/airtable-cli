from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel


class FieldType(str, Enum):
    single_line_text = "singleLineText"
    email = "email"
    url = "url"
    multiline_text = "multilineText"
    number = "number"
    percent = "percent"
    currency = "currency"
    single_select = "singleSelect"
    multi_select = "multipleSelects"
    date = "date"
    phone = "phoneNumber"
    checkbox = "checkbox"
    formula = "formula"
    created_time = "createdTime"
    rollup = "rollup"
    count = "count"
    lookup = "lookup"
    linked_record = "multipleRecordLinks"
    auto_number = "autoNumber"
    barcode = "barcode"
    rating = "rating"
    rich_text = "richText"
    duration = "duration"
    last_modified_time = "lastModifiedTime"
    created_by = "createdBy"
    last_modified_by = "lastModifiedBy"
    attachment = "multipleAttachments"
    button = "button"


class Field(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    options: Optional[dict[str, Any]] = None
