"""ACADEMIC domain SQLModel entities."""

from app.domains.academic.models.lms_assignment import LmsAssignment
from app.domains.academic.models.lms_course import LmsCourse
from app.domains.academic.models.lms_course_student import LmsCourseStudent
from app.domains.academic.models.lms_grade import LmsGrade
from app.domains.academic.models.lms_grade_director import LmsGradeDirector
from app.domains.academic.models.lms_material import LmsMaterial
from app.domains.academic.models.lms_submission import LmsSubmission
from app.domains.academic.models.lms_unit import LmsUnit
from app.domains.academic.models.school import School
from app.domains.academic.models.school_teacher import SchoolTeacher

__all__ = [
    "School",
    "SchoolTeacher",
    "LmsGrade",
    "LmsGradeDirector",
    "LmsCourse",
    "LmsCourseStudent",
    "LmsUnit",
    "LmsMaterial",
    "LmsAssignment",
    "LmsSubmission",
]
