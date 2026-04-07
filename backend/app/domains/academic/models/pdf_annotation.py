from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.mysql import JSON
from sqlmodel import Column, Field, SQLModel


class PDFAnnotation(SQLModel, table=True):
    __tablename__ = "pdf_annotations"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "material_id",
            name="uq_user_material",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    public_id: str = Field(
        default_factory=lambda: str(uuid4()),
        sa_column=Column(String(36), unique=True, nullable=False),
    )
    user_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("users.id"), nullable=False
        )
    )
    material_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("lms_materials.id"), nullable=False
        )
    )
    highlights: Any = Field(
        default=[],
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False),
    )
