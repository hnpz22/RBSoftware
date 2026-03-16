from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SyncStatusResponse(BaseModel):
    integration_name: str
    status: str
    last_synced_at: datetime | None
    last_cursor: str | None
    error_message: str | None

    model_config = {"from_attributes": True}


class SyncRequest(BaseModel):
    since: datetime | None = None


class SyncResult(BaseModel):
    orders_processed: int
    orders_created: int
    orders_updated: int
    status: str
