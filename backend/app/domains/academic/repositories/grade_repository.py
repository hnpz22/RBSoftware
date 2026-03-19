from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.academic.models.lms_course import LmsCourse
from app.domains.academic.models.lms_grade import LmsGrade
from app.domains.academic.models.lms_grade_director import LmsGradeDirector
from app.domains.academic.schemas.lms_grade import GradeCreate, GradeUpdate
from app.domains.auth.models import User


class GradeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, school_id: int, payload: GradeCreate) -> LmsGrade:
        grade = LmsGrade.model_validate(payload, update={"school_id": school_id})
        self.session.add(grade)
        self.session.commit()
        self.session.refresh(grade)
        return grade

    def get_by_id(self, grade_id: int) -> LmsGrade | None:
        return self.session.get(LmsGrade, grade_id)

    def get_by_public_id(self, public_id: UUID) -> LmsGrade | None:
        stmt = select(LmsGrade).where(LmsGrade.public_id == public_id)
        return self.session.exec(stmt).first()

    def list_by_school(self, school_id: int) -> list[LmsGrade]:
        stmt = (
            select(LmsGrade)
            .where(LmsGrade.school_id == school_id)
            .order_by(LmsGrade.name)
        )
        return list(self.session.exec(stmt).all())

    def get_with_courses(
        self, grade_id: int
    ) -> tuple[LmsGrade, list[LmsCourse], User | None]:
        grade = self.get_by_id(grade_id)
        if grade is None:
            return None  # type: ignore[return-value]

        courses_stmt = (
            select(LmsCourse)
            .where(LmsCourse.grade_id == grade_id, LmsCourse.is_active.is_(True))
            .order_by(LmsCourse.name)
        )
        courses = list(self.session.exec(courses_stmt).all())

        director_stmt = (
            select(User)
            .join(LmsGradeDirector, LmsGradeDirector.user_id == User.id)
            .where(
                LmsGradeDirector.grade_id == grade_id,
                LmsGradeDirector.is_active.is_(True),
            )
        )
        director = self.session.exec(director_stmt).first()

        return grade, courses, director

    def update(self, grade: LmsGrade, payload: GradeUpdate) -> LmsGrade:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(grade, field_name, value)
        self.session.add(grade)
        self.session.commit()
        self.session.refresh(grade)
        return grade

    def delete(self, grade: LmsGrade) -> None:
        self.session.delete(grade)
        self.session.commit()
