from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    email: str
    password_hash: str
    first_name: str
    last_name: str
    phone: str | None = None
    position: str | None = None
    is_active: bool = True


class SchoolBrief(SQLModel):
    """Colegio al que un usuario está afiliado, para pintar y filtrar la lista."""

    public_id: UUID
    name: str


class UserRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    email: str
    first_name: str
    last_name: str
    phone: str | None
    position: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    roles: list[str] = []
    # Vacío para quien no tiene colegio (ADMIN, TRAINER…) y para quien perdió su
    # única afiliación activa. Un docente puede estar en varios.
    schools: list[SchoolBrief] = []


class UserUpdate(SQLModel):
    email: str | None = None
    password_hash: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    position: str | None = None
    is_active: bool | None = None
