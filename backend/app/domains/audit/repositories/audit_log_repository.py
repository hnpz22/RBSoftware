from __future__ import annotations

from sqlmodel import Session, select

from app.domains.audit.models import AuditLog
from app.domains.audit.schemas import AuditLogCreate


class AuditLogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: AuditLogCreate) -> AuditLog:
        entry = AuditLog.model_validate(payload)
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def list(
        self,
        resource_type: str | None = None,
        user_id: int | None = None,
        limit: int = 50,
    ) -> list[AuditLog]:
        statement = select(AuditLog)
        if resource_type is not None:
            statement = statement.where(AuditLog.resource_type == resource_type)
        if user_id is not None:
            statement = statement.where(AuditLog.user_id == user_id)
        statement = statement.order_by(AuditLog.id.desc()).limit(limit)  # type: ignore[arg-type]
        return list(self.session.exec(statement).all())
