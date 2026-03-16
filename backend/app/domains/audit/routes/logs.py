from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.domains.audit.schemas import AuditLogRead
from app.domains.audit.services import AuditService
from app.domains.auth.dependencies import get_current_user  # noqa: F401 — auth guard
from app.domains.auth.repositories import UserRepository

router = APIRouter(prefix="/audit", tags=["audit"])

_svc = AuditService()


@router.get("/logs", response_model=list[AuditLogRead])
def list_audit_logs(
    resource_type: str | None = Query(default=None),
    user_id: UUID | None = Query(default=None, description="Public ID of the user"),
    limit: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[AuditLogRead]:
    # Resolve public user_id → internal int id for repository filter
    internal_user_id: int | None = None
    if user_id is not None:
        user = UserRepository(session).get_by_public_id(user_id)
        if user is not None:
            internal_user_id = user.id

    entries = _svc.list(session, resource_type=resource_type, user_id=internal_user_id, limit=limit)
    return [AuditLogRead.model_validate(e) for e in entries]
