from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class LmsAssignmentCreate(SQLModel):
    title: str
    description: str | None = None
    max_score: Decimal
    due_date: datetime | None = None
    order_index: int = 0


class LmsAssignmentRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    title: str
    description: str | None
    max_score: Decimal
    due_date: datetime | None
    order_index: int
    is_published: bool
    created_at: datetime
    updated_at: datetime


class LmsAssignmentUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    max_score: Decimal | None = None
    due_date: datetime | None = None
    order_index: int | None = None
