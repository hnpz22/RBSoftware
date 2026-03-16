from __future__ import annotations

from sqlmodel import Session, select

from app.domains.inventory.models.component_inventory_movement import ComponentInventoryMovement


class ComponentInventoryMovementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, movement: ComponentInventoryMovement) -> ComponentInventoryMovement:
        self.session.add(movement)
        self.session.flush()
        return movement

    def list(
        self,
        component_id: int | None = None,
        location_id: int | None = None,
    ) -> list[ComponentInventoryMovement]:
        stmt = select(ComponentInventoryMovement)
        if component_id is not None:
            stmt = stmt.where(ComponentInventoryMovement.component_id == component_id)
        if location_id is not None:
            stmt = stmt.where(ComponentInventoryMovement.location_id == location_id)
        return list(
            self.session.exec(stmt.order_by(ComponentInventoryMovement.id.desc())).all()
        )
