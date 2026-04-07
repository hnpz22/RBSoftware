from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class EnrollmentRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    enrolled_at: datetime
    completed_at: datetime | None
    status: Literal["ACTIVE", "COMPLETED", "SUSPENDED", "CANCELLED"]
    created_at: datetime
    updated_at: datetime
