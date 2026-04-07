from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class LessonProgressRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    completed_at: datetime
    created_at: datetime
