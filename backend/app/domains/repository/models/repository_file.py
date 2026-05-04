from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlmodel import Field, SQLModel


class RepositoryFile(SQLModel, table=True):
    __tablename__ = "repository_files"

    id: int | None = Field(default=None, primary_key=True)
    public_id: str = Field(
        default_factory=lambda: str(uuid4()),
        sa_column=Column(String(36), unique=True, nullable=False),
    )
    folder_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("repository_folders.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    file_key: str = Field(sa_column=Column(String(500), nullable=False))
    file_name: str = Field(sa_column=Column(String(255), nullable=False))
    file_size: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    file_type: str | None = Field(default=None, sa_column=Column(String(50), nullable=True))
    uploaded_by: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False),
    )
