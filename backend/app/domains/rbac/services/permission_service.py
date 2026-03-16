from __future__ import annotations

from sqlmodel import Session

from app.domains.rbac.models import Permission
from app.domains.rbac.repositories import PermissionRepository
from app.domains.rbac.schemas import PermissionCreate


class PermissionService:
    def create_permission(self, session: Session, data: PermissionCreate) -> Permission:
        repo = PermissionRepository(session)
        if repo.get_by_code(data.code) is not None:
            raise ValueError(f"Permission already exists: {data.code}")
        return repo.create(data)

    def list_permissions(self, session: Session) -> list[Permission]:
        return PermissionRepository(session).list()
