from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class RoleCreate(SQLModel):
    name: str
    description: str | None = None


class RoleRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class RoleUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
