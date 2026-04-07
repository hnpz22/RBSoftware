from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.training.models.training_certificate import TrainingCertificate


class CertificateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_public_id(self, public_id: UUID) -> TrainingCertificate | None:
        stmt = select(TrainingCertificate).where(
            TrainingCertificate.public_id == public_id
        )
        return self.session.exec(stmt).first()

    def get_by_enrollment(self, enrollment_id: int) -> TrainingCertificate | None:
        stmt = select(TrainingCertificate).where(
            TrainingCertificate.enrollment_id == enrollment_id
        )
        return self.session.exec(stmt).first()

    def get_by_code(self, certificate_code: str) -> TrainingCertificate | None:
        stmt = select(TrainingCertificate).where(
            TrainingCertificate.certificate_code == certificate_code
        )
        return self.session.exec(stmt).first()

    def create(self, certificate: TrainingCertificate) -> TrainingCertificate:
        self.session.add(certificate)
        self.session.commit()
        self.session.refresh(certificate)
        return certificate
