from __future__ import annotations

from sqlmodel import Session

from app.domains.audit.services import AuditService
from app.domains.rbac.models import Role
from app.domains.rbac.repositories import (
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
    UserRoleRepository,
)
from app.domains.rbac.schemas import UserRoleCreate

_audit = AuditService()


class UserRoleService:
    def assign_role_to_user(
        self,
        session: Session,
        user_id: int,
        role_id: int,
        performed_by_id: int | None = None,
    ) -> None:
        repo = UserRoleRepository(session)
        existing = repo.list_by_user_id(user_id)
        if any(ur.role_id == role_id for ur in existing):
            raise ValueError(f"Role {role_id} is already assigned to user {user_id}")
        repo.create(UserRoleCreate(user_id=user_id, role_id=role_id))
        _audit.log(
            session,
            user_id=performed_by_id,
            action="rbac.assign_role_to_user",
            resource_type="user",
            resource_id=str(user_id),
            payload={"role_id": role_id},
        )

    def remove_role_from_user(
        self,
        session: Session,
        user_id: int,
        role_id: int,
        performed_by_id: int | None = None,
    ) -> bool:
        repo = UserRoleRepository(session)
        existing = repo.list_by_user_id(user_id)
        record = next((ur for ur in existing if ur.role_id == role_id), None)
        if record is None:
            return False
        repo.delete(record)
        _audit.log(
            session,
            user_id=performed_by_id,
            action="rbac.remove_role_from_user",
            resource_type="user",
            resource_id=str(user_id),
            payload={"role_id": role_id},
        )
        return True

    def get_roles_for_user(self, session: Session, user_id: int) -> list[Role]:
        user_roles = UserRoleRepository(session).list_by_user_id(user_id)
        role_repo = RoleRepository(session)
        roles = []
        for ur in user_roles:
            role = role_repo.get_by_id(ur.role_id)
            if role is not None:
                roles.append(role)
        return roles

    def get_permissions_for_user(self, session: Session, user_id: int) -> list[str]:
        user_roles = UserRoleRepository(session).list_by_user_id(user_id)
        rp_repo = RolePermissionRepository(session)
        perm_repo = PermissionRepository(session)
        codes: set[str] = set()
        for ur in user_roles:
            for rp in rp_repo.list_by_role_id(ur.role_id):
                perm = perm_repo.get_by_id(rp.permission_id)
                if perm is not None:
                    codes.add(perm.code)
        return sorted(codes)
