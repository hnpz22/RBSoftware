from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.domains.academic.repositories import CourseRepository, UnitRepository
from app.domains.academic.schemas import UnitCreate, UnitRead, UnitUpdate
from app.domains.academic.services import AcademicService
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User

router = APIRouter(prefix="/academic", tags=["academic – units"])
_svc = AcademicService()


@router.get("/courses/{course_id}/units", response_model=list[UnitRead])
def list_units(
    course_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    course = CourseRepository(session).get_by_public_id(course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    return [
        UnitRead.model_validate(u)
        for u in UnitRepository(session).list_by_course(course.id)
    ]


@router.post(
    "/courses/{course_id}/units",
    response_model=UnitRead,
    status_code=status.HTTP_201_CREATED,
)
def create_unit(
    course_id: UUID,
    data: UnitCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    course = CourseRepository(session).get_by_public_id(course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    try:
        unit = _svc.create_unit(session, course.id, data, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    return UnitRead.model_validate(unit)


@router.patch("/units/{unit_id}", response_model=UnitRead)
def update_unit(
    unit_id: UUID,
    data: UnitUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    repo = UnitRepository(session)
    unit = repo.get_by_public_id(unit_id)
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unit not found")
    course = CourseRepository(session).get_by_id(unit.course_id)
    if course.teacher_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the teacher")
    return UnitRead.model_validate(repo.update(unit, data))


@router.post("/units/{unit_id}/publish", status_code=status.HTTP_204_NO_CONTENT)
def publish_unit(
    unit_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    unit = UnitRepository(session).get_by_public_id(unit_id)
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unit not found")
    try:
        _svc.publish_unit(session, unit.id, current_user.id, publish=True)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))


@router.delete("/units/{unit_id}/publish", status_code=status.HTTP_204_NO_CONTENT)
def unpublish_unit(
    unit_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    unit = UnitRepository(session).get_by_public_id(unit_id)
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unit not found")
    try:
        _svc.publish_unit(session, unit.id, current_user.id, publish=False)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
