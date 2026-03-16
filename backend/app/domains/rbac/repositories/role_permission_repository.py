from __future__ import annotations

from sqlmodel import Session, select

from app.domains.rbac.models import RolePermission
from app.domains.rbac.schemas import RolePermissionCreate, RolePermissionUpdate


class RolePermissionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: RolePermissionCreate) -> RolePermission:
        role_permission = RolePermission.model_validate(payload)
        self.session.add(role_permission)
        self.session.commit()
        self.session.refresh(role_permission)
        return role_permission

    def get_by_id(self, role_permission_id: int) -> RolePermission | None:
        return self.session.get(RolePermission, role_permission_id)

    def list(self) -> list[RolePermission]:
        statement = select(RolePermission).order_by(RolePermission.id)
        return list(self.session.exec(statement).all())

    def list_by_role_id(self, role_id: int) -> list[RolePermission]:
        statement = select(RolePermission).where(RolePermission.role_id == role_id)
        return list(self.session.exec(statement).all())

    def update(
        self,
        role_permission: RolePermission,
        payload: RolePermissionUpdate,
    ) -> RolePermission:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(role_permission, field_name, value)

        self.session.add(role_permission)
        self.session.commit()
        self.session.refresh(role_permission)
        return role_permission

    def delete(self, role_permission: RolePermission) -> None:
        self.session.delete(role_permission)
        self.session.commit()
