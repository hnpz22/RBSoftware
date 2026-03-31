from __future__ import annotations

from sqlmodel import Session, select

from app.domains.academic.models.school_teacher import SchoolTeacher
from app.domains.auth.models import User


class SchoolTeacherRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, school_id: int, user_id: int) -> SchoolTeacher:
        existing = self._get_record(school_id, user_id)
        if existing is not None:
            return existing
        record = SchoolTeacher(school_id=school_id, user_id=user_id)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def remove(self, school_id: int, user_id: int) -> bool:
        record = self._get_record(school_id, user_id)
        if record is None:
            return False
        self.session.delete(record)
        self.session.commit()
        return True

    def get_teacher_ids(self, school_id: int) -> list[int]:
        stmt = select(SchoolTeacher.user_id).where(
            SchoolTeacher.school_id == school_id
        )
        return list(self.session.exec(stmt).all())

    def is_teacher_in_school(self, school_id: int, user_id: int) -> bool:
        return self._get_record(school_id, user_id) is not None

    def list_teachers(self, school_id: int) -> list[User]:
        stmt = (
            select(User)
            .join(SchoolTeacher, SchoolTeacher.user_id == User.id)
            .where(SchoolTeacher.school_id == school_id)
            .order_by(User.first_name, User.last_name)
        )
        return list(self.session.exec(stmt).all())

    def _get_record(self, school_id: int, user_id: int) -> SchoolTeacher | None:
        stmt = select(SchoolTeacher).where(
            SchoolTeacher.school_id == school_id,
            SchoolTeacher.user_id == user_id,
        )
        return self.session.exec(stmt).first()
