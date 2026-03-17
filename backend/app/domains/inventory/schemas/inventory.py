from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.domains.inventory.models.inventory_balance import StockStatus
from app.domains.inventory.models.inventory_movement import StockMovementType


class BalanceRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    location_id: int
    status: StockStatus
    quantity: int
    updated_at: datetime


class BalanceSummaryItem(SQLModel):
    product_id: int
    status: str
    total_quantity: int


class MovementRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    location_id: int
    movement_type: StockMovementType
    quantity: int
    from_status: str | None
    to_status: str | None
    notes: str | None
    created_at: datetime


class ManualAdjustmentCreate(SQLModel):
    """Payload for POST /inventory/movements (manual stock adjust)."""

    product_public_id: UUID
    location_public_id: UUID
    status: StockStatus
    delta: int  # positive = add, negative = subtract
    notes: str | None = None


class StockAlertItem(SQLModel):
    """Per-product stock alert with semaphore color."""

    product_id: int
    product_name: str
    sku: str
    total_free: int
    status_color: str  # 'RED' | 'YELLOW' | 'GREEN'
