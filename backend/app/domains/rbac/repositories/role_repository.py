from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.rbac.models import Role
from app.domains.rbac.schemas import RoleCreate, RoleUpdate


class RoleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: RoleCreate) -> Role:
        role = Role.model_validate(payload)
        self.session.add(role)
        self.session.commit()
        self.session.refresh(role)
        return role

    def get_by_id(self, role_id: int) -> Role | None:
        return self.session.get(Role, role_id)

    def get_by_public_id(self, public_id: UUID) -> Role | None:
        statement = select(Role).where(Role.public_id == public_id)
        return self.session.exec(statement).first()

    def get_by_name(self, name: str) -> Role | None:
        statement = select(Role).where(Role.name == name)
        return self.session.exec(statement).first()

    def list(self) -> list[Role]:
        statement = select(Role).order_by(Role.id)
        return list(self.session.exec(statement).all())

    def update(self, role: Role, payload: RoleUpdate) -> Role:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(role, field_name, value)

        self.session.add(role)
        self.session.commit()
        self.session.refresh(role)
        return role

    def delete(self, role: Role) -> None:
        self.session.delete(role)
        self.session.commit()
