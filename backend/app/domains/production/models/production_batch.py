from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class BatchKind(str, enum.Enum):
    SALES = "SALES"
    STOCK = "STOCK"
    FAIR = "FAIR"
    MANUAL = "MANUAL"


class ProductionStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class ProductionBatch(SQLModel, table=True):
    __tablename__ = "production_batches"

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    kind: BatchKind = Field(sa_column=Column(String(20), nullable=False))
    status: ProductionStatus = Field(
        default=ProductionStatus.PENDING,
        sa_column=Column(String(20), nullable=False, server_default="PENDING"),
    )
    name: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    cutoff_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_by: int | None = Field(
        default=None,
        sa_column=Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
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
