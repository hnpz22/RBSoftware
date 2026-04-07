from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class LessonCreate(SQLModel):
    title: str
    type: str
    content: str | None = None
    file_key: str | None = None
    duration_minutes: int | None = None
    order_index: int = 0


class LessonRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    title: str
    type: str
    content: str | None
    file_key: str | None
    duration_minutes: int | None
    order_index: int
    is_published: bool
    created_at: datetime
    updated_at: datetime


class LessonUpdate(SQLModel):
    title: str | None = None
    type: str | None = None
    content: str | None = None
    file_key: str | None = None
    duration_minutes: int | None = None
    order_index: int | None = None
    is_published: bool | None = None
