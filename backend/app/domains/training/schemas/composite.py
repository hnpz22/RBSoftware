from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.domains.training.schemas.training_evaluation import EvaluationRead
from app.domains.training.schemas.training_lesson import LessonRead
from app.domains.training.schemas.training_module import ModuleRead
from app.domains.training.schemas.training_program import ProgramRead
from app.domains.training.schemas.training_quiz_question import QuizQuestionRead


class ProgramDetail(ProgramRead):
    modules: list[ModuleRead] = []
    enrolled_count: int = 0
    trainer_name: str = ""


class ModuleWithContent(ModuleRead):
    lessons: list[LessonRead] = []
    evaluations: list[EvaluationRead] = []


class EvaluationWithQuestions(EvaluationRead):
    questions: list[QuizQuestionRead] = []


class TeacherProgramProgress(SQLModel):
    program_id: UUID
    program_name: str
    total_lessons: int
    completed_lessons: int
    total_evaluations: int
    passed_evaluations: int
    overall_score: float | None = None
    is_certified: bool = False
    certificate_code: str | None = None


class QuizSubmitRequest(SQLModel):
    answers: dict[str, int]
