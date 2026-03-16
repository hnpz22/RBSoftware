from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text, func
from sqlmodel import Field, SQLModel


class IntegrationSyncState(SQLModel, table=True):
    __tablename__ = "integration_sync_states"

    id: int | None = Field(default=None, primary_key=True)
    integration_name: str = Field(
        sa_column=Column(String(100), nullable=False, unique=True, index=True)
    )
    last_synced_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    # ISO-8601 datetime string used as the "modified_after" cursor on next sync
    last_cursor: str | None = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    status: str = Field(
        default="NEVER",
        sa_column=Column(String(20), nullable=False, server_default="NEVER"),
    )
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
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
