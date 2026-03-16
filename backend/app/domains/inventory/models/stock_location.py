from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class LocationType(str, enum.Enum):
    WAREHOUSE = "WAREHOUSE"
    SEDE = "SEDE"
    FAIR = "FAIR"
    SCHOOL = "SCHOOL"


class StockLocation(SQLModel, table=True):
    __tablename__ = "stock_locations"

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    name: str = Field(sa_column=Column(String(100), nullable=False))
    type: LocationType = Field(sa_column=Column(String(50), nullable=False))
    address: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )
