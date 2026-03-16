from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlmodel import Field, SQLModel


class SalesOrderItem(SQLModel, table=True):
    __tablename__ = "sales_order_items"

    id: int | None = Field(default=None, primary_key=True)
    sales_order_id: int = Field(
        sa_column=Column(
            ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    product_id: int = Field(
        sa_column=Column(
            ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
        )
    )
    quantity: int = Field(sa_column=Column(Integer, nullable=False))
    unit_price: Decimal = Field(
        sa_column=Column(sa.Numeric(12, 2), nullable=False)
    )
    # Snapshot fields — populated when order is approved
    snapshot_name: str | None = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    snapshot_sku: str | None = Field(
        default=None, sa_column=Column(String(100), nullable=True)
    )
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
