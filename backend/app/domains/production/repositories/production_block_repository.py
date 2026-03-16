from __future__ import annotations

from sqlmodel import Session, select

from app.domains.production.models.production_block import ProductionBlock


class ProductionBlockRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, block: ProductionBlock) -> ProductionBlock:
        self.session.add(block)
        self.session.flush()
        self.session.refresh(block)
        return block

    def list_by_batch_item_id(self, batch_item_id: int) -> list[ProductionBlock]:
        return list(
            self.session.exec(
                select(ProductionBlock).where(
                    ProductionBlock.batch_item_id == batch_item_id
                )
            ).all()
        )
