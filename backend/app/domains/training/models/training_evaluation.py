from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class TrainingEvaluation(SQLModel, table=True):
    __tablename__ = "training_evaluations"

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    module_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("training_modules.id"), nullable=False
        )
    )
    title: str = Field(sa_column=Column(String(255), nullable=False))
    type: str = Field(sa_column=Column(String(20), nullable=False))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    max_score: int = Field(default=100, nullable=False)
    passing_score: int = Field(default=60, nullable=False)
    max_attempts: int = Field(default=3, nullable=False)
    is_published: bool = Field(default=False, nullable=False)
    after_lesson_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("training_lessons.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
