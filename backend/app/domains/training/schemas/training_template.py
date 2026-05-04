from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class TemplateRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    title: str
    description: str | None
    file_name: str
    file_size: int | None
    uploaded_by: int | None
    created_at: datetime
    updated_at: datetime
