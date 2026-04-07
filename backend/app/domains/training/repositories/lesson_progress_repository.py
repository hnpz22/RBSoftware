from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from app.domains.training.models.training_lesson import TrainingLesson
from app.domains.training.models.training_lesson_progress import TrainingLessonProgress
from app.domains.training.models.training_module import TrainingModule


class LessonProgressRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def mark_completed(self, user_id: int, lesson_id: int) -> TrainingLessonProgress:
        existing = self._get_record(user_id, lesson_id)
        if existing is not None:
            return existing
        progress = TrainingLessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completed_at=datetime.now(timezone.utc),
        )
        self.session.add(progress)
        self.session.commit()
        self.session.refresh(progress)
        return progress

    def get_completed_lessons(self, user_id: int, program_id: int) -> list[int]:
        stmt = (
            select(TrainingLessonProgress.lesson_id)
            .join(TrainingLesson, TrainingLesson.id == TrainingLessonProgress.lesson_id)
            .join(TrainingModule, TrainingModule.id == TrainingLesson.module_id)
            .where(
                TrainingLessonProgress.user_id == user_id,
                TrainingModule.program_id == program_id,
            )
        )
        return list(self.session.exec(stmt).all())

    def is_completed(self, user_id: int, lesson_id: int) -> bool:
        return self._get_record(user_id, lesson_id) is not None

    def _get_record(
        self, user_id: int, lesson_id: int
    ) -> TrainingLessonProgress | None:
        stmt = select(TrainingLessonProgress).where(
            TrainingLessonProgress.user_id == user_id,
            TrainingLessonProgress.lesson_id == lesson_id,
        )
        return self.session.exec(stmt).first()
