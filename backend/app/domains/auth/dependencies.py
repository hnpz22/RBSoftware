from __future__ import annotations

from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import decode_access_token
from app.domains.auth.models import User
from app.domains.auth.services.user_service import UserService


def get_current_user_optional(
    access_token: str | None = Cookie(default=None),
    session: Session = Depends(get_session),
) -> User | None:
    """Like get_current_user but returns None instead of raising 401."""
    if access_token is None:
        return None
    payload = decode_access_token(access_token)
    if payload is None:
        return None
    sub: str | None = payload.get("sub")
    if sub is None:
        return None
    try:
        public_id = UUID(sub)
    except ValueError:
        return None
    user = UserService().get_by_public_id(session, public_id)
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(
    access_token: str | None = Cookie(default=None),
    session: Session = Depends(get_session),
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    if access_token is None:
        raise exc

    payload = decode_access_token(access_token)
    if payload is None:
        raise exc

    sub: str | None = payload.get("sub")
    if sub is None:
        raise exc

    try:
        public_id = UUID(sub)
    except ValueError:
        raise exc

    user = UserService().get_by_public_id(session, public_id)
    if user is None or not user.is_active:
        raise exc

    return user
