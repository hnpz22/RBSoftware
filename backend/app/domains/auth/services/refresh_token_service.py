from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from sqlmodel import Session

from app.core.config import settings
from app.core.security import create_refresh_token
from app.domains.auth.models import RefreshToken
from app.domains.auth.repositories import RefreshTokenRepository
from app.domains.auth.schemas import RefreshTokenCreate, RefreshTokenUpdate


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class RefreshTokenService:
    def create_token(self, session: Session, user_id: int) -> tuple[str, RefreshToken]:
        raw = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        record = RefreshTokenRepository(session).create(
            RefreshTokenCreate(user_id=user_id, token_hash=_hash(raw), expires_at=expires_at)
        )
        return raw, record

    def validate_and_rotate(
        self, session: Session, raw_token: str
    ) -> tuple[str, RefreshToken] | None:
        repo = RefreshTokenRepository(session)
        record = repo.get_by_token_hash(_hash(raw_token))
        if record is None:
            return None
        now = datetime.now(timezone.utc)
        if record.revoked_at is not None or record.expires_at.replace(tzinfo=timezone.utc) < now:
            return None
        repo.update(record, RefreshTokenUpdate(revoked_at=now))
        return self.create_token(session, record.user_id)

    def revoke(self, session: Session, raw_token: str) -> bool:
        repo = RefreshTokenRepository(session)
        record = repo.get_by_token_hash(_hash(raw_token))
        if record is None or record.revoked_at is not None:
            return False
        repo.update(record, RefreshTokenUpdate(revoked_at=datetime.now(timezone.utc)))
        return True
