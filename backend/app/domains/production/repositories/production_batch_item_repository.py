from __future__ import annotations

from sqlmodel import Session, select

from app.domains.production.models.production_batch_item import ProductionBatchItem


class ProductionBatchItemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, item: ProductionBatchItem) -> ProductionBatchItem:
        self.session.add(item)
        self.session.flush()
        self.session.refresh(item)
        return item

    def list_by_batch_id(self, batch_id: int) -> list[ProductionBatchItem]:
        return list(
            self.session.exec(
                select(ProductionBatchItem)
                .where(ProductionBatchItem.batch_id == batch_id)
                .order_by(ProductionBatchItem.id)
            ).all()
        )

    def save(self, item: ProductionBatchItem) -> ProductionBatchItem:
        self.session.add(item)
        self.session.flush()
        self.session.refresh(item)
        return item
