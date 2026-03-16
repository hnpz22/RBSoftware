from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.commercial.models.sales_order import SalesOrder


class SalesOrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, order: SalesOrder) -> SalesOrder:
        self.session.add(order)
        self.session.flush()
        self.session.refresh(order)
        return order

    def get_by_id(self, order_id: int) -> SalesOrder | None:
        return self.session.get(SalesOrder, order_id)

    def get_by_public_id(self, public_id: UUID) -> SalesOrder | None:
        return self.session.exec(
            select(SalesOrder).where(SalesOrder.public_id == public_id)
        ).first()

    def get_by_external_id(self, external_id: str) -> SalesOrder | None:
        return self.session.exec(
            select(SalesOrder).where(SalesOrder.external_id == external_id)
        ).first()

    def get_by_qr_token(self, qr_token: str) -> SalesOrder | None:
        return self.session.exec(
            select(SalesOrder).where(SalesOrder.qr_token == qr_token)
        ).first()

    def list(self) -> list[SalesOrder]:
        return list(
            self.session.exec(select(SalesOrder).order_by(SalesOrder.id.desc())).all()
        )

    def save(self, order: SalesOrder) -> SalesOrder:
        self.session.add(order)
        self.session.flush()
        self.session.refresh(order)
        return order
