from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.training.models.training_program import TrainingProgram
from app.domains.training.schemas.training_program import ProgramCreate, ProgramUpdate


class ProgramRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, program_id: int) -> TrainingProgram | None:
        return self.session.get(TrainingProgram, program_id)

    def get_by_public_id(self, public_id: UUID) -> TrainingProgram | None:
        stmt = select(TrainingProgram).where(TrainingProgram.public_id == public_id)
        return self.session.exec(stmt).first()

    def list_active(self) -> list[TrainingProgram]:
        stmt = (
            select(TrainingProgram)
            .where(TrainingProgram.is_active.is_(True))
            .order_by(TrainingProgram.name)
        )
        return list(self.session.exec(stmt).all())

    def list_by_creator(self, created_by: int) -> list[TrainingProgram]:
        stmt = (
            select(TrainingProgram)
            .where(
                TrainingProgram.is_active.is_(True),
                TrainingProgram.created_by == created_by,
            )
            .order_by(TrainingProgram.name)
        )
        return list(self.session.exec(stmt).all())

    def list_published(self) -> list[TrainingProgram]:
        stmt = (
            select(TrainingProgram)
            .where(
                TrainingProgram.is_active.is_(True),
                TrainingProgram.is_published.is_(True),
            )
            .order_by(TrainingProgram.name)
        )
        return list(self.session.exec(stmt).all())

    def create(self, payload: ProgramCreate, created_by: int | None = None) -> TrainingProgram:
        program = TrainingProgram.model_validate(payload, update={"created_by": created_by})
        self.session.add(program)
        self.session.commit()
        self.session.refresh(program)
        return program

    def update(self, program: TrainingProgram, payload: ProgramUpdate) -> TrainingProgram:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(program, field_name, value)
        self.session.add(program)
        self.session.commit()
        self.session.refresh(program)
        return program
