from __future__ import annotations

from sqlmodel import Session, select

from app.domains.fulfillment.models.sales_order_pack_event import SalesOrderPackEvent


class SalesOrderPackEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, event: SalesOrderPackEvent) -> SalesOrderPackEvent:
        self._session.add(event)
        self._session.flush()
        self._session.refresh(event)
        return event

    def list_by_order_id(self, order_id: int) -> list[SalesOrderPackEvent]:
        return list(
            self._session.exec(
                select(SalesOrderPackEvent).where(
                    SalesOrderPackEvent.sales_order_id == order_id
                )
            ).all()
        )
