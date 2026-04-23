from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.permissions import require_roles
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.training.repositories.module_repository import ModuleRepository
from app.domains.training.repositories.program_repository import ProgramRepository
from app.domains.training.schemas.training_module import (
    ModuleCreate,
    ModuleRead,
    ModuleUpdate,
)
from app.domains.training.services import TrainingService

router = APIRouter(prefix="/training", tags=["training – modules"])
_svc = TrainingService()


@router.get("/programs/{program_id}/modules", response_model=list[ModuleRead])
def list_modules(
    program_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    program = ProgramRepository(session).get_by_public_id(program_id)
    if program is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programa no encontrado")
    return [
        ModuleRead.model_validate(m)
        for m in ModuleRepository(session).list_by_program(program.id)
    ]


@router.post(
    "/programs/{program_id}/modules",
    response_model=ModuleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_module(
    program_id: UUID,
    data: ModuleCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    try:
        module = _svc.create_module(session, program_id, data, current_user.id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    return ModuleRead.model_validate(module)


@router.patch("/modules/{module_id}", response_model=ModuleRead)
def update_module(
    module_id: UUID,
    data: ModuleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    module = ModuleRepository(session).get_by_public_id(module_id)
    if module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Módulo no encontrado")
    updates = data.model_dump(exclude_unset=True)
    for field_name, value in updates.items():
        setattr(module, field_name, value)
    session.add(module)
    session.commit()
    session.refresh(module)
    return ModuleRead.model_validate(module)


@router.post("/modules/{module_id}/publish", status_code=status.HTTP_204_NO_CONTENT)
def publish_module(
    module_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "TRAINER", "SUPER_TRAINER")),
):
    module = ModuleRepository(session).get_by_public_id(module_id)
    if module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Módulo no encontrado")
    module.is_published = True
    session.add(module)
    session.commit()
