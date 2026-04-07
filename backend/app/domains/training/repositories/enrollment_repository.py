from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.training.models.training_enrollment import TrainingEnrollment
from app.domains.training.schemas.training_enrollment import EnrollmentRead


class EnrollmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_public_id(self, public_id: UUID) -> TrainingEnrollment | None:
        stmt = select(TrainingEnrollment).where(TrainingEnrollment.public_id == public_id)
        return self.session.exec(stmt).first()

    def get_by_user_and_program(
        self, user_id: int, program_id: int
    ) -> TrainingEnrollment | None:
        stmt = select(TrainingEnrollment).where(
            TrainingEnrollment.user_id == user_id,
            TrainingEnrollment.program_id == program_id,
        )
        return self.session.exec(stmt).first()

    def list_by_program(self, program_id: int) -> list[TrainingEnrollment]:
        stmt = (
            select(TrainingEnrollment)
            .where(TrainingEnrollment.program_id == program_id)
            .order_by(TrainingEnrollment.enrolled_at)
        )
        return list(self.session.exec(stmt).all())

    def list_by_user(self, user_id: int) -> list[TrainingEnrollment]:
        stmt = (
            select(TrainingEnrollment)
            .where(TrainingEnrollment.user_id == user_id)
            .order_by(TrainingEnrollment.enrolled_at.desc())
        )
        return list(self.session.exec(stmt).all())

    def is_enrolled(self, user_id: int, program_id: int) -> bool:
        enrollment = self.get_by_user_and_program(user_id, program_id)
        return enrollment is not None and enrollment.status == "ACTIVE"

    def create(self, enrollment: TrainingEnrollment) -> TrainingEnrollment:
        self.session.add(enrollment)
        self.session.commit()
        self.session.refresh(enrollment)
        return enrollment

    def update(
        self, enrollment: TrainingEnrollment, updates: dict
    ) -> TrainingEnrollment:
        for field_name, value in updates.items():
            setattr(enrollment, field_name, value)
        self.session.add(enrollment)
        self.session.commit()
        self.session.refresh(enrollment)
        return enrollment
