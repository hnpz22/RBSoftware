from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class SchoolTeacher(SQLModel, table=True):
    __tablename__ = "school_teachers"
    __table_args__ = (
        UniqueConstraint("school_id", "user_id", name="uq_school_teachers_school_user"),
    )

    id: int | None = Field(default=None, primary_key=True)
    school_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
        )
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
