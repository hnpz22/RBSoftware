"""ACADEMIC domain schemas."""

from app.domains.academic.schemas.composite import (
    AssignmentSubmissionRead,
    AssignmentWithSubmissions,
    CourseDetail,
    CourseStudentRead,
    CourseTeacherRead,
    GradeDirectorRead,
    GradeWithCourses,
    StudentAssignmentProgress,
    StudentAssignmentWithMySubmission,
    StudentCourseContentUnit,
    StudentProgress,
    SubmissionStudentRead,
    UnitWithContent,
)
from app.domains.academic.schemas.lms_assignment import (
    LmsAssignmentCreate,
    LmsAssignmentRead,
    LmsAssignmentUpdate,
)
from app.domains.academic.schemas.lms_course import (
    LmsCourseCreate,
    LmsCourseRead,
    LmsCourseUpdate,
)
from app.domains.academic.schemas.lms_material import (
    LmsMaterialCreate,
    LmsMaterialRead,
    LmsMaterialUpdate,
)
from app.domains.academic.schemas.lms_submission import (
    LmsSubmissionCreate,
    LmsSubmissionRead,
    LmsSubmissionUpdate,
)
from app.domains.academic.schemas.lms_unit import (
    LmsUnitCreate,
    LmsUnitRead,
    LmsUnitUpdate,
)
from app.domains.academic.schemas.lms_grade import (
    LmsGradeCreate,
    LmsGradeRead,
    LmsGradeUpdate,
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
    "LmsGradeCreate",
    "LmsGradeRead",
    "LmsGradeUpdate",
    "LmsCourseCreate",
    "LmsCourseRead",
    "LmsCourseUpdate",
    "LmsUnitCreate",
    "LmsUnitRead",
    "LmsUnitUpdate",
    "LmsMaterialCreate",
    "LmsMaterialRead",
    "LmsMaterialUpdate",
    "LmsAssignmentCreate",
    "LmsAssignmentRead",
    "LmsAssignmentUpdate",
    "LmsSubmissionCreate",
    "LmsSubmissionRead",
    "LmsSubmissionUpdate",
    "GradeDirectorRead",
    "GradeWithCourses",
    "CourseTeacherRead",
    "CourseStudentRead",
    "CourseDetail",
    "UnitWithContent",
    "SubmissionStudentRead",
    "AssignmentSubmissionRead",
    "AssignmentWithSubmissions",
    "StudentAssignmentProgress",
    "StudentProgress",
    "StudentAssignmentWithMySubmission",
    "StudentCourseContentUnit",
]
