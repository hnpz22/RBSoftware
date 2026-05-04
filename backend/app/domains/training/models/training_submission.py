import enum
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class TrainingSubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"


class TrainingSubmission(SQLModel, table=True):
    __tablename__ = "training_submissions"
    __table_args__ = (
        UniqueConstraint(
            "evaluation_id", "user_id", name="uq_training_submissions_evaluation_user"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    evaluation_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("training_evaluations.id"), nullable=False
        )
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False)
    )
    content: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    file_key: str | None = Field(default=None, sa_column=Column(String(500), nullable=True))
    file_name: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    quiz_answers: Any | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    score: int | None = Field(default=None, nullable=True)
    attempts_used: int = Field(default=0, nullable=False)
    feedback: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    status: str = Field(
        default=TrainingSubmissionStatus.PENDING,
        sa_column=Column(String(20), nullable=False, server_default="PENDING"),
    )
    submitted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    graded_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    graded_by: int | None = Field(
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
