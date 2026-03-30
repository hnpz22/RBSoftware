from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Session

from app.core.storage import storage_service
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
from app.domains.academic.schemas.lms_assignment import (
    AssignmentCreate,
    AssignmentUpdate,
)
from app.domains.academic.schemas.lms_course import CourseCreate
from app.domains.academic.schemas.lms_grade import GradeCreate
from app.domains.academic.schemas.lms_material import MaterialCreate
from app.domains.academic.schemas.lms_submission import SubmissionUpdate
from app.domains.academic.schemas.lms_unit import UnitCreate
from app.domains.academic.schemas.school import SchoolCreate
from app.domains.audit.services import AuditService
from app.domains.auth.repositories import UserRepository
from app.domains.rbac.repositories import RoleRepository, UserRoleRepository

_audit = AuditService()


class AcademicService:

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _is_admin(session: Session, user_id: int) -> bool:
        user_roles = UserRoleRepository(session).list_by_user_id(user_id)
        role_repo = RoleRepository(session)
        for ur in user_roles:
            role = role_repo.get_by_id(ur.role_id)
            if role is not None and role.name.upper() == "ADMIN":
                return True
        return False

    def _assert_admin_or_director(
        self, session: Session, grade_id: int, user_id: int
    ) -> None:
        if self._is_admin(session, user_id):
            return
        if GradeDirectorRepository(session).is_director_of_grade(grade_id, user_id):
            return
        raise PermissionError("User must be admin or director of this grade")

    def _assert_admin_or_director_or_teacher(
        self, session: Session, course: LmsCourse, user_id: int
    ) -> None:
        if self._is_admin(session, user_id):
            return
        if GradeDirectorRepository(session).is_director_of_grade(
            course.grade_id, user_id
        ):
            return
        if course.teacher_id == user_id:
            return
        raise PermissionError(
            "User must be admin, director of this grade, or teacher of this course"
        )

    def _assert_admin_or_teacher(
        self, session: Session, course: LmsCourse, user_id: int
    ) -> None:
        if self._is_admin(session, user_id):
            return
        if course.teacher_id == user_id:
            return
        raise PermissionError("User must be admin or teacher of this course")

    # ── Schools ──────────────────────────────────────────────────────────────

    def create_school(self, session: Session, data: SchoolCreate) -> School:
        return SchoolRepository(session).create(data)

    # ── Grades ───────────────────────────────────────────────────────────────

    def create_grade(
        self, session: Session, school_id: int, data: GradeCreate
    ) -> LmsGrade:
        school = SchoolRepository(session).get_by_id(school_id)
        if school is None:
            raise LookupError("School not found")
        return GradeRepository(session).create(school.id, data)

    def assign_director(
        self,
        session: Session,
        grade_id: int,
        user_id: int,
        requesting_user_id: int,
    ) -> None:
        grade = GradeRepository(session).get_by_id(grade_id)
        if grade is None:
            raise LookupError("Grade not found")

        user = UserRepository(session).get_by_id(user_id)
        if user is None:
            raise LookupError("User not found")

        director_repo = GradeDirectorRepository(session)

        if director_repo.is_director_in_school(grade.school_id, user_id):
            grades = director_repo.get_grades_for_director(user_id)
            for g in grades:
                if g.school_id == grade.school_id and g.id != grade.id:
                    raise ValueError(
                        "User is already director of another grade in this school"
                    )

        current = director_repo.get_active_director(grade_id)
        if current is not None:
            director_repo.unassign(grade_id, current.id)

        director_repo.assign(grade_id, user_id)

        _audit.log(
            session,
            user_id=requesting_user_id,
            action="academic.grade.director_assigned",
            resource_type="lms_grade",
            resource_id=str(grade.id),
            payload={"director_user_id": user_id},
        )

    # ── Courses ──────────────────────────────────────────────────────────────

    def create_course(
        self,
        session: Session,
        grade_id: int,
        data: CourseCreate,
        teacher_id: int,
        requesting_user_id: int,
    ) -> LmsCourse:
        self._assert_admin_or_director(session, grade_id, requesting_user_id)

        grade = GradeRepository(session).get_by_id(grade_id)
        if grade is None:
            raise LookupError("Grade not found")

        director_grades = GradeDirectorRepository(session).get_grades_for_director(
            teacher_id
        )
        if director_grades:
            raise ValueError("Teacher cannot be a director")

        course = CourseRepository(session).create(
            grade_id, grade.school_id, teacher_id, data
        )

        _audit.log(
            session,
            user_id=requesting_user_id,
            action="academic.course.created",
            resource_type="lms_course",
            resource_id=str(course.id),
        )
        return course

    def assign_teacher(
        self,
        session: Session,
        course_id: int,
        teacher_id: int,
        requesting_user_id: int,
    ) -> LmsCourse:
        course = CourseRepository(session).get_by_id(course_id)
        if course is None:
            raise LookupError("Course not found")

        self._assert_admin_or_director(session, course.grade_id, requesting_user_id)

        director_grades = GradeDirectorRepository(session).get_grades_for_director(
            teacher_id
        )
        if director_grades:
            raise ValueError("Teacher cannot be a director")

        course = CourseRepository(session).set_teacher(course, teacher_id)

        _audit.log(
            session,
            user_id=requesting_user_id,
            action="academic.course.teacher_assigned",
            resource_type="lms_course",
            resource_id=str(course.id),
            payload={"teacher_id": teacher_id},
        )
        return course

    def enroll_student(
        self,
        session: Session,
        course_id: int,
        user_id: int,
        requesting_user_id: int,
    ) -> None:
        course = CourseRepository(session).get_by_id(course_id)
        if course is None:
            raise LookupError("Course not found")

        self._assert_admin_or_director_or_teacher(session, course, requesting_user_id)

        if course.teacher_id == user_id:
            raise ValueError("Cannot enroll the teacher of this course as a student")
        if GradeDirectorRepository(session).is_director_of_grade(
            course.grade_id, user_id
        ):
            raise ValueError("Cannot enroll a director as a student")

        cs_repo = CourseStudentRepository(session)
        if cs_repo.is_enrolled(course_id, user_id):
            raise ValueError("Already enrolled")

        cs_repo.enroll(course_id, user_id)

    def transfer_student(
        self,
        session: Session,
        student_id: int,
        from_course_id: int,
        to_course_id: int,
        requesting_user_id: int,
    ) -> None:
        from_course = CourseRepository(session).get_by_id(from_course_id)
        to_course = CourseRepository(session).get_by_id(to_course_id)
        if from_course is None or to_course is None:
            raise LookupError("Course not found")

        if from_course.grade_id != to_course.grade_id:
            raise ValueError("Both courses must belong to the same grade")

        self._assert_admin_or_director(
            session, from_course.grade_id, requesting_user_id
        )

        CourseStudentRepository(session).transfer(
            student_id, from_course_id, to_course_id
        )

        _audit.log(
            session,
            user_id=requesting_user_id,
            action="academic.student.transferred",
            resource_type="lms_course_student",
            resource_id=str(student_id),
            payload={
                "from_course_id": from_course_id,
                "to_course_id": to_course_id,
            },
        )

    # ── Content ──────────────────────────────────────────────────────────────

    def create_unit(
        self,
        session: Session,
        course_id: int,
        data: UnitCreate,
        requesting_user_id: int,
    ) -> LmsUnit:
        course = CourseRepository(session).get_by_id(course_id)
        if course is None:
            raise LookupError("Course not found")
        self._assert_admin_or_teacher(session, course, requesting_user_id)
        return UnitRepository(session).create(course_id, data)

    def add_material(
        self,
        session: Session,
        unit_id: int,
        data: MaterialCreate,
        file_bytes: bytes | None,
        content_type: str | None,
        requesting_user_id: int,
    ) -> LmsMaterial:
        unit = UnitRepository(session).get_by_id(unit_id)
        if unit is None:
            raise LookupError("Unit not found")
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_admin_or_teacher(session, course, requesting_user_id)

        file_key = None
        if data.type == "PDF" and file_bytes is not None:
            file_key = f"academic/{course.id}/materials/{uuid4()}.pdf"
            storage_service.upload_file(
                file_bytes, file_key, content_type or "application/pdf"
            )

        return MaterialRepository(session).create(unit_id, data, file_key=file_key)

    def delete_material(
        self,
        session: Session,
        material_id: int,
        requesting_user_id: int,
    ) -> None:
        repo = MaterialRepository(session)
        material = repo.get_by_id(material_id)
        if material is None:
            raise LookupError("Material not found")
        unit = UnitRepository(session).get_by_id(material.unit_id)
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_admin_or_teacher(session, course, requesting_user_id)

        if material.file_key:
            storage_service.delete_file(material.file_key)

        repo.delete(material)

    def publish_unit(
        self,
        session: Session,
        unit_id: int,
        requesting_user_id: int,
        publish: bool = True,
    ) -> LmsUnit:
        repo = UnitRepository(session)
        unit = repo.get_by_id(unit_id)
        if unit is None:
            raise LookupError("Unit not found")
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_admin_or_teacher(session, course, requesting_user_id)
        if publish:
            return repo.publish(unit)
        return repo.unpublish(unit)

    def create_assignment(
        self,
        session: Session,
        unit_id: int,
        data: AssignmentCreate,
        requesting_user_id: int,
    ) -> LmsAssignment:
        unit = UnitRepository(session).get_by_id(unit_id)
        if unit is None:
            raise LookupError("Unit not found")
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_admin_or_teacher(session, course, requesting_user_id)
        return AssignmentRepository(session).create(unit_id, data)

    def publish_assignment(
        self,
        session: Session,
        assignment_id: int,
        requesting_user_id: int,
        publish: bool = True,
    ) -> LmsAssignment:
        repo = AssignmentRepository(session)
        assignment = repo.get_by_id(assignment_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        unit = UnitRepository(session).get_by_id(assignment.unit_id)
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_admin_or_teacher(session, course, requesting_user_id)
        return repo.update(assignment, AssignmentUpdate(is_published=publish))

    # ── Submissions ──────────────────────────────────────────────────────────

    def submit(
        self,
        session: Session,
        assignment_id: int,
        student_id: int,
        content: str | None,
        file_bytes: bytes | None,
        file_name: str | None,
        content_type: str | None,
    ) -> LmsSubmission:
        assignment = AssignmentRepository(session).get_by_id(assignment_id)
        if assignment is None:
            raise LookupError("Assignment not found")

        if not assignment.is_published:
            raise ValueError("Assignment not published")

        unit = UnitRepository(session).get_by_id(assignment.unit_id)
        course = CourseRepository(session).get_by_id(unit.course_id)

        if not CourseStudentRepository(session).is_enrolled(course.id, student_id):
            raise PermissionError("Student is not enrolled in this course")

        file_key = None
        if file_bytes is not None and file_name is not None:
            ext = file_name.rsplit(".", 1)[-1]
            key = (
                f"academic/{course.id}/submissions"
                f"/{assignment_id}/{student_id}/{uuid4()}.{ext}"
            )
            storage_service.upload_file(
                file_bytes, key, content_type or "application/octet-stream"
            )
            file_key = key

        return SubmissionRepository(session).upsert(
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            file_key=file_key,
            file_name=file_name,
        )

    # ── Grading ──────────────────────────────────────────────────────────────

    def grade_submission(
        self,
        session: Session,
        submission_id: int,
        score: int,
        feedback: str | None,
        teacher_id: int,
    ) -> LmsSubmission:
        sub_repo = SubmissionRepository(session)
        submission = sub_repo.get_by_id(submission_id)
        if submission is None:
            raise LookupError("Submission not found")

        assignment = AssignmentRepository(session).get_by_id(submission.assignment_id)
        unit = UnitRepository(session).get_by_id(assignment.unit_id)
        course = CourseRepository(session).get_by_id(unit.course_id)
        self._assert_admin_or_teacher(session, course, teacher_id)

        if score < 0 or score > assignment.max_score:
            raise ValueError(
                f"Score must be between 0 and {assignment.max_score}"
            )

        submission = sub_repo.update(
            submission,
            SubmissionUpdate(
                status=SubmissionStatus.GRADED,
                score=score,
                feedback=feedback,
                graded_by=teacher_id,
                graded_at=datetime.now(timezone.utc),
            ),
        )

        _audit.log(
            session,
            user_id=teacher_id,
            action="academic.submission.graded",
            resource_type="lms_submission",
            resource_id=str(submission.id),
            payload={"score": score, "assignment_id": assignment.id},
        )
        return submission

    # ── Queries ──────────────────────────────────────────────────────────────

    def get_my_courses_as_teacher(
        self, session: Session, user_id: int
    ) -> list[LmsCourse]:
        if self._is_admin(session, user_id):
            return CourseRepository(session).list_all_active()
        director_grades = GradeDirectorRepository(session).get_grades_for_director(
            user_id
        )
        if director_grades:
            grade_ids = [g.id for g in director_grades]
            return CourseRepository(session).list_by_grade_ids(grade_ids)
        return CourseRepository(session).list_by_teacher(user_id)

    def get_my_courses_as_student(
        self, session: Session, user_id: int
    ) -> list[LmsCourse]:
        if self._is_admin(session, user_id):
            return []
        return CourseStudentRepository(session).get_courses_for_student(user_id)

    def get_my_grades_as_director(
        self, session: Session, user_id: int
    ) -> list[LmsGrade]:
        if self._is_admin(session, user_id):
            return GradeRepository(session).list_all_active()
        return GradeDirectorRepository(session).get_grades_for_director(user_id)

    def get_course_content(
        self,
        session: Session,
        course_id: int,
        requesting_user_id: int,
    ) -> tuple[
        LmsCourse,
        list[
            tuple[
                LmsUnit,
                list[LmsMaterial],
                list[tuple[LmsAssignment, LmsSubmission | None]],
            ]
        ],
    ]:
        course = CourseRepository(session).get_by_id(course_id)
        if course is None:
            raise LookupError("Course not found")

        is_admin = self._is_admin(session, requesting_user_id)
        is_teacher = course.teacher_id == requesting_user_id
        is_director = GradeDirectorRepository(session).is_director_of_grade(
            course.grade_id, requesting_user_id
        )
        is_student = CourseStudentRepository(session).is_enrolled(
            course_id, requesting_user_id
        )

        if not (is_admin or is_teacher or is_director or is_student):
            raise PermissionError(
                "User must be admin, teacher, director, or enrolled student"
            )

        # Teacher/admin see everything (drafts included); others only published
        published_only = not (is_admin or is_teacher)

        units = UnitRepository(session).list_by_course(
            course_id, published_only=published_only
        )
        result: list[
            tuple[
                LmsUnit,
                list[LmsMaterial],
                list[tuple[LmsAssignment, LmsSubmission | None]],
            ]
        ] = []
        for unit in units:
            materials = MaterialRepository(session).list_by_unit(
                unit.id, published_only=published_only
            )
            assignments = AssignmentRepository(session).list_by_unit(
                unit.id, published_only=published_only
            )
            assignment_data: list[tuple[LmsAssignment, LmsSubmission | None]] = []
            for a in assignments:
                sub = None
                if is_student:
                    sub = SubmissionRepository(session).get_by_student_and_assignment(
                        requesting_user_id, a.id
                    )
                assignment_data.append((a, sub))
            result.append((unit, materials, assignment_data))

        return course, result
