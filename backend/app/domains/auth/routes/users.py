from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session

from app.domains.audit.services import AuditService

from app.core.database import get_session
from app.core.permissions import require_roles
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
    _: User = Depends(require_roles("ADMIN")),
):
    return _svc.list_users(session)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID,
    data: UpdateUserRequest,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
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
    _: User = Depends(require_roles("ADMIN")),
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


@router.post("/import-csv", status_code=status.HTTP_200_OK)
def import_students_csv(
    file: UploadFile = File(...),
    school_id: str = Form(...),
    course_id: str = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    from app.domains.rbac.repositories.user_role_repository import UserRoleRepository

    roles = UserRoleRepository(session).get_role_names_for_user(current_user.id)
    if "ADMIN" not in [r.upper() for r in roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden importar usuarios",
        )

    csv_bytes = file.file.read()
    if not csv_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )

    try:
        return _svc.import_from_csv(
            session,
            csv_bytes=csv_bytes,
            school_public_id=school_id,
            course_public_id=course_id,
            requesting_user_id=current_user.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
