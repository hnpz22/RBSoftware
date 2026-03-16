from __future__ import annotations

from sqlmodel import Session, select

from app.domains.commercial.models.sales_order_item import SalesOrderItem


class SalesOrderItemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, item: SalesOrderItem) -> SalesOrderItem:
        self.session.add(item)
        self.session.flush()
        self.session.refresh(item)
        return item

    def list_by_order_id(self, order_id: int) -> list[SalesOrderItem]:
        return list(
            self.session.exec(
                select(SalesOrderItem)
                .where(SalesOrderItem.sales_order_id == order_id)
                .order_by(SalesOrderItem.id)
            ).all()
        )

    def save(self, item: SalesOrderItem) -> SalesOrderItem:
        self.session.add(item)
        self.session.flush()
        self.session.refresh(item)
        return item
