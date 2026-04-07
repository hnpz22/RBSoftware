from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.training.models.training_quiz_question import TrainingQuizQuestion
from app.domains.training.schemas.training_quiz_question import (
    QuizQuestionCreate,
    QuizQuestionUpdate,
)


class QuizQuestionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, question_id: int) -> TrainingQuizQuestion | None:
        return self.session.get(TrainingQuizQuestion, question_id)

    def get_by_public_id(self, public_id: UUID) -> TrainingQuizQuestion | None:
        stmt = select(TrainingQuizQuestion).where(
            TrainingQuizQuestion.public_id == public_id
        )
        return self.session.exec(stmt).first()

    def list_by_evaluation(self, evaluation_id: int) -> list[TrainingQuizQuestion]:
        stmt = (
            select(TrainingQuizQuestion)
            .where(TrainingQuizQuestion.evaluation_id == evaluation_id)
            .order_by(TrainingQuizQuestion.order_index)
        )
        return list(self.session.exec(stmt).all())

    def create(
        self, evaluation_id: int, payload: QuizQuestionCreate
    ) -> TrainingQuizQuestion:
        question = TrainingQuizQuestion.model_validate(
            payload, update={"evaluation_id": evaluation_id}
        )
        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)
        return question

    def update(
        self, question: TrainingQuizQuestion, payload: QuizQuestionUpdate
    ) -> TrainingQuizQuestion:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(question, field_name, value)
        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)
        return question

    def delete(self, question: TrainingQuizQuestion) -> None:
        self.session.delete(question)
        self.session.commit()
