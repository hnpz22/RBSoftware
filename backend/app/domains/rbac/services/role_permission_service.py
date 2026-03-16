from __future__ import annotations

from sqlmodel import Session

from app.domains.audit.services import AuditService
from app.domains.rbac.models import Permission
from app.domains.rbac.repositories import PermissionRepository, RolePermissionRepository
from app.domains.rbac.schemas import RolePermissionCreate

_audit = AuditService()


class RolePermissionService:
    def assign_permission_to_role(
        self,
        session: Session,
        role_id: int,
        permission_id: int,
        performed_by_id: int | None = None,
    ) -> None:
        repo = RolePermissionRepository(session)
        existing = repo.list_by_role_id(role_id)
        if any(rp.permission_id == permission_id for rp in existing):
            raise ValueError(
                f"Permission {permission_id} is already assigned to role {role_id}"
            )
        repo.create(RolePermissionCreate(role_id=role_id, permission_id=permission_id))
        _audit.log(
            session,
            user_id=performed_by_id,
            action="rbac.assign_permission_to_role",
            resource_type="role",
            resource_id=str(role_id),
            payload={"permission_id": permission_id},
        )

    def remove_permission_from_role(
        self,
        session: Session,
        role_id: int,
        permission_id: int,
        performed_by_id: int | None = None,
    ) -> bool:
        repo = RolePermissionRepository(session)
        existing = repo.list_by_role_id(role_id)
        record = next((rp for rp in existing if rp.permission_id == permission_id), None)
        if record is None:
            return False
        repo.delete(record)
        _audit.log(
            session,
            user_id=performed_by_id,
            action="rbac.remove_permission_from_role",
            resource_type="role",
            resource_id=str(role_id),
            payload={"permission_id": permission_id},
        )
        return True

    def get_permissions_for_role(
        self, session: Session, role_id: int
    ) -> list[Permission]:
        rp_repo = RolePermissionRepository(session)
        perm_repo = PermissionRepository(session)
        role_permissions = rp_repo.list_by_role_id(role_id)
        permissions = []
        for rp in role_permissions:
            perm = perm_repo.get_by_id(rp.permission_id)
            if perm is not None:
                permissions.append(perm)
        return permissions
