from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class ComponentMovementType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    CONSUME = "CONSUME"
    ADJUST = "ADJUST"


class ComponentInventoryMovement(SQLModel, table=True):
    __tablename__ = "component_inventory_movements"

    id: int | None = Field(default=None, primary_key=True)
    component_id: int = Field(
        sa_column=Column(
            ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    location_id: int = Field(
        sa_column=Column(
            ForeignKey("stock_locations.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    movement_type: ComponentMovementType = Field(sa_column=Column(String(20), nullable=False))
    quantity: int = Field(sa_column=Column(Integer, nullable=False))
    from_status: str | None = Field(default=None, sa_column=Column(String(30), nullable=True))
    to_status: str | None = Field(default=None, sa_column=Column(String(30), nullable=True))
    batch_id: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    performed_by: int | None = Field(
        default=None,
        sa_column=Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
