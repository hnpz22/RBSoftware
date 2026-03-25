from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.core.database import get_session
from app.domains.academic.repositories import CourseRepository
from app.domains.academic.services import AcademicService
from app.core.permissions import require_roles
from app.domains.auth.models import User
from app.domains.auth.repositories import UserRepository

router = APIRouter(prefix="/academic", tags=["academic – students"])
_svc = AcademicService()


class TransferBody(BaseModel):
    from_course_id: UUID
    to_course_id: UUID


@router.post(
    "/students/{student_id}/transfer",
    status_code=status.HTTP_204_NO_CONTENT,
)
def transfer_student(
    student_id: UUID,
    body: TransferBody,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "DIRECTOR")),
):
    student = UserRepository(session).get_by_public_id(student_id)
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    from_course = CourseRepository(session).get_by_public_id(body.from_course_id)
    if from_course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source course not found")
    to_course = CourseRepository(session).get_by_public_id(body.to_course_id)
    if to_course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Target course not found")
    try:
        _svc.transfer_student(
            session, student.id, from_course.id, to_course.id, current_user.id
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
