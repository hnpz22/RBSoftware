from __future__ import annotations

from sqlmodel import Session, select

from app.domains.academic.models.lms_course import LmsCourse
from app.domains.academic.models.lms_course_student import LmsCourseStudent
from app.domains.auth.models import User


class CourseStudentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def enroll(
        self,
        course_id: int,
        user_id: int,
        from_course_id: int | None = None,
    ) -> LmsCourseStudent:
        existing = self._get_record(course_id, user_id)
        if existing is not None:
            if not existing.is_active:
                existing.is_active = True
                existing.transferred_from_course_id = from_course_id
                self.session.add(existing)
                self.session.commit()
                self.session.refresh(existing)
            return existing
        record = LmsCourseStudent(
            course_id=course_id,
            user_id=user_id,
            transferred_from_course_id=from_course_id,
            is_active=True,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def unenroll(self, course_id: int, user_id: int) -> bool:
        record = self._get_record(course_id, user_id)
        if record is None or not record.is_active:
            return False
        record.is_active = False
        self.session.add(record)
        self.session.commit()
        return True

    def transfer(
        self, student_id: int, from_course_id: int, to_course_id: int
    ) -> LmsCourseStudent:
        self.unenroll(from_course_id, student_id)
        return self.enroll(to_course_id, student_id, from_course_id=from_course_id)

    def get_students(self, course_id: int) -> list[User]:
        stmt = (
            select(User)
            .join(LmsCourseStudent, LmsCourseStudent.user_id == User.id)
            .where(
                LmsCourseStudent.course_id == course_id,
                LmsCourseStudent.is_active.is_(True),
            )
            .order_by(User.last_name, User.first_name)
        )
        return list(self.session.exec(stmt).all())

    def get_courses_for_student(self, user_id: int) -> list[LmsCourse]:
        stmt = (
            select(LmsCourse)
            .join(LmsCourseStudent, LmsCourseStudent.course_id == LmsCourse.id)
            .where(
                LmsCourseStudent.user_id == user_id,
                LmsCourseStudent.is_active.is_(True),
                LmsCourse.is_active.is_(True),
            )
            .order_by(LmsCourse.name)
        )
        return list(self.session.exec(stmt).all())

    def is_enrolled(self, course_id: int, user_id: int) -> bool:
        record = self._get_record(course_id, user_id)
        return record is not None and record.is_active

    def _get_record(self, course_id: int, user_id: int) -> LmsCourseStudent | None:
        stmt = select(LmsCourseStudent).where(
            LmsCourseStudent.course_id == course_id,
            LmsCourseStudent.user_id == user_id,
        )
        return self.session.exec(stmt).first()
