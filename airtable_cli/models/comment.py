from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class Author(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None


class Comment(BaseModel):
    id: str
    text: str
    author: Optional[Author] = None
    createdTime: Optional[str] = None
    lastUpdatedTime: Optional[str] = None


class CommentList(BaseModel):
    comments: list[Comment]
    offset: Optional[str] = None
