from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class LmsMaterialCreate(SQLModel):
    title: str
    type: str
    content: str | None = None
    file_key: str | None = None
    file_name: str | None = None
    order_index: int = 0
    is_published: bool = False


class LmsMaterialRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    title: str
    type: str
    content: str | None
    file_key: str | None
    file_name: str | None
    order_index: int
    is_published: bool
    created_at: datetime
    updated_at: datetime


class LmsMaterialUpdate(SQLModel):
    title: str | None = None
    type: str | None = None
    content: str | None = None
    file_key: str | None = None
    file_name: str | None = None
    order_index: int | None = None
    is_published: bool | None = None
