from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class ProductType(str, enum.Enum):
    KIT = "KIT"
    COMPONENT = "COMPONENT"


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    sku: str = Field(sa_column=Column(String(100), nullable=False, unique=True, index=True))
    name: str = Field(sa_column=Column(String(255), nullable=False))
    type: ProductType = Field(
        sa_column=Column(sa.Enum(ProductType, name="product_type"), nullable=False)
    )
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    qr_code: str | None = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    is_active: bool = Field(default=True, nullable=False)
    # Chassis / laser-cut file (COMPONENT only)
    cut_file_key: str | None = Field(
        default=None, sa_column=Column(String(500), nullable=True)
    )
    cut_file_notes: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        ),
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
    # No ORM Relationships defined — circular FK disambiguation causes issues
    # with from __future__ import annotations. Use explicit repository queries.
