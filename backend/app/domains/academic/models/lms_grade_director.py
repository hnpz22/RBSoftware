from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class LmsGradeDirector(SQLModel, table=True):
    __tablename__ = "lms_grade_directors"
    __table_args__ = (
        UniqueConstraint("grade_id", "user_id", name="uq_lms_grade_directors_grade_user"),
    )

    id: int | None = Field(default=None, primary_key=True)
    grade_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("lms_grades.id", ondelete="CASCADE"), nullable=False
        )
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    is_active: bool = Field(default=True, nullable=False)
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
