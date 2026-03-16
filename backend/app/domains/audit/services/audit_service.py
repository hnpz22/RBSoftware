from __future__ import annotations

from sqlmodel import Session

from app.domains.audit.models import AuditLog
from app.domains.audit.repositories import AuditLogRepository
from app.domains.audit.schemas import AuditLogCreate


class AuditService:
    def log(
        self,
        session: Session,
        *,
        user_id: int | None,
        action: str,
        resource_type: str,
        resource_id: str,
        payload: dict | None = None,
        ip: str | None = None,
    ) -> AuditLog:
        return AuditLogRepository(session).create(
            AuditLogCreate(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                payload=payload,
                ip_address=ip,
            )
        )

    def list(
        self,
        session: Session,
        resource_type: str | None = None,
        user_id: int | None = None,
        limit: int = 50,
    ) -> list[AuditLog]:
        return AuditLogRepository(session).list(
            resource_type=resource_type,
            user_id=user_id,
            limit=limit,
        )
