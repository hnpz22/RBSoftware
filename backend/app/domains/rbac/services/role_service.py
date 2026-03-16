from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from app.domains.rbac.models import Role
from app.domains.rbac.repositories import RoleRepository
from app.domains.rbac.schemas import RoleCreate


class RoleService:
    def create_role(self, session: Session, data: RoleCreate) -> Role:
        repo = RoleRepository(session)
        if repo.get_by_name(data.name) is not None:
            raise ValueError(f"Role already exists: {data.name}")
        return repo.create(data)

    def get_role(self, session: Session, public_id: UUID) -> Role | None:
        return RoleRepository(session).get_by_public_id(public_id)

    def list_roles(self, session: Session) -> list[Role]:
        return RoleRepository(session).list()

    def delete_role(self, session: Session, public_id: UUID) -> bool:
        repo = RoleRepository(session)
        role = repo.get_by_public_id(public_id)
        if role is None:
            return False
        repo.delete(role)
        return True
