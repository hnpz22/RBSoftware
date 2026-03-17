from __future__ import annotations

import sqlalchemy as sa
from sqlmodel import Session, select

from app.domains.inventory.models.inventory_balance import InventoryBalance, StockStatus


class InventoryBalanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_key(
        self, product_id: int, location_id: int, status: StockStatus
    ) -> InventoryBalance | None:
        return self.session.exec(
            select(InventoryBalance).where(
                InventoryBalance.product_id == product_id,
                InventoryBalance.location_id == location_id,
                InventoryBalance.status == status,
            )
        ).first()

    def upsert(
        self, product_id: int, location_id: int, status: StockStatus, quantity: int
    ) -> InventoryBalance:
        balance = self.get_by_key(product_id, location_id, status)
        if balance is None:
            balance = InventoryBalance(
                product_id=product_id,
                location_id=location_id,
                status=status,
                quantity=quantity,
            )
        else:
            balance.quantity = quantity
        self.session.add(balance)
        self.session.flush()
        return balance

    def list(
        self,
        product_id: int | None = None,
        location_id: int | None = None,
    ) -> list[InventoryBalance]:
        stmt = select(InventoryBalance)
        if product_id is not None:
            stmt = stmt.where(InventoryBalance.product_id == product_id)
        if location_id is not None:
            stmt = stmt.where(InventoryBalance.location_id == location_id)
        return list(self.session.exec(stmt.order_by(InventoryBalance.id)).all())

    def free_totals_by_product(self) -> dict[int, int]:
        """Sum FREE quantities per product_id across all locations."""
        stmt = (
            select(
                InventoryBalance.product_id,
                sa.func.sum(InventoryBalance.quantity).label("total"),
            )
            .where(InventoryBalance.status == StockStatus.FREE)
            .group_by(InventoryBalance.product_id)
        )
        return {row[0]: int(row[1]) for row in self.session.exec(stmt).all()}

    def summary(self) -> list[tuple[int, str, int]]:
        """Returns (product_id, status, total_quantity) grouped by product and status."""
        stmt = (
            select(
                InventoryBalance.product_id,
                InventoryBalance.status,
                sa.func.sum(InventoryBalance.quantity).label("total"),
            )
            .group_by(InventoryBalance.product_id, InventoryBalance.status)
            .order_by(InventoryBalance.product_id)
        )
        return list(self.session.exec(stmt).all())
