from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, func
from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(
        default=None,
        sa_column=Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    action: str = Field(
        sa_column=Column(String(100), nullable=False, index=True)
    )
    resource_type: str = Field(
        sa_column=Column(String(100), nullable=False, index=True)
    )
    resource_id: str = Field(
        sa_column=Column(String(36), nullable=False)
    )
    payload: dict | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    ip_address: str | None = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
