from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.domains.production.models.production_batch import BatchKind, ProductionStatus


class BlockRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    component_id: int
    missing_qty: int
    resolved_at: datetime | None
    notes: str | None


class BatchItemRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    required_qty_total: int
    available_stock_qty: int
    to_produce_qty: int
    produced_qty: int
    blocks: list[BlockRead] = []


class LinkedOrderRead(SQLModel):
    sales_order_id: int
    link_mode: str


class BatchRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    kind: BatchKind
    status: ProductionStatus
    name: str | None
    notes: str | None
    cutoff_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[BatchItemRead] = []
    linked_orders: list[LinkedOrderRead] = []


class BatchItemCreate(SQLModel):
    product_public_id: UUID
    required_qty_total: int
    available_stock_qty: int = 0


class BatchCreate(SQLModel):
    kind: BatchKind
    name: str | None = None
    notes: str | None = None
    items: list[BatchItemCreate] = []
    sales_order_public_ids: list[UUID] = []


class BatchStatusUpdate(SQLModel):
    status: ProductionStatus


# ── Master sheet ──────────────────────────────────────────────────────────────


class BomComponentDetail(SQLModel):
    component_id: int
    component_sku: str
    component_name: str
    qty_per_kit: int
    total_needed: int
    available: int
    missing: int


class MasterSheetItem(SQLModel):
    batch_item_id: int
    product_id: int
    product_sku: str
    product_name: str
    required_qty_total: int
    available_stock_qty: int
    to_produce_qty: int
    produced_qty: int
    bom: list[BomComponentDetail]
    blocks: list[BlockRead]


class MasterSheetResponse(SQLModel):
    batch_public_id: UUID
    kind: str
    status: str
    name: str | None
    cutoff_at: datetime | None
    items: list[MasterSheetItem]
    linked_orders: list[LinkedOrderRead]
