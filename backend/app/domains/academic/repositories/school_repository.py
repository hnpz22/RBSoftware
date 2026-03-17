from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.academic.models.school import School
from app.domains.academic.schemas.school import SchoolCreate, SchoolUpdate


class SchoolRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: SchoolCreate) -> School:
        school = School.model_validate(payload)
        self.session.add(school)
        self.session.commit()
        self.session.refresh(school)
        return school

    def get_by_id(self, school_id: int) -> School | None:
        return self.session.get(School, school_id)

    def get_by_public_id(self, public_id: UUID) -> School | None:
        stmt = select(School).where(School.public_id == public_id)
        return self.session.exec(stmt).first()

    def get_by_code(self, code: str) -> School | None:
        stmt = select(School).where(School.code == code)
        return self.session.exec(stmt).first()

    def list(self, is_active: bool | None = None) -> list[School]:
        stmt = select(School)
        if is_active is not None:
            stmt = stmt.where(School.is_active == is_active)
        stmt = stmt.order_by(School.name)
        return list(self.session.exec(stmt).all())

    def list_active(self) -> list[School]:
        return self.list(is_active=True)

    def update(self, school: School, payload: SchoolUpdate) -> School:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(school, field_name, value)
        self.session.add(school)
        self.session.commit()
        self.session.refresh(school)
        return school

    def delete(self, school: School) -> None:
        self.session.delete(school)
        self.session.commit()
