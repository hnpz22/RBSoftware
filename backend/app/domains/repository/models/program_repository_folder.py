from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlmodel import Field, SQLModel


class ProgramRepositoryFolder(SQLModel, table=True):
    __tablename__ = "program_repository_folders"
    __table_args__ = (
        UniqueConstraint("program_id", "folder_id", name="uq_program_folder"),
    )

    id: int | None = Field(default=None, primary_key=True)
    program_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("training_programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    folder_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("repository_folders.id", ondelete="CASCADE"),
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
