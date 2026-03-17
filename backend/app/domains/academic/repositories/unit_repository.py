from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.academic.models.lms_unit import LmsUnit
from app.domains.academic.schemas.lms_unit import LmsUnitCreate, LmsUnitUpdate


class UnitRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, course_id: int, payload: LmsUnitCreate) -> LmsUnit:
        unit = LmsUnit.model_validate(payload, update={"course_id": course_id})
        self.session.add(unit)
        self.session.commit()
        self.session.refresh(unit)
        return unit

    def get_by_id(self, unit_id: int) -> LmsUnit | None:
        return self.session.get(LmsUnit, unit_id)

    def get_by_public_id(self, public_id: UUID) -> LmsUnit | None:
        stmt = select(LmsUnit).where(LmsUnit.public_id == public_id)
        return self.session.exec(stmt).first()

    def list_by_course(
        self, course_id: int, published_only: bool = False
    ) -> list[LmsUnit]:
        stmt = select(LmsUnit).where(LmsUnit.course_id == course_id)
        if published_only:
            stmt = stmt.where(LmsUnit.is_published.is_(True))
        stmt = stmt.order_by(LmsUnit.order_index)
        return list(self.session.exec(stmt).all())

    def reorder(self, unit: LmsUnit, new_index: int) -> LmsUnit:
        unit.order_index = new_index
        self.session.add(unit)
        self.session.commit()
        self.session.refresh(unit)
        return unit

    def update(self, unit: LmsUnit, payload: LmsUnitUpdate) -> LmsUnit:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(unit, field_name, value)
        self.session.add(unit)
        self.session.commit()
        self.session.refresh(unit)
        return unit

    def publish(self, unit: LmsUnit) -> LmsUnit:
        unit.is_published = True
        self.session.add(unit)
        self.session.commit()
        self.session.refresh(unit)
        return unit

    def unpublish(self, unit: LmsUnit) -> LmsUnit:
        unit.is_published = False
        self.session.add(unit)
        self.session.commit()
        self.session.refresh(unit)
        return unit

    def delete(self, unit: LmsUnit) -> None:
        self.session.delete(unit)
        self.session.commit()
