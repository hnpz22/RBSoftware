from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class TrainingProgram(SQLModel, table=True):
    __tablename__ = "training_programs"

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    objective: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    duration_hours: int | None = Field(default=None, nullable=True)
    is_active: bool = Field(default=True, nullable=False)
    is_published: bool = Field(default=False, nullable=False)
    certificate_template_key: str | None = Field(
        default=None, sa_column=Column(String(500), nullable=True)
    )
    created_by: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=True),
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
