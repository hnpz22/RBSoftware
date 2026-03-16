from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class KitBomItemAdd(SQLModel):
    """Request body for adding a component to a kit's BOM."""

    component_id: UUID  # public_id of the component product
    quantity: int
    notes: str | None = None


class KitBomItemRead(SQLModel):
    """BOM entry with embedded component details for display."""

    component_public_id: UUID
    component_sku: str
    component_name: str
    quantity: int
    notes: str | None
    created_at: datetime
