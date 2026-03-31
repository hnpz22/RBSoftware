from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.core.database import get_session
from app.domains.academic.repositories import GradeRepository, SchoolRepository
from app.domains.academic.schemas import (
    GradeCreate, GradeRead, SchoolCreate, SchoolRead, SchoolUpdate,
)
from app.domains.academic.services import AcademicService
from app.core.permissions import require_roles
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.auth.repositories import UserRepository
from app.domains.auth.schemas import UserRead

router = APIRouter(prefix="/academic", tags=["academic – schools"])
_svc = AcademicService()


class TeacherBody(BaseModel):
    user_id: UUID


@router.get("/schools", response_model=list[SchoolRead])
def list_schools(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
):
    return [SchoolRead.model_validate(s) for s in SchoolRepository(session).list()]


@router.post("/schools", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(
    data: SchoolCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
):
    return SchoolRead.model_validate(_svc.create_school(session, data))


@router.get("/schools/{school_id}", response_model=SchoolRead)
def get_school(
    school_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
):
    school = SchoolRepository(session).get_by_public_id(school_id)
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    return SchoolRead.model_validate(school)


@router.patch("/schools/{school_id}", response_model=SchoolRead)
def update_school(
    school_id: UUID,
    data: SchoolUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
):
    repo = SchoolRepository(session)
    school = repo.get_by_public_id(school_id)
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    return SchoolRead.model_validate(repo.update(school, data))


@router.get("/schools/{school_id}/grades", response_model=list[GradeRead])
def list_grades(
    school_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
):
    school = SchoolRepository(session).get_by_public_id(school_id)
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    return [
        GradeRead.model_validate(g)
        for g in GradeRepository(session).list_by_school(school.id)
    ]


@router.post(
    "/schools/{school_id}/grades",
    response_model=GradeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_grade(
    school_id: UUID,
    data: GradeCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN")),
):
    school = SchoolRepository(session).get_by_public_id(school_id)
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    try:
        grade = _svc.create_grade(session, school.id, data)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    return GradeRead.model_validate(grade)


@router.get("/schools/{school_id}/teachers", response_model=list[UserRead])
def list_school_teachers(
    school_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "DIRECTOR")),
):
    school = SchoolRepository(session).get_by_public_id(school_id)
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    try:
        return _svc.get_teachers_for_school(session, school.id, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))


@router.post(
    "/schools/{school_id}/teachers",
    status_code=status.HTTP_201_CREATED,
)
def add_school_teacher(
    school_id: UUID,
    body: TeacherBody,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN")),
):
    school = SchoolRepository(session).get_by_public_id(school_id)
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    user = UserRepository(session).get_by_public_id(body.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    try:
        _svc.add_teacher_to_school(session, school.id, user.id, current_user.id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return {"detail": "Teacher added"}


@router.delete(
    "/schools/{school_id}/teachers/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_school_teacher(
    school_id: UUID,
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN")),
):
    school = SchoolRepository(session).get_by_public_id(school_id)
    if school is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    user = UserRepository(session).get_by_public_id(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    try:
        _svc.remove_teacher_from_school(session, school.id, user.id, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
