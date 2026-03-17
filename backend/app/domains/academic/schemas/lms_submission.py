from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class LmsSubmissionCreate(SQLModel):
    assignment_id: int
    student_id: int
    content: str | None = None
    file_key: str | None = None
    file_name: str | None = None
    status: str = "DRAFT"


class LmsSubmissionRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    content: str | None
    file_key: str | None
    file_name: str | None
    status: str
    score: Decimal | None
    feedback: str | None
    graded_at: datetime | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LmsSubmissionUpdate(SQLModel):
    content: str | None = None
    file_key: str | None = None
    file_name: str | None = None
    status: str | None = None
    score: Decimal | None = None
    feedback: str | None = None
    graded_by: int | None = None
    graded_at: datetime | None = None
    submitted_at: datetime | None = None
