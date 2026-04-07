from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class CertificateRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    certificate_code: str
    badge_key: str | None
    issued_at: datetime
    created_at: datetime
    updated_at: datetime
