from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session

from app.core.database import get_session
from app.domains.academic.repositories import AssignmentRepository, SubmissionRepository
from app.domains.academic.schemas import SubmissionRead
from app.domains.academic.services import AcademicService
from app.core.permissions import require_roles
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User

router = APIRouter(prefix="/academic", tags=["academic – submissions"])
_svc = AcademicService()


class GradeBody(BaseModel):
    score: int
    feedback: str | None = None


@router.post(
    "/assignments/{assignment_id}/submit",
    response_model=SubmissionRead,
)
async def submit_assignment(
    assignment_id: UUID,
    content: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("STUDENT")),
):
    assignment = AssignmentRepository(session).get_by_public_id(assignment_id)
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    file_bytes = None
    file_name = None
    content_type = None
    if file is not None:
        file_bytes = await file.read()
        file_name = file.filename
        content_type = file.content_type
    try:
        submission = _svc.submit(
            session,
            assignment.id,
            current_user.id,
            content,
            file_bytes,
            file_name,
            content_type,
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return SubmissionRead.model_validate(submission)


@router.get(
    "/assignments/{assignment_id}/my-submission",
    response_model=SubmissionRead,
)
def get_my_submission(
    assignment_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("STUDENT")),
):
    assignment = AssignmentRepository(session).get_by_public_id(assignment_id)
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    submission = SubmissionRepository(session).get_by_student_and_assignment(
        current_user.id, assignment.id
    )
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No submission found")
    return SubmissionRead.model_validate(submission)


@router.post(
    "/submissions/{submission_id}/grade",
    status_code=status.HTTP_204_NO_CONTENT,
)
def grade_submission(
    submission_id: UUID,
    body: GradeBody,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN", "TEACHER")),
):
    submission = SubmissionRepository(session).get_by_public_id(submission_id)
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    try:
        _svc.grade_submission(
            session, submission.id, body.score, body.feedback, current_user.id
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
