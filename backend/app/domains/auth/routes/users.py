from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.auth.schemas import UserRead
from app.domains.auth.services.user_service import UserService

router = APIRouter(prefix="/auth/users", tags=["auth"])

_svc = UserService()


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
