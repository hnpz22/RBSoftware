from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlmodel import Field, SQLModel


class ProgramRepositoryFile(SQLModel, table=True):
    __tablename__ = "program_repository_files"
    __table_args__ = (
        UniqueConstraint("program_id", "file_id", name="uq_program_file"),
    )

    id: int | None = Field(default=None, primary_key=True)
    program_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("training_programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    file_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("repository_files.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    assigned_by: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False),
    )
