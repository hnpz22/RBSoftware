from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class SchoolCreate(SQLModel):
    name: str
    code: str
    address: str | None = None
    city: str | None = None
    phone: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    is_active: bool = True


class SchoolRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    code: str
    address: str | None
    city: str | None
    phone: str | None
    contact_name: str | None
    contact_email: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SchoolUpdate(SQLModel):
    name: str | None = None
    code: str | None = None
    address: str | None = None
    city: str | None = None
    phone: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    is_active: bool | None = None
