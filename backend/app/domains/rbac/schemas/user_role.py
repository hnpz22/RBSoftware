from __future__ import annotations

from datetime import datetime

from sqlmodel import SQLModel


class UserRoleCreate(SQLModel):
    user_id: int
    role_id: int


class UserRoleRead(SQLModel):
    id: int
    user_id: int
    role_id: int
    created_at: datetime
    updated_at: datetime


class UserRoleUpdate(SQLModel):
    user_id: int | None = None
    role_id: int | None = None
