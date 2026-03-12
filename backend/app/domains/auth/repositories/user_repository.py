from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.auth.models import User
from app.domains.auth.schemas import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: UserCreate) -> User:
        user = User.model_validate(payload)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_public_id(self, public_id: UUID) -> User | None:
        statement = select(User).where(User.public_id == public_id)
        return self.session.exec(statement).first()

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def list(self) -> list[User]:
        statement = select(User).order_by(User.id)
        return list(self.session.exec(statement).all())

    def update(self, user: User, payload: UserUpdate) -> User:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(user, field_name, value)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.session.delete(user)
        self.session.commit()
