"""TRAINING domain SQLModel entities."""

from app.domains.training.models.training_program import TrainingProgram
from app.domains.training.models.training_module import TrainingModule
from app.domains.training.models.training_lesson import TrainingLesson
from app.domains.training.models.training_evaluation import TrainingEvaluation
from app.domains.training.models.training_quiz_question import TrainingQuizQuestion
from app.domains.training.models.training_enrollment import TrainingEnrollment
from app.domains.training.models.training_submission import TrainingSubmission
from app.domains.training.models.training_certificate import TrainingCertificate
from app.domains.training.models.training_lesson_progress import TrainingLessonProgress

__all__ = [
    "TrainingProgram",
    "TrainingModule",
    "TrainingLesson",
    "TrainingEvaluation",
    "TrainingQuizQuestion",
    "TrainingEnrollment",
    "TrainingSubmission",
    "TrainingCertificate",
    "TrainingLessonProgress",
]
