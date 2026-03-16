from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class StockMovementType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    ADJUST = "ADJUST"


class InventoryMovement(SQLModel, table=True):
    __tablename__ = "inventory_movements"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(
        sa_column=Column(
            ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    location_id: int = Field(
        sa_column=Column(
            ForeignKey("stock_locations.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    movement_type: StockMovementType = Field(sa_column=Column(String(20), nullable=False))
    quantity: int = Field(sa_column=Column(Integer, nullable=False))
    from_status: str | None = Field(default=None, sa_column=Column(String(30), nullable=True))
    to_status: str | None = Field(default=None, sa_column=Column(String(30), nullable=True))
    # Forward references to tables not yet created — stored as plain integers without FK
    sales_order_id: int | None = Field(
        default=None, sa_column=Column(Integer, nullable=True)
    )
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
