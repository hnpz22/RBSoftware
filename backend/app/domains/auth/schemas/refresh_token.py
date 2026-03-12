from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class RefreshTokenCreate(SQLModel):
    user_id: int
    token_hash: str
    expires_at: datetime


class RefreshTokenRead(SQLModel):
    public_id: UUID
    user_id: int
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RefreshTokenUpdate(SQLModel):
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
