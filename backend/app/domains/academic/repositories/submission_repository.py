from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.domains.academic.models.lms_assignment import LmsAssignment
from app.domains.academic.models.lms_submission import LmsSubmission, SubmissionStatus
from app.domains.academic.models.lms_unit import LmsUnit
from app.domains.academic.schemas.lms_submission import SubmissionUpdate
from app.domains.auth.models import User


class SubmissionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, submission_id: int) -> LmsSubmission | None:
        return self.session.get(LmsSubmission, submission_id)

    def get_by_public_id(self, public_id: UUID) -> LmsSubmission | None:
        stmt = select(LmsSubmission).where(LmsSubmission.public_id == public_id)
        return self.session.exec(stmt).first()

    def upsert(
        self,
        assignment_id: int,
        student_id: int,
        content: str | None = None,
        file_key: str | None = None,
        file_name: str | None = None,
    ) -> LmsSubmission:
        existing = self.get_by_student_and_assignment(student_id, assignment_id)
        if existing is not None:
            if content is not None:
                existing.content = content
            if file_key is not None:
                existing.file_key = file_key
                existing.file_name = file_name
            existing.status = SubmissionStatus.SUBMITTED
            existing.submitted_at = datetime.now(timezone.utc)
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        submission = LmsSubmission(
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            file_key=file_key,
            file_name=file_name,
            status=SubmissionStatus.SUBMITTED,
            submitted_at=datetime.now(timezone.utc),
        )
        self.session.add(submission)
        self.session.commit()
        self.session.refresh(submission)
        return submission

    def get_by_assignment(
        self, assignment_id: int
    ) -> list[tuple[LmsSubmission, User]]:
        stmt = (
            select(LmsSubmission, User)
            .join(User, User.id == LmsSubmission.student_id)
            .where(LmsSubmission.assignment_id == assignment_id)
            .order_by(User.last_name, User.first_name)
        )
        return list(self.session.exec(stmt).all())

    def get_by_student_and_assignment(
        self, student_id: int, assignment_id: int
    ) -> LmsSubmission | None:
        stmt = select(LmsSubmission).where(
            LmsSubmission.student_id == student_id,
            LmsSubmission.assignment_id == assignment_id,
        )
        return self.session.exec(stmt).first()

    def get_pending_for_course(self, course_id: int) -> list[tuple[LmsSubmission, User]]:
        stmt = (
            select(LmsSubmission, User)
            .join(LmsAssignment, LmsAssignment.id == LmsSubmission.assignment_id)
            .join(LmsUnit, LmsUnit.id == LmsAssignment.unit_id)
            .join(User, User.id == LmsSubmission.student_id)
            .where(
                LmsUnit.course_id == course_id,
                LmsSubmission.status == SubmissionStatus.SUBMITTED,
            )
            .order_by(LmsSubmission.submitted_at)
        )
        return list(self.session.exec(stmt).all())

    def get_progress(
        self, student_id: int, course_id: int
    ) -> dict[int, LmsSubmission | None]:
        assignments_stmt = (
            select(LmsAssignment)
            .join(LmsUnit, LmsUnit.id == LmsAssignment.unit_id)
            .where(LmsUnit.course_id == course_id)
        )
        assignments = list(self.session.exec(assignments_stmt).all())

        submissions_stmt = (
            select(LmsSubmission)
            .join(LmsAssignment, LmsAssignment.id == LmsSubmission.assignment_id)
            .join(LmsUnit, LmsUnit.id == LmsAssignment.unit_id)
            .where(
                LmsSubmission.student_id == student_id,
                LmsUnit.course_id == course_id,
            )
        )
        submissions = list(self.session.exec(submissions_stmt).all())
        sub_map = {s.assignment_id: s for s in submissions}

        return {a.id: sub_map.get(a.id) for a in assignments}

    def update(
        self, submission: LmsSubmission, payload: SubmissionUpdate
    ) -> LmsSubmission:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(submission, field_name, value)
        self.session.add(submission)
        self.session.commit()
        self.session.refresh(submission)
        return submission
