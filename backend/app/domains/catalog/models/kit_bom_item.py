from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class KitBomItem(SQLModel, table=True):
    __tablename__ = "kit_bom_items"
    __table_args__ = (
        UniqueConstraint("kit_id", "component_id", name="uq_kit_bom_items_pair"),
    )

    id: int | None = Field(default=None, primary_key=True)
    kit_id: int = Field(
        sa_column=Column(
            ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    component_id: int = Field(
        sa_column=Column(
            ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    quantity: int = Field(nullable=False)
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
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

    # No ORM Relationships defined — two FKs to same table + from __future__ import annotations
    # causes SQLAlchemy mapper resolution failures. Use explicit repository JOIN queries.
