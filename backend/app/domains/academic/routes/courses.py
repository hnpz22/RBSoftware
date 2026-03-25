from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session

from app.core.database import get_session
from app.domains.academic.repositories import (
    CourseRepository,
    CourseStudentRepository,
    UnitRepository,
)
from app.domains.academic.schemas import (
    AssignmentRead, CourseDetail, CourseRead, CourseUpdate,
    MaterialRead, SubmissionRead, UnitRead,
)
from app.domains.academic.services import AcademicService
from app.core.permissions import require_roles
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.auth.repositories import UserRepository
from app.domains.auth.schemas.user import UserRead

router = APIRouter(prefix="/academic", tags=["academic – courses"])
_svc = AcademicService()


class TeacherBody(BaseModel):
    teacher_id: UUID


class EnrollBody(BaseModel):
    user_id: UUID


class _AssignmentStudentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    title: str
    description: str | None
    due_date: datetime | None
    max_score: int
    is_published: bool
    my_submission: SubmissionRead | None = None


class _UnitStudentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    title: str
    description: str | None
    order_index: int
    is_published: bool
    materials: list[MaterialRead] = []
    assignments: list[_AssignmentStudentView] = []


@router.get("/my-courses", response_model=list[CourseRead])
def my_courses(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    teacher = _svc.get_my_courses_as_teacher(session, current_user.id)
    student = _svc.get_my_courses_as_student(session, current_user.id)
    seen: set[int] = set()
    combined = []
    for c in teacher + student:
        if c.id not in seen:
            seen.add(c.id)
            combined.append(c)
    return [CourseRead.model_validate(c) for c in combined]


@router.get("/courses/{course_id}", response_model=CourseDetail)
def get_course(
    course_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    course = CourseRepository(session).get_by_public_id(course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    teacher = UserRepository(session).get_by_id(course.teacher_id)
    students = CourseStudentRepository(session).get_students(course.id)
    units = UnitRepository(session).list_by_course(course.id)
    return CourseDetail(
        public_id=course.public_id,
        name=course.name,
        description=course.description,
        is_active=course.is_active,
        created_at=course.created_at,
        updated_at=course.updated_at,
        teacher=UserRead.model_validate(teacher),
        students=[UserRead.model_validate(s) for s in students],
        units=[UnitRead.model_validate(u) for u in units],
    )


@router.patch("/courses/{course_id}", response_model=CourseRead)
def update_course(
    course_id: UUID,
    data: CourseUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "DIRECTOR")),
):
    repo = CourseRepository(session)
    course = repo.get_by_public_id(course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    return CourseRead.model_validate(repo.update(course, data))


@router.post("/courses/{course_id}/teacher", status_code=status.HTTP_204_NO_CONTENT)
def assign_teacher(
    course_id: UUID,
    body: TeacherBody,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "DIRECTOR")),
):
    course = CourseRepository(session).get_by_public_id(course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    teacher = UserRepository(session).get_by_public_id(body.teacher_id)
    if teacher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher not found")
    try:
        _svc.assign_teacher(session, course.id, teacher.id, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("/courses/{course_id}/students", response_model=list[UserRead])
def list_students(
    course_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "DIRECTOR", "TEACHER")),
):
    course = CourseRepository(session).get_by_public_id(course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    return [
        UserRead.model_validate(s)
        for s in CourseStudentRepository(session).get_students(course.id)
    ]


@router.post(
    "/courses/{course_id}/students",
    status_code=status.HTTP_204_NO_CONTENT,
)
def enroll_student(
    course_id: UUID,
    body: EnrollBody,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "DIRECTOR")),
):
    course = CourseRepository(session).get_by_public_id(course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    user = UserRepository(session).get_by_public_id(body.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    try:
        _svc.enroll_student(session, course.id, user.id, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.delete(
    "/courses/{course_id}/students/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unenroll_student(
    course_id: UUID,
    user_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "DIRECTOR")),
):
    course = CourseRepository(session).get_by_public_id(course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    user = UserRepository(session).get_by_public_id(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if not CourseStudentRepository(session).unenroll(course.id, user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student is not enrolled")


@router.get("/courses/{course_id}/content", response_model=list[_UnitStudentView])
def get_course_content(
    course_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    course = CourseRepository(session).get_by_public_id(course_id)
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")
    try:
        _, units_data = _svc.get_course_content_for_student(
            session, course.id, current_user.id
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    result = []
    for unit, materials, assignment_pairs in units_data:
        result.append(
            _UnitStudentView(
                public_id=unit.public_id,
                title=unit.title,
                description=unit.description,
                order_index=unit.order_index,
                is_published=unit.is_published,
                materials=[MaterialRead.model_validate(m) for m in materials],
                assignments=[
                    _AssignmentStudentView(
                        public_id=a.public_id,
                        title=a.title,
                        description=a.description,
                        due_date=a.due_date,
                        max_score=a.max_score,
                        is_published=a.is_published,
                        my_submission=(
                            SubmissionRead.model_validate(sub) if sub else None
                        ),
                    )
                    for a, sub in assignment_pairs
                ],
            )
        )
    return result
