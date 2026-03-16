from __future__ import annotations

from sqlmodel import Session, select

from app.domains.rbac.models import UserRole
from app.domains.rbac.schemas import UserRoleCreate, UserRoleUpdate


class UserRoleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: UserRoleCreate) -> UserRole:
        user_role = UserRole.model_validate(payload)
        self.session.add(user_role)
        self.session.commit()
        self.session.refresh(user_role)
        return user_role

    def get_by_id(self, user_role_id: int) -> UserRole | None:
        return self.session.get(UserRole, user_role_id)

    def list(self) -> list[UserRole]:
        statement = select(UserRole).order_by(UserRole.id)
        return list(self.session.exec(statement).all())

    def list_by_user_id(self, user_id: int) -> list[UserRole]:
        statement = select(UserRole).where(UserRole.user_id == user_id)
        return list(self.session.exec(statement).all())

    def update(self, user_role: UserRole, payload: UserRoleUpdate) -> UserRole:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(user_role, field_name, value)

        self.session.add(user_role)
        self.session.commit()
        self.session.refresh(user_role)
        return user_role

    def delete(self, user_role: UserRole) -> None:
        self.session.delete(user_role)
        self.session.commit()
