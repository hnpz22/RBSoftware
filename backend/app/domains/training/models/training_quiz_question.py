from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class TrainingQuizQuestion(SQLModel, table=True):
    """Quiz question for a training evaluation.

    options format:
        [
            {"id": 0, "text": "Opción A"},
            {"id": 1, "text": "Opción B"},
            {"id": 2, "text": "Opción C"},
            {"id": 3, "text": "Opción D"}
        ]
    correct_option: int index (0-3) matching an option id.
    """

    __tablename__ = "training_quiz_questions"

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
    question: str = Field(sa_column=Column(Text, nullable=False))
    options: Any = Field(
        default=[],
        sa_column=Column(JSON, nullable=False),
    )
    correct_option: int = Field(nullable=False)
    points: int = Field(default=10, nullable=False)
    order_index: int = Field(default=0, nullable=False)
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
