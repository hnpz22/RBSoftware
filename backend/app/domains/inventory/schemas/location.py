from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.domains.inventory.models.stock_location import LocationType


class LocationCreate(SQLModel):
    name: str
    type: LocationType
    address: str | None = None
    is_active: bool = True


class LocationRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    type: LocationType
    address: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LocationUpdate(SQLModel):
    name: str | None = None
    type: LocationType | None = None
    address: str | None = None
    is_active: bool | None = None
