from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class LmsGradeCreate(SQLModel):
    name: str
    label: str | None = None
    order_index: int = 0
    is_active: bool = True


class LmsGradeRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    label: str | None
    order_index: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LmsGradeUpdate(SQLModel):
    name: str | None = None
    label: str | None = None
    order_index: int | None = None
    is_active: bool | None = None
