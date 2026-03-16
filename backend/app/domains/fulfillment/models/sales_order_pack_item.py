from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class SalesOrderPackItem(SQLModel, table=True):
    __tablename__ = "sales_order_pack_items"

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    sales_order_id: int = Field(
        sa_column=Column(Integer, nullable=False, index=True)
    )
    product_id: int = Field(
        sa_column=Column(Integer, nullable=False, index=True)
    )
    required_qty: int = Field(sa_column=Column(Integer, nullable=False))
    confirmed_qty: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default="0"),
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
