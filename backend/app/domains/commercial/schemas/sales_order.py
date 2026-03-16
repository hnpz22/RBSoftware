from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.domains.commercial.models.sales_order import FulfillmentStatus, OrderStatus


class OrderItemCreate(SQLModel):
    product_public_id: UUID
    quantity: int
    unit_price: Decimal


class OrderItemRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    snapshot_name: str | None
    snapshot_sku: str | None
    created_at: datetime


class OrderCreate(SQLModel):
    external_id: str | None = None
    source: str
    customer_name: str
    customer_email: str
    customer_phone: str | None = None
    shipping_address: str | None = None
    billing_address: str | None = None
    notes: str | None = None
    items: list[OrderItemCreate]


class OrderRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    external_id: str | None
    source: str
    status: OrderStatus
    fulfillment_status: FulfillmentStatus
    customer_name: str
    customer_email: str
    customer_phone: str | None
    shipping_address: str | None
    billing_address: str | None
    notes: str | None
    qr_token: str | None
    created_by_name: str | None = None
    approved_at: datetime | None
    snapshot_frozen_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = []


class OrderUpdate(SQLModel):
    external_id: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    shipping_address: str | None = None
    billing_address: str | None = None
    notes: str | None = None


class ApproveRequest(SQLModel):
    """Location from which to reserve stock when approving the order."""

    location_id: UUID


class ApproveResult(SQLModel):
    order_public_id: UUID
    qr_token: str
    reserved: dict[str, int]
    missing: dict[str, int]
