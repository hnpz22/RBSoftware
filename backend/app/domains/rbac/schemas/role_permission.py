from __future__ import annotations

from datetime import datetime

from sqlmodel import SQLModel


class RolePermissionCreate(SQLModel):
    role_id: int
    permission_id: int


class RolePermissionRead(SQLModel):
    id: int
    role_id: int
    permission_id: int
    created_at: datetime
    updated_at: datetime


class RolePermissionUpdate(SQLModel):
    role_id: int | None = None
    permission_id: int | None = None
