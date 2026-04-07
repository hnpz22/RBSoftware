from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from app.domains.academic.models.pdf_annotation import PDFAnnotation


class PDFAnnotationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_user_and_material(
        self, user_id: int, material_id: int
    ) -> PDFAnnotation | None:
        stmt = select(PDFAnnotation).where(
            PDFAnnotation.user_id == user_id,
            PDFAnnotation.material_id == material_id,
        )
        return self.session.exec(stmt).first()

    def upsert(
        self, user_id: int, material_id: int, highlights: list
    ) -> PDFAnnotation:
        now = datetime.now(timezone.utc)
        existing = self.get_by_user_and_material(user_id, material_id)
        if existing:
            existing.highlights = highlights
            existing.updated_at = now
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        annotation = PDFAnnotation(
            user_id=user_id,
            material_id=material_id,
            highlights=highlights,
        )
        self.session.add(annotation)
        self.session.commit()
        self.session.refresh(annotation)
        return annotation
