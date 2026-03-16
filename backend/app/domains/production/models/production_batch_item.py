from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlmodel import Field, SQLModel


class ProductionBatchItem(SQLModel, table=True):
    __tablename__ = "production_batch_items"

    id: int | None = Field(default=None, primary_key=True)
    batch_id: int = Field(
        sa_column=Column(
            ForeignKey("production_batches.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    product_id: int = Field(
        sa_column=Column(
            ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
        )
    )
    required_qty_total: int = Field(sa_column=Column(Integer, nullable=False))
    available_stock_qty: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
    )
    to_produce_qty: int = Field(sa_column=Column(Integer, nullable=False))
    produced_qty: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
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
