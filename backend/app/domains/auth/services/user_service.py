from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from app.core.security import hash_password, verify_password
from app.domains.auth.models import User
from app.domains.auth.repositories import UserRepository
from app.domains.auth.schemas import UserCreate, UserUpdate
from app.domains.auth.services.refresh_token_service import RefreshTokenService


class UserService:
    def register(
        self,
        session: Session,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: str | None = None,
        position: str | None = None,
    ) -> User:
        repo = UserRepository(session)
        if repo.get_by_email(email) is not None:
            raise ValueError(f"Email already registered: {email}")
        return repo.create(
            UserCreate(
                email=email,
                password_hash=hash_password(password),
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                position=position,
            )
        )

    def authenticate(self, session: Session, email: str, password: str) -> User | None:
        repo = UserRepository(session)
        user = repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    def get_by_id(self, session: Session, user_id: int) -> User | None:
        return UserRepository(session).get_by_id(user_id)

    def get_by_public_id(self, session: Session, public_id: UUID) -> User | None:
        return UserRepository(session).get_by_public_id(public_id)

    def list_users(self, session: Session) -> list[User]:
        return UserRepository(session).list()

    def update_user(
        self,
        session: Session,
        public_id: UUID,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        position: str | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        repo = UserRepository(session)
        user = repo.get_by_public_id(public_id)
        if user is None:
            return None
        return repo.update(
            user,
            UserUpdate(
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                position=position,
                is_active=is_active,
            ),
        )

    def change_password(
        self,
        session: Session,
        public_id: UUID,
        new_password: str,
        current_user_public_id: UUID,
    ) -> User:
        repo = UserRepository(session)
        user = repo.get_by_public_id(public_id)
        if user is None:
            raise LookupError("User not found")
        if user.public_id != current_user_public_id:
            raise PermissionError("Cannot change another user's password")
        updated = repo.update(user, UserUpdate(password_hash=hash_password(new_password)))
        RefreshTokenService().revoke_all_for_user(session, user.id)
        return updated
