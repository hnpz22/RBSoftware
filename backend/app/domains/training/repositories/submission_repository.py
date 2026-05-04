from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.domains.training.models.training_submission import (
    TrainingSubmission,
    TrainingSubmissionStatus,
)


class SubmissionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_public_id(self, public_id: UUID) -> TrainingSubmission | None:
        stmt = select(TrainingSubmission).where(TrainingSubmission.public_id == public_id)
        return self.session.exec(stmt).first()

    def get_by_user_and_evaluation(
        self, user_id: int, evaluation_id: int
    ) -> TrainingSubmission | None:
        stmt = select(TrainingSubmission).where(
            TrainingSubmission.user_id == user_id,
            TrainingSubmission.evaluation_id == evaluation_id,
        )
        return self.session.exec(stmt).first()

    def get_by_evaluation(self, evaluation_id: int) -> list[TrainingSubmission]:
        stmt = (
            select(TrainingSubmission)
            .where(TrainingSubmission.evaluation_id == evaluation_id)
            .order_by(TrainingSubmission.submitted_at)
        )
        return list(self.session.exec(stmt).all())

    def upsert(
        self,
        user_id: int,
        evaluation_id: int,
        *,
        content: str | None = None,
        file_key: str | None = None,
        file_name: str | None = None,
        quiz_answers: dict | None = None,
    ) -> TrainingSubmission | None:
        from app.domains.training.models.training_evaluation import TrainingEvaluation

        evaluation = self.session.get(TrainingEvaluation, evaluation_id)
        existing = self.get_by_user_and_evaluation(user_id, evaluation_id)

        if existing is not None:
            if existing.status == TrainingSubmissionStatus.GRADED:
                if (
                    evaluation is not None
                    and existing.score is not None
                    and existing.score >= evaluation.passing_score
                ):
                    return None
                max_attempts = evaluation.max_attempts if evaluation is not None else 3
                if existing.attempts_used >= max_attempts:
                    return None

            if content is not None:
                existing.content = content
            if file_key is not None:
                existing.file_key = file_key
                existing.file_name = file_name
            if quiz_answers is not None:
                existing.quiz_answers = quiz_answers
            existing.status = TrainingSubmissionStatus.SUBMITTED
            existing.submitted_at = datetime.now(timezone.utc)
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        submission = TrainingSubmission(
            evaluation_id=evaluation_id,
            user_id=user_id,
            content=content,
            file_key=file_key,
            file_name=file_name,
            quiz_answers=quiz_answers,
            status=TrainingSubmissionStatus.SUBMITTED,
            submitted_at=datetime.now(timezone.utc),
        )
        self.session.add(submission)
        self.session.commit()
        self.session.refresh(submission)
        return submission
