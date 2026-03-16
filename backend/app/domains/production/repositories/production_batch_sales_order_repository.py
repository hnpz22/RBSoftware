from __future__ import annotations

from sqlmodel import Session, select

from app.domains.production.models.production_batch_sales_order import ProductionBatchSalesOrder


class ProductionBatchSalesOrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, link: ProductionBatchSalesOrder) -> ProductionBatchSalesOrder:
        self.session.add(link)
        self.session.flush()
        self.session.refresh(link)
        return link

    def list_by_batch_id(self, batch_id: int) -> list[ProductionBatchSalesOrder]:
        return list(
            self.session.exec(
                select(ProductionBatchSalesOrder).where(
                    ProductionBatchSalesOrder.batch_id == batch_id
                )
            ).all()
        )
