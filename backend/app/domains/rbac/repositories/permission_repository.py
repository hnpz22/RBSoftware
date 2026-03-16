from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.rbac.models import Permission
from app.domains.rbac.schemas import PermissionCreate, PermissionUpdate


class PermissionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: PermissionCreate) -> Permission:
        permission = Permission.model_validate(payload)
        self.session.add(permission)
        self.session.commit()
        self.session.refresh(permission)
        return permission

    def get_by_id(self, permission_id: int) -> Permission | None:
        return self.session.get(Permission, permission_id)

    def get_by_public_id(self, public_id: UUID) -> Permission | None:
        statement = select(Permission).where(Permission.public_id == public_id)
        return self.session.exec(statement).first()

    def get_by_code(self, code: str) -> Permission | None:
        statement = select(Permission).where(Permission.code == code)
        return self.session.exec(statement).first()

    def list(self) -> list[Permission]:
        statement = select(Permission).order_by(Permission.id)
        return list(self.session.exec(statement).all())

    def update(self, permission: Permission, payload: PermissionUpdate) -> Permission:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(permission, field_name, value)

        self.session.add(permission)
        self.session.commit()
        self.session.refresh(permission)
        return permission

    def delete(self, permission: Permission) -> None:
        self.session.delete(permission)
        self.session.commit()
