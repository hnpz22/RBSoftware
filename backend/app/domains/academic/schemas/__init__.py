"""ACADEMIC domain schemas."""

from app.domains.academic.schemas.composite import (
    AssignmentWithSubmissions,
    CourseDetail,
    GradeWithCourses,
    StudentCourseProgress,
    SubmissionWithStudent,
    UnitWithContent,
)
from app.domains.academic.schemas.lms_assignment import (
    AssignmentCreate,
    AssignmentRead,
    AssignmentUpdate,
)
from app.domains.academic.schemas.lms_course import (
    CourseCreate,
    CourseRead,
    CourseUpdate,
)
from app.domains.academic.schemas.lms_grade import (
    GradeCreate,
    GradeRead,
    GradeUpdate,
)
from app.domains.academic.schemas.lms_material import (
    MaterialCreate,
    MaterialRead,
    MaterialUpdate,
)
from app.domains.academic.schemas.lms_submission import (
    SubmissionRead,
    SubmissionUpdate,
)
from app.domains.academic.schemas.lms_unit import (
    UnitCreate,
    UnitRead,
    UnitUpdate,
)
from app.domains.academic.schemas.school import (
    SchoolCreate,
    SchoolRead,
    SchoolUpdate,
)

__all__ = [
    "SchoolCreate",
    "SchoolRead",
    "SchoolUpdate",
    "GradeCreate",
    "GradeRead",
    "GradeUpdate",
    "CourseCreate",
    "CourseRead",
    "CourseUpdate",
    "UnitCreate",
    "UnitRead",
    "UnitUpdate",
    "MaterialCreate",
    "MaterialRead",
    "MaterialUpdate",
    "AssignmentCreate",
    "AssignmentRead",
    "AssignmentUpdate",
    "SubmissionRead",
    "SubmissionUpdate",
    "GradeWithCourses",
    "CourseDetail",
    "UnitWithContent",
    "SubmissionWithStudent",
    "AssignmentWithSubmissions",
    "StudentCourseProgress",
]
