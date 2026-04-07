from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.training.models.training_evaluation import TrainingEvaluation
from app.domains.training.schemas.training_evaluation import EvaluationCreate, EvaluationUpdate


class EvaluationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, evaluation_id: int) -> TrainingEvaluation | None:
        return self.session.get(TrainingEvaluation, evaluation_id)

    def get_by_public_id(self, public_id: UUID) -> TrainingEvaluation | None:
        stmt = select(TrainingEvaluation).where(TrainingEvaluation.public_id == public_id)
        return self.session.exec(stmt).first()

    def list_by_module(
        self, module_id: int, published_only: bool = False
    ) -> list[TrainingEvaluation]:
        stmt = select(TrainingEvaluation).where(TrainingEvaluation.module_id == module_id)
        if published_only:
            stmt = stmt.where(TrainingEvaluation.is_published.is_(True))
        stmt = stmt.order_by(TrainingEvaluation.title)
        return list(self.session.exec(stmt).all())

    def create(self, module_id: int, payload: EvaluationCreate) -> TrainingEvaluation:
        evaluation = TrainingEvaluation.model_validate(
            payload, update={"module_id": module_id}
        )
        self.session.add(evaluation)
        self.session.commit()
        self.session.refresh(evaluation)
        return evaluation

    def update(
        self, evaluation: TrainingEvaluation, payload: EvaluationUpdate
    ) -> TrainingEvaluation:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(evaluation, field_name, value)
        self.session.add(evaluation)
        self.session.commit()
        self.session.refresh(evaluation)
        return evaluation
