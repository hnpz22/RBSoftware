from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class QuizQuestionCreate(SQLModel):
    question: str
    options: list[dict[str, Any]]
    correct_option: int
    points: int = 10
    order_index: int = 0


class QuizQuestionRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    question: str
    options: list[dict[str, Any]]
    correct_option: int
    points: int
    order_index: int
    created_at: datetime
    updated_at: datetime


class QuizQuestionUpdate(SQLModel):
    question: str | None = None
    options: list[dict[str, Any]] | None = None
    correct_option: int | None = None
    points: int | None = None
    order_index: int | None = None
