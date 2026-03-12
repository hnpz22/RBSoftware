from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.auth.models import RefreshToken
from app.domains.auth.schemas import RefreshTokenCreate, RefreshTokenUpdate


class RefreshTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: RefreshTokenCreate) -> RefreshToken:
        refresh_token = RefreshToken.model_validate(payload)
        self.session.add(refresh_token)
        self.session.commit()
        self.session.refresh(refresh_token)
        return refresh_token

    def get_by_id(self, refresh_token_id: int) -> RefreshToken | None:
        return self.session.get(RefreshToken, refresh_token_id)

    def get_by_public_id(self, public_id: UUID) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.public_id == public_id)
        return self.session.exec(statement).first()

    def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.session.exec(statement).first()

    def list_by_user_id(self, user_id: int) -> list[RefreshToken]:
        statement = (
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .order_by(RefreshToken.id)
        )
        return list(self.session.exec(statement).all())

    def update(self, refresh_token: RefreshToken, payload: RefreshTokenUpdate) -> RefreshToken:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(refresh_token, field_name, value)

        self.session.add(refresh_token)
        self.session.commit()
        self.session.refresh(refresh_token)
        return refresh_token

    def delete(self, refresh_token: RefreshToken) -> None:
        self.session.delete(refresh_token)
        self.session.commit()
