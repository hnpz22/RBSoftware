"""Endpoints consumidos por el portal admin.
Autenticado con service token compartido (no requiere usuario)."""
from __future__ import annotations

import secrets
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.core.config import settings
from app.core.database import get_session
from app.core.security import hash_password
from app.domains.auth.models import User
from app.domains.auth.schemas import UserCreate
from app.domains.rbac.models import Role
from app.domains.rbac.repositories import RoleRepository, UserRoleRepository

router = APIRouter(prefix="/admin", tags=["portal-admin"])


def _verify_service_token(x_service_token: str | None = Header(default=None)) -> None:
    if not x_service_token or x_service_token != settings.portal_service_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing service token",
        )


@router.get("/roles")
def list_roles(
    session: Session = Depends(get_session),
    _: None = Depends(_verify_service_token),
) -> dict:
    """Devuelve la lista de roles que esta plataforma ofrece."""
    rows = session.exec(select(Role).order_by(Role.name)).all()
    return {
        "roles": [
            {"key": r.name, "label": r.description or r.name}
            for r in rows
        ]
    }


class UsersSyncRequest(BaseModel):
    action: Literal["activate", "deactivate", "upsert"]
    emails: list[str] = []
    # upsert only
    email: str | None = None
    name: str | None = None
    role: str | None = None


@router.post("/users-sync")
def users_sync(
    body: UsersSyncRequest,
    session: Session = Depends(get_session),
    _: None = Depends(_verify_service_token),
) -> dict:
    """Sincroniza usuarios desde el portal:
    - activate/deactivate: activa o desactiva por lista de emails.
    - upsert: pre-crea el usuario si no existe y sincroniza su rol.
    """
    if body.action == "upsert":
        return _handle_upsert(session, body)
    return _handle_toggle(session, body)


def _handle_toggle(session: Session, body: UsersSyncRequest) -> dict:
    emails = [e.lower().strip() for e in body.emails if e]
    if not emails:
        return {"ok": True, "matched": 0}
    is_active = body.action == "activate"
    users = session.exec(select(User).where(col(User.email).in_(emails))).all()
    for user in users:
        user.is_active = is_active
        session.add(user)
    session.commit()
    return {"ok": True, "action": body.action, "matched": len(users)}


def _handle_upsert(session: Session, body: UsersSyncRequest) -> dict:
    email = (body.email or "").lower().strip()
    if not email:
        raise HTTPException(status_code=422, detail="email requerido para upsert")

    user = session.exec(select(User).where(User.email == email)).first()
    created = False
    if user is None:
        name = (body.name or email).strip()
        parts = name.split(" ", 1)
        first, last = parts[0], parts[1] if len(parts) > 1 else ""
        user = User.model_validate(UserCreate(
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            first_name=first,
            last_name=last,
        ))
        session.add(user)
        session.commit()
        session.refresh(user)
        created = True

    if body.role:
        role = RoleRepository(session).get_by_name(body.role)
        if role:
            UserRoleRepository(session).set_user_roles(user.id, [role.id])

    return {"ok": True, "action": "upsert", "created": created, "matched": 1}
