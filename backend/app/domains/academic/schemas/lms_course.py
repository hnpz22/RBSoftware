from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class LmsCourseCreate(SQLModel):
    name: str
    description: str | None = None
    year: int
    is_active: bool = True


class LmsCourseRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    description: str | None
    year: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LmsCourseUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    year: int | None = None
    is_active: bool | None = None
