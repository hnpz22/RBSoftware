from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class UserCreate(SQLModel):
    email: str
    password_hash: str
    is_active: bool = True


class UserRead(SQLModel):
    public_id: UUID
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(SQLModel):
    email: str | None = None
    password_hash: str | None = None
    is_active: bool | None = None
