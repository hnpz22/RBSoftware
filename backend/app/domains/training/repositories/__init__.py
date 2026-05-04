"""TRAINING domain repositories."""

from app.domains.training.repositories.certificate_repository import CertificateRepository
from app.domains.training.repositories.enrollment_repository import EnrollmentRepository
from app.domains.training.repositories.evaluation_repository import EvaluationRepository
from app.domains.training.repositories.lesson_progress_repository import LessonProgressRepository
from app.domains.training.repositories.lesson_repository import LessonRepository
from app.domains.training.repositories.module_repository import ModuleRepository
from app.domains.training.repositories.program_repository import ProgramRepository
from app.domains.training.repositories.quiz_question_repository import QuizQuestionRepository
from app.domains.training.repositories.submission_repository import SubmissionRepository
from app.domains.training.repositories.template_repository import TemplateRepository

__all__ = [
    "ProgramRepository",
    "ModuleRepository",
    "LessonRepository",
    "EvaluationRepository",
    "QuizQuestionRepository",
    "EnrollmentRepository",
    "SubmissionRepository",
    "CertificateRepository",
    "LessonProgressRepository",
    "TemplateRepository",
]
