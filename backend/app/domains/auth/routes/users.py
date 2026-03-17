from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session

from app.domains.audit.services import AuditService

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.auth.schemas import UserRead
from app.domains.auth.services.user_service import UserService

router = APIRouter(prefix="/auth/users", tags=["auth"])

_svc = UserService()
_audit = AuditService()


class CreateUserRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    position: str | None = None


class UpdateUserRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    position: str | None = None
    is_active: bool | None = None


class ChangePasswordRequest(BaseModel):
    new_password: str


@router.get("", response_model=list[UserRead])
def list_users(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[UserRead]:
    users = _svc.list_users(session)
    return [UserRead.model_validate(u) for u in users]


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID,
    data: UpdateUserRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> UserRead:
    user = _svc.update_user(
        session,
        public_id=user_id,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        position=data.position,
        is_active=data.is_active,
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: CreateUserRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> UserRead:
    try:
        user = _svc.register(
            session,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            position=data.position,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return UserRead.model_validate(user)


@router.patch("/{user_id}/password", status_code=status.HTTP_200_OK)
def change_password(
    user_id: UUID,
    data: ChangePasswordRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    try:
        _svc.change_password(
            session,
            public_id=user_id,
            new_password=data.new_password,
            current_user_public_id=current_user.public_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    _audit.log(
        session,
        user_id=current_user.id,
        action="user.password_changed",
        resource_type="user",
        resource_id=str(user_id),
        ip=request.client.host if request.client else None,
    )
    return {"message": "Password updated"}
