from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class ModuleCreate(SQLModel):
    title: str
    description: str | None = None
    order_index: int = 0


class ModuleRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    title: str
    description: str | None
    order_index: int
    is_published: bool
    created_at: datetime
    updated_at: datetime


class ModuleUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    order_index: int | None = None
    is_published: bool | None = None
