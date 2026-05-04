"""TRAINING domain schemas."""

from app.domains.training.schemas.composite import (
    EvaluationWithQuestions,
    ModuleWithContent,
    ProgramDetail,
    QuizSubmitRequest,
    TeacherProgramProgress,
)
from app.domains.training.schemas.training_certificate import CertificateRead
from app.domains.training.schemas.training_enrollment import EnrollmentRead
from app.domains.training.schemas.training_evaluation import (
    EvaluationCreate,
    EvaluationRead,
    EvaluationUpdate,
)
from app.domains.training.schemas.training_lesson import (
    LessonCreate,
    LessonRead,
    LessonUpdate,
)
from app.domains.training.schemas.training_lesson_progress import LessonProgressRead
from app.domains.training.schemas.training_module import (
    ModuleCreate,
    ModuleRead,
    ModuleUpdate,
)
from app.domains.training.schemas.training_program import (
    ProgramCreate,
    ProgramRead,
    ProgramUpdate,
)
from app.domains.training.schemas.training_quiz_question import (
    QuizQuestionCreate,
    QuizQuestionRead,
    QuizQuestionUpdate,
)
from app.domains.training.schemas.training_submission import (
    SubmissionRead,
    SubmissionUpdate,
)
from app.domains.training.schemas.training_template import TemplateRead

__all__ = [
    "ProgramCreate",
    "ProgramRead",
    "ProgramUpdate",
    "ModuleCreate",
    "ModuleRead",
    "ModuleUpdate",
    "LessonCreate",
    "LessonRead",
    "LessonUpdate",
    "EvaluationCreate",
    "EvaluationRead",
    "EvaluationUpdate",
    "QuizQuestionCreate",
    "QuizQuestionRead",
    "QuizQuestionUpdate",
    "EnrollmentRead",
    "SubmissionRead",
    "SubmissionUpdate",
    "CertificateRead",
    "LessonProgressRead",
    "ProgramDetail",
    "ModuleWithContent",
    "EvaluationWithQuestions",
    "TeacherProgramProgress",
    "QuizSubmitRequest",
    "TemplateRead",
]
