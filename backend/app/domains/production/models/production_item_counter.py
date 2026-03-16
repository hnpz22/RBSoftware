from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlmodel import Field, SQLModel


class ProductionItemCounter(SQLModel, table=True):
    __tablename__ = "production_item_counters"

    id: int | None = Field(default=None, primary_key=True)
    batch_item_id: int = Field(
        sa_column=Column(
            ForeignKey("production_batch_items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    counted_by: int | None = Field(
        default=None,
        sa_column=Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    count: int = Field(sa_column=Column(Integer, nullable=False))
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
