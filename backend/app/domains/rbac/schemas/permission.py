from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class PermissionCreate(SQLModel):
    code: str
    description: str | None = None


class PermissionRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    code: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class PermissionUpdate(SQLModel):
    code: str | None = None
    description: str | None = None
