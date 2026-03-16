from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.fulfillment.models.sales_order_pack_item import SalesOrderPackItem


class SalesOrderPackItemRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, item: SalesOrderPackItem) -> SalesOrderPackItem:
        self._session.add(item)
        self._session.flush()
        self._session.refresh(item)
        return item

    def save(self, item: SalesOrderPackItem) -> SalesOrderPackItem:
        self._session.add(item)
        self._session.flush()
        self._session.refresh(item)
        return item

    def list_by_order_id(self, order_id: int) -> list[SalesOrderPackItem]:
        return list(
            self._session.exec(
                select(SalesOrderPackItem).where(
                    SalesOrderPackItem.sales_order_id == order_id
                )
            ).all()
        )

    def get_by_order_and_product(
        self, order_id: int, product_id: int
    ) -> SalesOrderPackItem | None:
        return self._session.exec(
            select(SalesOrderPackItem).where(
                SalesOrderPackItem.sales_order_id == order_id,
                SalesOrderPackItem.product_id == product_id,
            )
        ).first()
