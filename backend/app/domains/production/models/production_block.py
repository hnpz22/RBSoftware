from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlmodel import Field, SQLModel


class ProductionBlock(SQLModel, table=True):
    __tablename__ = "production_blocks"

    id: int | None = Field(default=None, primary_key=True)
    batch_item_id: int = Field(
        sa_column=Column(
            ForeignKey("production_batch_items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    component_id: int = Field(
        sa_column=Column(
            ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
        )
    )
    missing_qty: int = Field(sa_column=Column(Integer, nullable=False))
    resolved_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
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
