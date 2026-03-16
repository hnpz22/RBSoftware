from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.domains.catalog.models.product import ProductType


class ProductCreate(SQLModel):
    sku: str
    name: str
    type: ProductType
    description: str | None = None
    qr_code: str | None = None
    cut_file_key: str | None = None
    cut_file_notes: str | None = None
    is_active: bool = True


class ProductRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    sku: str
    name: str
    type: ProductType
    description: str | None
    qr_code: str | None
    is_active: bool
    cut_file_key: str | None
    cut_file_notes: str | None
    created_at: datetime
    updated_at: datetime


class ProductUpdate(SQLModel):
    sku: str | None = None
    name: str | None = None
    type: ProductType | None = None
    description: str | None = None
    qr_code: str | None = None
    is_active: bool | None = None
    cut_file_key: str | None = None
    cut_file_notes: str | None = None
