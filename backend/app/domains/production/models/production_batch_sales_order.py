from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class BatchLinkMode(str, enum.Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"


class ProductionBatchSalesOrder(SQLModel, table=True):
    __tablename__ = "production_batch_sales_orders"
    __table_args__ = (
        UniqueConstraint("batch_id", "sales_order_id", name="uq_batch_sales_order"),
    )

    id: int | None = Field(default=None, primary_key=True)
    batch_id: int = Field(
        sa_column=Column(
            ForeignKey("production_batches.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    sales_order_id: int = Field(
        sa_column=Column(
            ForeignKey("sales_orders.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    link_mode: BatchLinkMode = Field(sa_column=Column(String(10), nullable=False))
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
