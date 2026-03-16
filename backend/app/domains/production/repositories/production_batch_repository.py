from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.production.models.production_batch import ProductionBatch


class ProductionBatchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, batch: ProductionBatch) -> ProductionBatch:
        self.session.add(batch)
        self.session.flush()
        self.session.refresh(batch)
        return batch

    def get_by_id(self, batch_id: int) -> ProductionBatch | None:
        return self.session.get(ProductionBatch, batch_id)

    def get_by_public_id(self, public_id: UUID) -> ProductionBatch | None:
        return self.session.exec(
            select(ProductionBatch).where(ProductionBatch.public_id == public_id)
        ).first()

    def list(self) -> list[ProductionBatch]:
        return list(
            self.session.exec(
                select(ProductionBatch).order_by(ProductionBatch.id.desc())
            ).all()
        )

    def save(self, batch: ProductionBatch) -> ProductionBatch:
        self.session.add(batch)
        self.session.flush()
        self.session.refresh(batch)
        return batch
