from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlmodel import Field, SQLModel


class PackEventType(str, enum.Enum):
    KIT_SCANNED = "KIT_SCANNED"
    COMPONENT_CONFIRMED = "COMPONENT_CONFIRMED"
    PACK_CLOSED = "PACK_CLOSED"
    PACK_REOPENED = "PACK_REOPENED"


class SalesOrderPackEvent(SQLModel, table=True):
    __tablename__ = "sales_order_pack_events"

    id: int | None = Field(default=None, primary_key=True)
    sales_order_id: int = Field(
        sa_column=Column(Integer, nullable=False, index=True)
    )
    product_id: int | None = Field(
        default=None, sa_column=Column(Integer, nullable=True)
    )
    event_type: str = Field(
        sa_column=Column(String(30), nullable=False)
    )
    quantity: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    scanned_qr: str | None = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    performed_by: int | None = Field(
        default=None, sa_column=Column(Integer, nullable=True)
    )
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
