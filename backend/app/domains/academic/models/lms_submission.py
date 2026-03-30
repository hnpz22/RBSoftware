import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.types import Uuid
from sqlmodel import Field, SQLModel


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"


class LmsSubmission(SQLModel, table=True):
    __tablename__ = "lms_submissions"
    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "student_id", name="uq_lms_submissions_assignment_student"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    assignment_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("lms_assignments.id", ondelete="CASCADE"), nullable=False
        )
    )
    student_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    content: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    file_key: str | None = Field(default=None, sa_column=Column(String(500), nullable=True))
    file_name: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    score: int | None = Field(default=None, nullable=True)
    feedback: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    status: str = Field(
        default=SubmissionStatus.PENDING,
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
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
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
