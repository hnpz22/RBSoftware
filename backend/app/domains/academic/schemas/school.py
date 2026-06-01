from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.domains.academic.models.school import WorkLine


class SchoolCreate(SQLModel):
    name: str
    city: str | None = None
    address: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    work_line: WorkLine | None = None
    is_active: bool = True


class SchoolRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    city: str | None
    address: str | None
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    work_line: WorkLine | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SchoolUpdate(SQLModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    work_line: WorkLine | None = None
    is_active: bool | None = None
