from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import Session

from app.domains.academic.models.lms_assignment import LmsAssignment
from app.domains.academic.models.lms_course import LmsCourse
from app.domains.academic.models.lms_grade import LmsGrade
from app.domains.academic.models.lms_material import LmsMaterial
from app.domains.academic.models.lms_submission import LmsSubmission, SubmissionStatus
from app.domains.academic.models.lms_unit import LmsUnit
from app.domains.academic.models.school import School
from app.domains.academic.repositories import (
    AssignmentRepository,
    CourseRepository,
    CourseStudentRepository,
    GradeDirectorRepository,
    GradeRepository,
    MaterialRepository,
    SchoolRepository,
    SubmissionRepository,
    UnitRepository,
)
from app.domains.academic.schemas.lms_assignment import LmsAssignmentCreate, LmsAssignmentUpdate
from app.domains.academic.schemas.lms_course import LmsCourseCreate, LmsCourseUpdate
from app.domains.academic.schemas.lms_grade import LmsGradeCreate, LmsGradeUpdate
from app.domains.academic.schemas.lms_material import LmsMaterialCreate
from app.domains.academic.schemas.lms_submission import LmsSubmissionUpdate
from app.domains.academic.schemas.lms_unit import LmsUnitCreate, LmsUnitUpdate
from app.domains.academic.schemas.school import SchoolCreate, SchoolUpdate
from app.domains.audit.services import AuditService
from app.domains.auth.models import User
from app.domains.auth.repositories import UserRepository

_audit = AuditService()


class AcademicService:

    # ── Schools (Admin only) ──────────────────────────────────────────────────

    def create_school(self, session: Session, data: SchoolCreate) -> School:
        repo = SchoolRepository(session)
        if repo.get_by_code(data.code) is not None:
            raise ValueError(f"School code already exists: {data.code}")
        return repo.create(data)

    def get_school(self, session: Session, public_id: UUID) -> School | None:
        return SchoolRepository(session).get_by_public_id(public_id)

    def list_schools(
        self, session: Session, is_active: bool | None = True
    ) -> list[School]:
        return SchoolRepository(session).list(is_active=is_active)

    def update_school(
        self, session: Session, public_id: UUID, data: SchoolUpdate
    ) -> School | None:
        repo = SchoolRepository(session)
        school = repo.get_by_public_id(public_id)
        if school is None:
            return None
        if data.code is not None and data.code != school.code:
            if repo.get_by_code(data.code) is not None:
                raise ValueError(f"School code already exists: {data.code}")
        return repo.update(school, data)

    # ── Grades (Admin only) ───────────────────────────────────────────────────

    def create_grade(
        self, session: Session, school_public_id: UUID, data: LmsGradeCreate
    ) -> LmsGrade:
        school = SchoolRepository(session).get_by_public_id(school_public_id)
        if school is None:
            raise LookupError("School not found")
        return GradeRepository(session).create(school.id, data)

    def get_grade(self, session: Session, public_id: UUID) -> LmsGrade | None:
        return GradeRepository(session).get_by_public_id(public_id)

    def list_grades_by_school(
        self, session: Session, school_public_id: UUID
    ) -> list[LmsGrade]:
        school = SchoolRepository(session).get_by_public_id(school_public_id)
        if school is None:
            raise LookupError("School not found")
        return GradeRepository(session).list_by_school(school.id)

    def update_grade(
        self, session: Session, public_id: UUID, data: LmsGradeUpdate
    ) -> LmsGrade | None:
        repo = GradeRepository(session)
        grade = repo.get_by_public_id(public_id)
        if grade is None:
            return None
        return repo.update(grade, data)

    def assign_director(
        self,
        session: Session,
        grade_public_id: UUID,
        user_id_public: UUID,
        requesting_user: User,
    ) -> None:
        grade = GradeRepository(session).get_by_public_id(grade_public_id)
        if grade is None:
            raise LookupError("Grade not found")

        user = UserRepository(session).get_by_public_id(user_id_public)
        if user is None:
            raise LookupError("User not found")

        director_repo = GradeDirectorRepository(session)
        if director_repo.is_director_of_any_grade_in_school(grade.school_id, user.id):
            existing_grades = director_repo.get_grades_for_director(user.id)
            for g in existing_grades:
                if g.school_id == grade.school_id and g.id != grade.id:
                    raise ValueError(
                        "User is already director of another grade in this school"
                    )

        director_repo.assign(grade.id, user.id)
        _audit.log(
            session,
            user_id=requesting_user.id,
            action="academic.grade.assign_director",
            resource_type="lms_grade",
            resource_id=str(grade.public_id),
            payload={"director_user_public_id": str(user.public_id)},
        )

    def unassign_director(
        self,
        session: Session,
        grade_public_id: UUID,
        requesting_user: User,
    ) -> None:
        grade = GradeRepository(session).get_by_public_id(grade_public_id)
        if grade is None:
            raise LookupError("Grade not found")

        director_repo = GradeDirectorRepository(session)
        director = director_repo.get_director(grade.id)
        if director is None:
            raise LookupError("No active director for this grade")

        director_repo.unassign(grade.id, director.id)
        _audit.log(
            session,
            user_id=requesting_user.id,
            action="academic.grade.unassign_director",
            resource_type="lms_grade",
            resource_id=str(grade.public_id),
        )

    def get_my_grades(self, session: Session, user: User) -> list[LmsGrade]:
        return GradeDirectorRepository(session).get_grades_for_director(user.id)

    # ── Courses (Admin or Director of the grade) ─────────────────────────────

    def create_course(
        self,
        session: Session,
        grade_public_id: UUID,
        data: LmsCourseCreate,
        teacher_public_id: UUID | None,
        requesting_user: User,
    ) -> LmsCourse:
        grade = GradeRepository(session).get_by_public_id(grade_public_id)
        if grade is None:
            raise LookupError("Grade not found")

        self._assert_admin_or_director(session, grade, requesting_user)

        teacher_id = None
        if teacher_public_id is not None:
            teacher = UserRepository(session).get_by_public_id(teacher_public_id)
            if teacher is None:
                raise LookupError("Teacher user not found")
            teacher_id = teacher.id

        course = CourseRepository(session).create(
            grade.id, grade.school_id, teacher_id, data
        )

        _audit.log(
            session,
            user_id=requesting_user.id,
            action="academic.course.create",
            resource_type="lms_course",
            resource_id=str(course.public_id),
        )
        return course

    def update_course(
        self,
        session: Session,
        course_public_id: UUID,
        data: LmsCourseUpdate,
        requesting_user: User,
    ) -> LmsCourse | None:
        repo = CourseRepository(session)
        course = repo.get_by_public_id(course_public_id)
        if course is None:
            return None
        grade = GradeRepository(session).get_by_id(course.grade_id)
        self._assert_admin_or_director(session, grade, requesting_user)
        return repo.update(course, data)

    def assign_teacher(
        self,
        session: Session,
        course_public_id: UUID,
        teacher_public_id: UUID,
        requesting_user: User,
    ) -> LmsCourse:
        repo = CourseRepository(session)
        course = repo.get_by_public_id(course_public_id)
        if course is None:
            raise LookupError("Course not found")

        grade = GradeRepository(session).get_by_id(course.grade_id)
        self._assert_admin_or_director(session, grade, requesting_user)

        teacher = UserRepository(session).get_by_public_id(teacher_public_id)
        if teacher is None:
            raise LookupError("Teacher user not found")

        course = repo.set_teacher(course, teacher.id)
        _audit.log(
            session,
            user_id=requesting_user.id,
            action="academic.course.assign_teacher",
            resource_type="lms_course",
            resource_id=str(course.public_id),
            payload={"teacher_public_id": str(teacher.public_id)},
        )
        return course

    def list_courses_by_grade(
        self, session: Session, grade_public_id: UUID
    ) -> list[LmsCourse]:
        grade = GradeRepository(session).get_by_public_id(grade_public_id)
        if grade is None:
            raise LookupError("Grade not found")
        return CourseRepository(session).list_by_grade(grade.id)

    def get_course_detail(
        self, session: Session, course_public_id: UUID
    ) -> tuple[LmsCourse, User | None, list[User], list[LmsUnit]] | None:
        repo = CourseRepository(session)
        course = repo.get_by_public_id(course_public_id)
        if course is None:
            return None

        teacher = None
        if course.teacher_id is not None:
            teacher = UserRepository(session).get_by_id(course.teacher_id)

        students = CourseStudentRepository(session).get_students(course.id)
        units = UnitRepository(session).list_by_course(course.id)
        return course, teacher, students, units

    def get_my_courses_teacher(
        self, session: Session, user: User
    ) -> list[LmsCourse]:
        return CourseRepository(session).list_by_teacher(user.id)

    def get_my_courses_student(
        self, session: Session, user: User
    ) -> list[LmsCourse]:
        return CourseStudentRepository(session).get_courses_for_student(user.id)

    # ── Students (Admin or Director) ─────────────────────────────────────────

    def enroll_student(
        self,
        session: Session,
        course_public_id: UUID,
        student_public_id: UUID,
        requesting_user: User,
    ) -> None:
        course = CourseRepository(session).get_by_public_id(course_public_id)
        if course is None:
            raise LookupError("Course not found")

        grade = GradeRepository(session).get_by_id(course.grade_id)
        self._assert_admin_or_director(session, grade, requesting_user)

        student = UserRepository(session).get_by_public_id(student_public_id)
        if student is None:
            raise LookupError("Student user not found")

        CourseStudentRepository(session).enroll(course.id, student.id)

    def unenroll_student(
        self,
        session: Session,
        course_public_id: UUID,
        student_public_id: UUID,
        requesting_user: User,
    ) -> None:
        course = CourseRepository(session).get_by_public_id(course_public_id)
        if course is None:
            raise LookupError("Course not found")

        grade = GradeRepository(session).get_by_id(course.grade_id)
        self._assert_admin_or_director(session, grade, requesting_user)

        student = UserRepository(session).get_by_public_id(student_public_id)
        if student is None:
            raise LookupError("Student user not found")

        if not CourseStudentRepository(session).unenroll(course.id, student.id):
            raise LookupError("Student is not enrolled in this course")

    def transfer_student(
        self,
        session: Session,
        student_public_id: UUID,
        from_course_public_id: UUID,
        to_course_public_id: UUID,
        requesting_user: User,
    ) -> None:
        student = UserRepository(session).get_by_public_id(student_public_id)
        if student is None:
            raise LookupError("Student not found")

        from_course = CourseRepository(session).get_by_public_id(from_course_public_id)
        to_course = CourseRepository(session).get_by_public_id(to_course_public_id)
        if from_course is None or to_course is None:
            raise LookupError("Course not found")

        if from_course.grade_id != to_course.grade_id:
            raise ValueError("Both courses must belong to the same grade")

        grade = GradeRepository(session).get_by_id(from_course.grade_id)
        self._assert_admin_or_director(session, grade, requesting_user)

        CourseStudentRepository(session).transfer(
            student.id, from_course.id, to_course.id
        )

        _audit.log(
            session,
            user_id=requesting_user.id,
            action="academic.student.transfer",
            resource_type="lms_course_student",
            resource_id=str(student.public_id),
            payload={
                "from_course": str(from_course.public_id),
                "to_course": str(to_course.public_id),
            },
        )

    # ── Content (Teacher of the course) ──────────────────────────────────────

    def create_unit(
        self,
        session: Session,
        course_public_id: UUID,
        data: LmsUnitCreate,
        requesting_user: User,
    ) -> LmsUnit:
        course = CourseRepository(session).get_by_public_id(course_public_id)
        if course is None:
            raise LookupError("Course not found")
        self._assert_teacher(course, requesting_user)
        return UnitRepository(session).create(course.id, data)

    def update_unit(
        self,
        session: Session,
        unit_public_id: UUID,
        data: LmsUnitUpdate,
        requesting_user: User,
    ) -> LmsUnit | None:
        repo = UnitRepository(session)
        unit = repo.get_by_public_id(unit_public_id)
        if unit is None:
            return None
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_teacher(course, requesting_user)
        return repo.update(unit, data)

    def publish_unit(
        self, session: Session, unit_public_id: UUID, requesting_user: User
    ) -> LmsUnit:
        repo = UnitRepository(session)
        unit = repo.get_by_public_id(unit_public_id)
        if unit is None:
            raise LookupError("Unit not found")
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_teacher(course, requesting_user)
        return repo.publish(unit)

    def unpublish_unit(
        self, session: Session, unit_public_id: UUID, requesting_user: User
    ) -> LmsUnit:
        repo = UnitRepository(session)
        unit = repo.get_by_public_id(unit_public_id)
        if unit is None:
            raise LookupError("Unit not found")
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_teacher(course, requesting_user)
        return repo.unpublish(unit)

    def add_material(
        self,
        session: Session,
        unit_public_id: UUID,
        title: str,
        material_type: str,
        requesting_user: User,
        content: str | None = None,
        file_key: str | None = None,
        file_name: str | None = None,
    ) -> LmsMaterial:
        repo = UnitRepository(session)
        unit = repo.get_by_public_id(unit_public_id)
        if unit is None:
            raise LookupError("Unit not found")
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_teacher(course, requesting_user)

        mat_data = LmsMaterialCreate(
            title=title,
            type=material_type,
            content=content,
            file_key=file_key,
            file_name=file_name,
        )
        return MaterialRepository(session).create(unit.id, mat_data)

    def delete_material(
        self, session: Session, material_public_id: UUID, requesting_user: User
    ) -> None:
        repo = MaterialRepository(session)
        material = repo.get_by_public_id(material_public_id)
        if material is None:
            raise LookupError("Material not found")
        unit = UnitRepository(session).get_by_id(material.unit_id)
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_teacher(course, requesting_user)
        repo.delete(material)

    def get_material(
        self, session: Session, material_public_id: UUID
    ) -> LmsMaterial | None:
        return MaterialRepository(session).get_by_public_id(material_public_id)

    def get_material_course(
        self, session: Session, material: LmsMaterial
    ) -> LmsCourse:
        unit = UnitRepository(session).get_by_id(material.unit_id)
        return CourseRepository(session).get_by_id(unit.course_id)

    def create_assignment(
        self,
        session: Session,
        unit_public_id: UUID,
        data: LmsAssignmentCreate,
        requesting_user: User,
    ) -> LmsAssignment:
        unit = UnitRepository(session).get_by_public_id(unit_public_id)
        if unit is None:
            raise LookupError("Unit not found")
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_teacher(course, requesting_user)
        return AssignmentRepository(session).create(unit.id, data)

    def update_assignment(
        self,
        session: Session,
        assignment_public_id: UUID,
        data: LmsAssignmentUpdate,
        requesting_user: User,
    ) -> LmsAssignment | None:
        repo = AssignmentRepository(session)
        assignment = repo.get_by_public_id(assignment_public_id)
        if assignment is None:
            return None
        unit = UnitRepository(session).get_by_id(assignment.unit_id)
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_teacher(course, requesting_user)
        return repo.update(assignment, data)

    def get_assignment_submissions(
        self,
        session: Session,
        assignment_public_id: UUID,
        requesting_user: User,
    ) -> list[tuple[LmsSubmission, User]]:
        assignment = AssignmentRepository(session).get_by_public_id(assignment_public_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        unit = UnitRepository(session).get_by_id(assignment.unit_id)
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_teacher(course, requesting_user)
        return SubmissionRepository(session).get_by_assignment(assignment.id)

    # ── Submissions (Student enrolled) ───────────────────────────────────────

    def submit(
        self,
        session: Session,
        assignment_public_id: UUID,
        student: User,
        content: str | None = None,
        file_key: str | None = None,
        file_name: str | None = None,
    ) -> LmsSubmission:
        assignment = AssignmentRepository(session).get_by_public_id(assignment_public_id)
        if assignment is None:
            raise LookupError("Assignment not found")

        if not assignment.is_published:
            raise ValueError("Assignment is not published")

        unit = UnitRepository(session).get_by_id(assignment.unit_id)
        course = CourseRepository(session).get_by_id(unit.course_id)

        if not CourseStudentRepository(session).is_enrolled(course.id, student.id):
            raise PermissionError("Student is not enrolled in this course")

        return SubmissionRepository(session).upsert(
            assignment_id=assignment.id,
            student_id=student.id,
            content=content,
            file_key=file_key,
            file_name=file_name,
        )

    def get_my_submission(
        self, session: Session, assignment_public_id: UUID, student: User
    ) -> LmsSubmission | None:
        assignment = AssignmentRepository(session).get_by_public_id(assignment_public_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        return SubmissionRepository(session).get_by_student_and_assignment(
            student.id, assignment.id
        )

    # ── Grading (Teacher of the course) ──────────────────────────────────────

    def grade_submission(
        self,
        session: Session,
        submission_public_id: UUID,
        score: Decimal,
        feedback: str | None,
        teacher: User,
    ) -> LmsSubmission:
        sub_repo = SubmissionRepository(session)
        submission = sub_repo.get_by_public_id(submission_public_id)
        if submission is None:
            raise LookupError("Submission not found")

        assignment = AssignmentRepository(session).get_by_id(submission.assignment_id)
        unit = UnitRepository(session).get_by_id(assignment.unit_id)
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_teacher(course, teacher)

        if score < 0 or score > assignment.max_score:
            raise ValueError(
                f"Score must be between 0 and {assignment.max_score}"
            )

        submission = sub_repo.update(
            submission,
            LmsSubmissionUpdate(
                status=SubmissionStatus.GRADED,
                score=score,
                feedback=feedback,
                graded_by=teacher.id,
                graded_at=datetime.now(timezone.utc),
            ),
        )

        _audit.log(
            session,
            user_id=teacher.id,
            action="academic.submission.grade",
            resource_type="lms_submission",
            resource_id=str(submission.public_id),
            payload={"score": str(score), "assignment": str(assignment.public_id)},
        )
        return submission

    # ── Student course content view ──────────────────────────────────────────

    def get_student_course_content(
        self, session: Session, course_public_id: UUID, student: User
    ) -> tuple[LmsCourse, list[tuple[LmsUnit, list[LmsMaterial], list[tuple[LmsAssignment, LmsSubmission | None]]]]] | None:
        course = CourseRepository(session).get_by_public_id(course_public_id)
        if course is None:
            return None

        if not CourseStudentRepository(session).is_enrolled(course.id, student.id):
            raise PermissionError("Student is not enrolled in this course")

        units = UnitRepository(session).list_by_course(course.id, published_only=True)
        result = []
        for unit in units:
            materials = MaterialRepository(session).list_by_unit(
                unit.id, published_only=True
            )
            assignments = AssignmentRepository(session).list_by_unit(
                unit.id, published_only=True
            )
            assignment_data = []
            for a in assignments:
                sub = SubmissionRepository(session).get_by_student_and_assignment(
                    student.id, a.id
                )
                assignment_data.append((a, sub))
            result.append((unit, materials, assignment_data))

        return course, result

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _assert_teacher(course: LmsCourse, user: User) -> None:
        if course.teacher_id != user.id:
            raise PermissionError("User is not the teacher of this course")

    @staticmethod
    def _assert_admin_or_director(
        session: Session, grade: LmsGrade, user: User
    ) -> None:
        # Check if user is director of this grade
        if GradeDirectorRepository(session).is_director(grade.id, user.id):
            return
        # Otherwise, we assume the route-level authorization already checked admin
        # If not admin and not director, deny
        raise PermissionError(
            "User must be admin or director of this grade"
        )
