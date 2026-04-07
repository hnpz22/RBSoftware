from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class EvaluationCreate(SQLModel):
    title: str
    type: str
    description: str | None = None
    max_score: int = 100
    passing_score: int = 60


class EvaluationRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    title: str
    type: str
    description: str | None
    max_score: int
    passing_score: int
    is_published: bool
    created_at: datetime
    updated_at: datetime


class EvaluationUpdate(SQLModel):
    title: str | None = None
    type: str | None = None
    description: str | None = None
    max_score: int | None = None
    passing_score: int | None = None
    is_published: bool | None = None
