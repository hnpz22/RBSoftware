from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    UNPAID = "UNPAID"
    APPROVED = "APPROVED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class FulfillmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class SalesOrder(SQLModel, table=True):
    __tablename__ = "sales_orders"

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    external_id: str | None = Field(
        default=None, sa_column=Column(String(100), nullable=True)
    )
    source: str = Field(sa_column=Column(String(50), nullable=False))
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        sa_column=Column(String(20), nullable=False, server_default="PENDING"),
    )
    fulfillment_status: FulfillmentStatus = Field(
        default=FulfillmentStatus.PENDING,
        sa_column=Column(String(20), nullable=False, server_default="PENDING"),
    )
    customer_name: str = Field(sa_column=Column(String(255), nullable=False))
    customer_email: str = Field(sa_column=Column(String(255), nullable=False))
    customer_phone: str | None = Field(
        default=None, sa_column=Column(String(30), nullable=True)
    )
    shipping_address: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    billing_address: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    qr_token: str | None = Field(
        default=None, sa_column=Column(String(64), nullable=True, unique=True)
    )
    created_by: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    approved_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    snapshot_frozen_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
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
