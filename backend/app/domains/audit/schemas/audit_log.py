from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class AuditLogCreate(SQLModel):
    user_id: int | None = None
    action: str
    resource_type: str
    resource_id: str
    payload: dict | None = None
    ip_address: str | None = None


class AuditLogRead(SQLModel):
    # audit_logs has no public_id in db.sql — id is the only identifier
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    resource_type: str
    resource_id: str
    payload: dict | None
    ip_address: str | None
    created_at: datetime
