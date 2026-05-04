from __future__ import annotations

from sqlmodel import Session, select

from app.domains.training.models.training_template import TrainingTemplate


class TemplateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_public_id(self, public_id: str) -> TrainingTemplate | None:
        stmt = select(TrainingTemplate).where(TrainingTemplate.public_id == public_id)
        return self.session.exec(stmt).first()

    def list_by_program(self, program_id: int) -> list[TrainingTemplate]:
        stmt = (
            select(TrainingTemplate)
            .where(TrainingTemplate.program_id == program_id)
            .order_by(TrainingTemplate.created_at.desc())
        )
        return list(self.session.exec(stmt).all())

    def create(self, template: TrainingTemplate) -> TrainingTemplate:
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        return template

    def delete(self, template: TrainingTemplate) -> None:
        self.session.delete(template)
        self.session.commit()
