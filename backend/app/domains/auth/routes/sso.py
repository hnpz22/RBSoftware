from __future__ import annotations

import secrets
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.domains.audit.services import AuditService
from app.domains.auth.models import User
from app.domains.auth.repositories import UserRepository
from app.domains.auth.routes.auth import _set_auth_cookies
from app.domains.auth.schemas import UserCreate
from app.domains.auth.services.refresh_token_service import RefreshTokenService
from app.domains.rbac.repositories import RoleRepository, UserRoleRepository
from app.domains.rbac.schemas import UserRoleCreate

router = APIRouter(prefix="/auth/sso", tags=["auth"])

_audit = AuditService()

_GROUP_TO_ROLE: dict[str, str] = {
    "admin":         "ADMIN",
    "director":      "DIRECTOR",
    "trainer":       "TRAINER",
    "super_trainer": "TRAINER",
    "tallerista":    "TRAINER",
    "teacher":       "TEACHER",
    "student":       "STUDENT",
    "staff":         "TEACHER",
    "comercial":     "COMERCIAL",
    "produccion":    "OPERATIVO",
    "reparto":       "OPERATIVO",
}

_jwks_cache: list[dict] = []
_jwks_cache_at: float = 0.0


async def _get_jwks() -> list[dict]:
    global _jwks_cache, _jwks_cache_at
    if not _jwks_cache or time.monotonic() - _jwks_cache_at > 3600:
        async with httpx.AsyncClient() as client:
            res = await client.get(settings.jwt_jwks_url, timeout=10)
            res.raise_for_status()
        _jwks_cache = res.json().get("keys", [])
        _jwks_cache_at = time.monotonic()
    return _jwks_cache


def _validate_token(token: str, jwks: list[dict]) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        key = next((k for k in jwks if k.get("kid") == kid), jwks[0] if jwks else None)
        if not key:
            raise JWTError("no matching key in JWKS")
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False, "verify_at_hash": False},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {exc}",
        )
    return claims


def _sync_roles(
    session: Session,
    user_id: int,
    groups: list[str],
) -> list[str]:
    user_role_repo = UserRoleRepository(session)
    role_repo = RoleRepository(session)
    target = {_GROUP_TO_ROLE[g] for g in groups if g in _GROUP_TO_ROLE}
    current = set(user_role_repo.get_role_names_for_user(user_id))
    for role_name in target - current:
        role = role_repo.get_by_name(role_name)
        if role:
            user_role_repo.create(UserRoleCreate(user_id=user_id, role_id=role.id))
    return list(current | target)


class SSOTokenRequest(BaseModel):
    token: str


@router.post("/login", response_model=dict)
async def sso_login(
    request: Request,
    body: SSOTokenRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> dict:
    ip = request.client.host if request.client else None

    try:
        jwks = await _get_jwks()
        claims = _validate_token(body.token, jwks)
    except HTTPException:
        _jwks_cache.clear()  # force refetch on next attempt
        raise

    email = (claims.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token sin email")

    user_repo = UserRepository(session)
    user: User | None = user_repo.get_by_email(email)

    if user is None:
        # JIT provision: create LMS user from portal JWT claims
        name = (claims.get("name") or email).strip()
        parts = name.split(" ", 1)
        first, last = parts[0], parts[1] if len(parts) > 1 else ""
        user = user_repo.create(UserCreate(
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            first_name=first,
            last_name=last,
        ))

    if not user.is_active:
        _audit.log(session, user_id=user.id, action="auth.sso_blocked",
                   resource_type="user", resource_id=email, ip=ip)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta inactiva")

    groups: list[str] = claims.get("groups") or []
    role_names = _sync_roles(session, user.id, groups)

    raw_refresh, _ = RefreshTokenService().create_token(session, user.id)
    access_token = create_access_token({"sub": str(user.public_id)})
    _set_auth_cookies(response, access_token, raw_refresh, role_names)

    _audit.log(session, user_id=user.id, action="auth.sso_login",
               resource_type="user", resource_id=str(user.public_id), ip=ip)

    return {"ok": True}
