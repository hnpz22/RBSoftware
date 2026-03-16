from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class StockStatus(str, enum.Enum):
    FREE = "FREE"
    RESERVED_WEB = "RESERVED_WEB"
    RESERVED_FAIR = "RESERVED_FAIR"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    TO_DISASSEMBLE = "TO_DISASSEMBLE"
    LOST = "LOST"
    DAMAGED = "DAMAGED"
    BLOCKED = "BLOCKED"


class InventoryBalance(SQLModel, table=True):
    __tablename__ = "inventory_balances"
    __table_args__ = (
        UniqueConstraint("product_id", "location_id", "status", name="uq_inv_balance"),
    )

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
    status: StockStatus = Field(sa_column=Column(String(30), nullable=False))
    quantity: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
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
