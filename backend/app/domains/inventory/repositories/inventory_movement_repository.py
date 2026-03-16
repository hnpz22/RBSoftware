from __future__ import annotations

from sqlmodel import Session, select

from app.domains.inventory.models.inventory_movement import InventoryMovement


class InventoryMovementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, movement: InventoryMovement) -> InventoryMovement:
        self.session.add(movement)
        self.session.flush()
        return movement

    def list(
        self,
        product_id: int | None = None,
        location_id: int | None = None,
    ) -> list[InventoryMovement]:
        stmt = select(InventoryMovement)
        if product_id is not None:
            stmt = stmt.where(InventoryMovement.product_id == product_id)
        if location_id is not None:
            stmt = stmt.where(InventoryMovement.location_id == location_id)
        return list(
            self.session.exec(stmt.order_by(InventoryMovement.id.desc())).all()
        )
