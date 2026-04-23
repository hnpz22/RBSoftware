from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.core.database import get_session
from app.core.permissions import require_roles
from app.domains.auth.models import User
from app.domains.auth.repositories import UserRepository
from app.domains.training.repositories.enrollment_repository import EnrollmentRepository
from app.domains.training.repositories.program_repository import ProgramRepository
from app.domains.training.schemas.composite import TeacherProgramProgress
from app.domains.training.schemas.training_enrollment import EnrollmentRead
from app.domains.training.services import TrainingService

router = APIRouter(prefix="/training", tags=["training – enrollments"])
_svc = TrainingService()


class EnrollBody(BaseModel):
    user_id: UUID


@router.get(
    "/programs/{program_id}/enrollments", response_model=list[EnrollmentRead]
)
def list_enrollments(
    program_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    program = ProgramRepository(session).get_by_public_id(program_id)
    if program is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programa no encontrado")
    return [
        EnrollmentRead.model_validate(e)
        for e in EnrollmentRepository(session).list_by_program(program.id)
    ]


@router.post(
    "/programs/{program_id}/enroll",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
def enroll_teacher(
    program_id: UUID,
    body: EnrollBody,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    user = UserRepository(session).get_by_public_id(body.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    try:
        enrollment = _svc.enroll_teacher(
            session, program_id, user.id, current_user.id
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return EnrollmentRead.model_validate(enrollment)


@router.get(
    "/programs/{program_id}/my-completed-lessons",
    response_model=list[UUID],
)
def get_my_completed_lessons(
    program_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("TEACHER")),
):
    try:
        return _svc.get_my_completed_lessons(session, program_id, current_user.id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))


@router.get(
    "/my-programs",
    response_model=list[TeacherProgramProgress],
)
def get_my_programs(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("TEACHER")),
):
    return _svc.get_my_programs(session, current_user.id)
