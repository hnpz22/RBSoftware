from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.permissions import require_roles
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.auth.repositories import UserRepository
from app.domains.training.repositories.certificate_repository import CertificateRepository
from app.domains.training.repositories.enrollment_repository import EnrollmentRepository
from app.domains.training.repositories.program_repository import ProgramRepository
from app.domains.training.schemas.training_certificate import CertificateRead
from app.domains.training.services import TrainingService

router = APIRouter(prefix="/training", tags=["training – certificates"])
_svc = TrainingService()


@router.get("/enrollments/{enrollment_id}/check")
def check_completion(
    enrollment_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("ADMIN", "TRAINER")),
):
    try:
        return _svc.check_completion(session, enrollment_id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.post(
    "/enrollments/{enrollment_id}/certificate",
    response_model=CertificateRead,
    status_code=status.HTTP_201_CREATED,
)
def issue_certificate(
    enrollment_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("ADMIN")),
):
    try:
        certificate = _svc.issue_certificate(
            session, enrollment_id, current_user.id
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return CertificateRead.model_validate(certificate)


@router.get("/certificates/{code}/verify")
def verify_certificate(
    code: str,
    session: Session = Depends(get_session),
):
    certificate = CertificateRepository(session).get_by_code(code)
    if certificate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificado no encontrado")
    program = ProgramRepository(session).get(certificate.program_id)
    user = UserRepository(session).get_by_id(certificate.user_id)
    return {
        "valid": True,
        "certificate_code": certificate.certificate_code,
        "issued_at": certificate.issued_at.isoformat(),
        "program_name": program.name if program else None,
        "holder": {
            "first_name": user.first_name if user else None,
            "last_name": user.last_name if user else None,
        },
    }


@router.get("/my-certificates", response_model=list[CertificateRead])
def get_my_certificates(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("TEACHER")),
):
    enrollments = EnrollmentRepository(session).list_by_user(current_user.id)
    cert_repo = CertificateRepository(session)
    result = []
    for enrollment in enrollments:
        cert = cert_repo.get_by_enrollment(enrollment.id)
        if cert is not None:
            result.append(CertificateRead.model_validate(cert))
    return result
