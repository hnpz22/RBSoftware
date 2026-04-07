from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.training.models.training_lesson import TrainingLesson
from app.domains.training.schemas.training_lesson import LessonCreate, LessonUpdate


class LessonRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, lesson_id: int) -> TrainingLesson | None:
        return self.session.get(TrainingLesson, lesson_id)

    def get_by_public_id(self, public_id: UUID) -> TrainingLesson | None:
        stmt = select(TrainingLesson).where(TrainingLesson.public_id == public_id)
        return self.session.exec(stmt).first()

    def list_by_module(
        self, module_id: int, published_only: bool = False
    ) -> list[TrainingLesson]:
        stmt = select(TrainingLesson).where(TrainingLesson.module_id == module_id)
        if published_only:
            stmt = stmt.where(TrainingLesson.is_published.is_(True))
        stmt = stmt.order_by(TrainingLesson.order_index)
        return list(self.session.exec(stmt).all())

    def create(self, module_id: int, payload: LessonCreate) -> TrainingLesson:
        lesson = TrainingLesson.model_validate(payload, update={"module_id": module_id})
        self.session.add(lesson)
        self.session.commit()
        self.session.refresh(lesson)
        return lesson

    def update(self, lesson: TrainingLesson, payload: LessonUpdate) -> TrainingLesson:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(lesson, field_name, value)
        self.session.add(lesson)
        self.session.commit()
        self.session.refresh(lesson)
        return lesson
