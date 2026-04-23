from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlmodel import Field, SQLModel


class Rubric(SQLModel, table=True):
    __tablename__ = "rubrics"

    id: int | None = Field(default=None, primary_key=True)
    public_id: str = Field(
        default_factory=lambda: str(uuid4()),
        sa_column=Column(String(36), unique=True, nullable=False),
    )
    title: str = Field(sa_column=Column(String(255), nullable=False))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    training_evaluation_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("training_evaluations.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    lms_assignment_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("lms_assignments.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False),
    )
