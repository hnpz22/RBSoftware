from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class LmsCourseStudent(SQLModel, table=True):
    __tablename__ = "lms_course_students"
    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_lms_course_students_course_user"),
    )

    id: int | None = Field(default=None, primary_key=True)
    course_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("lms_courses.id", ondelete="CASCADE"), nullable=False
        )
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    transferred_from_course_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("lms_courses.id", ondelete="SET NULL"), nullable=True
        ),
    )
    is_active: bool = Field(default=True, nullable=False)
    enrolled_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
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
