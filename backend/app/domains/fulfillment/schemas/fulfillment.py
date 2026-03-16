from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PackItemRead(BaseModel):
    id: int
    public_id: UUID
    sales_order_id: int
    product_id: int
    required_qty: int
    confirmed_qty: int

    model_config = {"from_attributes": True}


class PackEventRead(BaseModel):
    id: int
    sales_order_id: int
    product_id: int | None
    event_type: str
    quantity: int | None
    scanned_qr: str | None
    performed_by: int | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PackStatusResponse(BaseModel):
    order_public_id: UUID
    fulfillment_status: str
    items: list[PackItemRead]
    events: list[PackEventRead]


class ScanOrderRequest(BaseModel):
    qr_token: str


class ScanKitRequest(BaseModel):
    order_public_id: UUID
    product_qr: str


class ConfirmComponentRequest(BaseModel):
    product_public_id: UUID
    quantity: int
