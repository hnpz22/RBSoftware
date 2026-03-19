from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class GradeCreate(SQLModel):
    name: str
    description: str | None = None
    is_active: bool = True


class GradeRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GradeUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
