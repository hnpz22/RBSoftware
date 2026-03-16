from __future__ import annotations

import sqlalchemy as sa
from sqlmodel import Session, select

from app.domains.inventory.models.component_inventory_balance import (
    ComponentInventoryBalance,
    ComponentStockStatus,
)


class ComponentInventoryBalanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_key(
        self, component_id: int, location_id: int, status: ComponentStockStatus
    ) -> ComponentInventoryBalance | None:
        return self.session.exec(
            select(ComponentInventoryBalance).where(
                ComponentInventoryBalance.component_id == component_id,
                ComponentInventoryBalance.location_id == location_id,
                ComponentInventoryBalance.status == status,
            )
        ).first()

    def upsert(
        self,
        component_id: int,
        location_id: int,
        status: ComponentStockStatus,
        quantity: int,
    ) -> ComponentInventoryBalance:
        balance = self.get_by_key(component_id, location_id, status)
        if balance is None:
            balance = ComponentInventoryBalance(
                component_id=component_id,
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
        component_id: int | None = None,
        location_id: int | None = None,
    ) -> list[ComponentInventoryBalance]:
        stmt = select(ComponentInventoryBalance)
        if component_id is not None:
            stmt = stmt.where(ComponentInventoryBalance.component_id == component_id)
        if location_id is not None:
            stmt = stmt.where(ComponentInventoryBalance.location_id == location_id)
        return list(self.session.exec(stmt.order_by(ComponentInventoryBalance.id)).all())

    def summary(self) -> list[tuple[int, str, int]]:
        stmt = (
            select(
                ComponentInventoryBalance.component_id,
                ComponentInventoryBalance.status,
                sa.func.sum(ComponentInventoryBalance.quantity).label("total"),
            )
            .group_by(
                ComponentInventoryBalance.component_id, ComponentInventoryBalance.status
            )
            .order_by(ComponentInventoryBalance.component_id)
        )
        return list(self.session.exec(stmt).all())
