from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class ProgramCreate(SQLModel):
    name: str
    description: str | None = None
    objective: str | None = None
    duration_hours: int | None = None
    is_active: bool = True


class ProgramRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    description: str | None
    objective: str | None
    duration_hours: int | None
    is_active: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime


class ProgramUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    objective: str | None = None
    duration_hours: int | None = None
    is_active: bool | None = None
    is_published: bool | None = None
