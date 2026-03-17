from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.domains.academic.schemas.lms_assignment import LmsAssignmentRead
from app.domains.academic.schemas.lms_course import LmsCourseRead
from app.domains.academic.schemas.lms_material import LmsMaterialRead
from app.domains.academic.schemas.lms_submission import LmsSubmissionRead
from app.domains.academic.schemas.lms_unit import LmsUnitRead


class GradeDirectorRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    first_name: str
    last_name: str
    email: str


class GradeWithCourses(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    label: str | None
    order_index: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    director: GradeDirectorRead | None = None
    courses: list[LmsCourseRead] = []


class CourseTeacherRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    first_name: str
    last_name: str
    email: str


class CourseStudentRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    first_name: str
    last_name: str
    email: str


class CourseDetail(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    description: str | None
    year: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    teacher: CourseTeacherRead | None = None
    students: list[CourseStudentRead] = []
    units: list[LmsUnitRead] = []


class UnitWithContent(SQLModel):
    public_id: UUID
    title: str
    description: str | None
    order_index: int
    is_published: bool
    materials: list[LmsMaterialRead] = []
    assignments: list[LmsAssignmentRead] = []


class SubmissionStudentRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    first_name: str
    last_name: str
    email: str


class AssignmentSubmissionRead(SQLModel):
    public_id: UUID
    content: str | None
    file_name: str | None
    status: str
    score: Decimal | None
    feedback: str | None
    graded_at: datetime | None
    submitted_at: datetime | None
    student: SubmissionStudentRead


class AssignmentWithSubmissions(SQLModel):
    public_id: UUID
    title: str
    description: str | None
    max_score: Decimal
    due_date: datetime | None
    is_published: bool
    submissions: list[AssignmentSubmissionRead] = []


class StudentAssignmentProgress(SQLModel):
    assignment_public_id: UUID
    assignment_title: str
    max_score: Decimal
    due_date: datetime | None
    submission: LmsSubmissionRead | None = None


class StudentProgress(SQLModel):
    course_public_id: UUID
    student_public_id: UUID
    assignments: list[StudentAssignmentProgress] = []


class StudentAssignmentWithMySubmission(SQLModel):
    public_id: UUID
    title: str
    description: str | None
    max_score: Decimal
    due_date: datetime | None
    order_index: int
    is_published: bool
    my_submission: LmsSubmissionRead | None = None


class StudentCourseContentUnit(SQLModel):
    public_id: UUID
    title: str
    description: str | None
    order_index: int
    materials: list[LmsMaterialRead] = []
    assignments: list[StudentAssignmentWithMySubmission] = []
