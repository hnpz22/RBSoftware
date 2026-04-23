from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session

from app.core.database import get_session
from app.core.permissions import require_roles
from app.core.storage import storage_service
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.training.repositories.lesson_repository import LessonRepository
from app.domains.training.repositories.module_repository import ModuleRepository
from app.domains.training.schemas.training_lesson import (
    LessonCreate,
    LessonRead,
    LessonUpdate,
)
from app.domains.training.services import TrainingService

router = APIRouter(prefix="/training", tags=["training – lessons"])
_svc = TrainingService()


@router.get("/modules/{module_id}/lessons", response_model=list[LessonRead])
def list_lessons(
    module_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    module = ModuleRepository(session).get_by_public_id(module_id)
    if module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Módulo no encontrado")
    return [
        LessonRead.model_validate(l)
        for l in LessonRepository(session).list_by_module(module.id)
    ]


@router.post(
    "/modules/{module_id}/lessons",
    response_model=LessonRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson(
    module_id: UUID,
    title: str = Form(...),
    type: str = Form(...),
    content: str | None = Form(default=None),
    duration_minutes: int | None = Form(default=None),
    order_index: int = Form(default=0),
    file: UploadFile | None = File(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TRAINER")),
):
    file_bytes = None
    content_type = None
    if file is not None:
        file_bytes = await file.read()
        if len(file_bytes) > 100 * 1024 * 1024:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "El archivo excede 100 MB"
            )
        content_type = file.content_type
    data = LessonCreate(
        title=title,
        type=type,
        content=content,
        duration_minutes=duration_minutes,
        order_index=order_index,
    )
    try:
        lesson = _svc.create_lesson(
            session, module_id, data, file_bytes, content_type, current_user.id
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return LessonRead.model_validate(lesson)


@router.patch("/lessons/{lesson_id}", response_model=LessonRead)
def update_lesson(
    lesson_id: UUID,
    data: LessonUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "TRAINER")),
):
    lesson = LessonRepository(session).get_by_public_id(lesson_id)
    if lesson is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lección no encontrada")
    updated = LessonRepository(session).update(lesson, data)
    return LessonRead.model_validate(updated)


class PublishBody(BaseModel):
    publish: bool


@router.post("/lessons/{lesson_id}/publish", response_model=LessonRead)
def publish_lesson(
    lesson_id: UUID,
    body: PublishBody,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "TRAINER")),
):
    lesson = LessonRepository(session).get_by_public_id(lesson_id)
    if lesson is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lección no encontrada")
    updated = LessonRepository(session).update(
        lesson, LessonUpdate(is_published=body.publish)
    )
    return LessonRead.model_validate(updated)


@router.post("/lessons/{lesson_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
def complete_lesson(
    lesson_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("TEACHER")),
):
    try:
        _svc.mark_lesson_completed(session, lesson_id, current_user.id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))


@router.get("/lessons/{lesson_id}/view")
def view_lesson(
    lesson_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    lesson = LessonRepository(session).get_by_public_id(lesson_id)
    if lesson is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lección no encontrada")
    if not lesson.file_key:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta lección no tiene archivo")
    url = storage_service.generate_presigned_url(lesson.file_key, inline=True)
    return {"url": url}
