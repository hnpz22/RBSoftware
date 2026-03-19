from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.academic.models.lms_assignment import LmsAssignment
from app.domains.academic.models.lms_unit import LmsUnit
from app.domains.academic.schemas.lms_assignment import AssignmentCreate, AssignmentUpdate


class AssignmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, unit_id: int, payload: AssignmentCreate) -> LmsAssignment:
        assignment = LmsAssignment.model_validate(payload, update={"unit_id": unit_id})
        self.session.add(assignment)
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def get_by_id(self, assignment_id: int) -> LmsAssignment | None:
        return self.session.get(LmsAssignment, assignment_id)

    def get_by_public_id(self, public_id: UUID) -> LmsAssignment | None:
        stmt = select(LmsAssignment).where(LmsAssignment.public_id == public_id)
        return self.session.exec(stmt).first()

    def list_by_unit(
        self, unit_id: int, published_only: bool = False
    ) -> list[LmsAssignment]:
        stmt = select(LmsAssignment).where(LmsAssignment.unit_id == unit_id)
        if published_only:
            stmt = stmt.where(LmsAssignment.is_published.is_(True))
        stmt = stmt.order_by(LmsAssignment.title)
        return list(self.session.exec(stmt).all())

    def list_by_course(self, course_id: int) -> list[LmsAssignment]:
        stmt = (
            select(LmsAssignment)
            .join(LmsUnit, LmsUnit.id == LmsAssignment.unit_id)
            .where(LmsUnit.course_id == course_id)
            .order_by(LmsUnit.order_index, LmsAssignment.title)
        )
        return list(self.session.exec(stmt).all())

    def update(
        self, assignment: LmsAssignment, payload: AssignmentUpdate
    ) -> LmsAssignment:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(assignment, field_name, value)
        self.session.add(assignment)
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def delete(self, assignment: LmsAssignment) -> None:
        self.session.delete(assignment)
        self.session.commit()
