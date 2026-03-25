from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.rbac.repositories import UserRoleRepository


def require_roles(*allowed_roles: str):
    """
    Dependency factory que verifica que el usuario autenticado
    tenga AL MENOS UNO de los roles especificados.

    ADMIN siempre tiene acceso, independientemente de los roles listados.

    Uso:
        @router.get("/ruta")
        def mi_endpoint(
            current_user: User = Depends(require_roles("ADMIN", "DIRECTOR"))
        ):
            ...
    """

    def dependency(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session),
    ) -> User:
        user_roles = UserRoleRepository(session).get_role_names_for_user(
            current_user.id
        )
        if "ADMIN" in user_roles:
            return current_user
        if any(role in user_roles for role in allowed_roles):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Se requiere uno de estos roles: {', '.join(allowed_roles)}",
        )

    return dependency
