from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.domains.inventory.models.component_inventory_balance import ComponentStockStatus
from app.domains.inventory.models.component_inventory_movement import ComponentMovementType


class ComponentBalanceRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    component_id: int
    location_id: int
    status: ComponentStockStatus
    quantity: int
    updated_at: datetime


class ComponentBalanceSummaryItem(SQLModel):
    component_id: int
    status: str
    total_quantity: int


class ComponentMovementRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    component_id: int
    location_id: int
    movement_type: ComponentMovementType
    quantity: int
    from_status: str | None
    to_status: str | None
    notes: str | None
    created_at: datetime


class ComponentManualAdjustmentCreate(SQLModel):
    """Payload for POST /inventory/components/movements (manual component adjust)."""

    component_public_id: UUID
    location_public_id: UUID
    status: ComponentStockStatus
    delta: int
    notes: str | None = None
