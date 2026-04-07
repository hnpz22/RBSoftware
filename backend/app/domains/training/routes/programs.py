from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.permissions import require_roles
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.rbac.repositories import UserRoleRepository
from app.domains.training.repositories.enrollment_repository import EnrollmentRepository
from app.domains.training.repositories.program_repository import ProgramRepository
from app.domains.training.schemas.composite import ProgramDetail, ModuleWithContent
from app.domains.training.schemas.training_module import ModuleRead
from app.domains.training.schemas.training_program import (
    ProgramCreate,
    ProgramRead,
    ProgramUpdate,
)
from app.domains.training.services import TrainingService

router = APIRouter(prefix="/training", tags=["training – programs"])
_svc = TrainingService()


@router.get("/programs", response_model=list[ProgramRead])
def list_programs(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    role_names = UserRoleRepository(session).get_role_names_for_user(current_user.id)
    if "ADMIN" in role_names:
        programs = ProgramRepository(session).list_active()
    elif "TRAINER" in role_names:
        programs = ProgramRepository(session).list_by_creator(current_user.id)
    else:
        enrollments = EnrollmentRepository(session).list_by_user(current_user.id)
        program_ids = [e.program_id for e in enrollments]
        programs = [
            p
            for p in ProgramRepository(session).list_published()
            if p.id in program_ids
        ]
    return [ProgramRead.model_validate(p) for p in programs]


@router.post(
    "/programs",
    response_model=ProgramRead,
    status_code=status.HTTP_201_CREATED,
)
def create_program(
    data: ProgramCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER")),
):
    try:
        program = _svc.create_program(session, data, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    return ProgramRead.model_validate(program)


@router.get("/programs/{program_id}", response_model=ProgramRead)
def get_program(
    program_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    program = ProgramRepository(session).get_by_public_id(program_id)
    if program is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programa no encontrado")
    return ProgramRead.model_validate(program)


@router.patch("/programs/{program_id}", response_model=ProgramRead)
def update_program(
    program_id: UUID,
    data: ProgramUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER")),
):
    try:
        program = _svc.update_program(session, program_id, data, current_user.id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    return ProgramRead.model_validate(program)


@router.post("/programs/{program_id}/publish", status_code=status.HTTP_204_NO_CONTENT)
def publish_program(
    program_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER")),
):
    try:
        _svc.publish_program(session, program_id, current_user.id, publish=True)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("/programs/{program_id}/progress")
def get_program_progress(
    program_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER")),
):
    program = ProgramRepository(session).get_by_public_id(program_id)
    if program is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programa no encontrado")
    enrollments = EnrollmentRepository(session).list_by_program(program.id)
    results = []
    for enrollment in enrollments:
        try:
            completion = _svc.check_completion(session, enrollment.public_id)
        except LookupError:
            continue
        from app.domains.auth.repositories import UserRepository

        user = UserRepository(session).get_by_id(enrollment.user_id)
        results.append(
            {
                "user": {
                    "public_id": str(user.public_id) if user else None,
                    "first_name": user.first_name if user else None,
                    "last_name": user.last_name if user else None,
                    "email": user.email if user else None,
                },
                "enrollment_public_id": str(enrollment.public_id),
                "status": enrollment.status,
                **completion,
            }
        )
    return results
