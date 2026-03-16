from __future__ import annotations

from sqlmodel import Session

from app.domains.inventory.models.component_inventory_balance import (
    ComponentInventoryBalance,
    ComponentStockStatus,
)
from app.domains.inventory.models.component_inventory_movement import (
    ComponentInventoryMovement,
    ComponentMovementType,
)
from app.domains.inventory.repositories import (
    ComponentInventoryBalanceRepository,
    ComponentInventoryMovementRepository,
)
from app.domains.inventory.schemas.component_inventory import ComponentBalanceSummaryItem


class ComponentInventoryService:

    # ── Balances ──────────────────────────────────────────────────────────────

    def list_balances(
        self,
        session: Session,
        component_id: int | None = None,
        location_id: int | None = None,
    ) -> list[ComponentInventoryBalance]:
        return ComponentInventoryBalanceRepository(session).list(component_id, location_id)

    def get_summary(self, session: Session) -> list[ComponentBalanceSummaryItem]:
        rows = ComponentInventoryBalanceRepository(session).summary()
        return [
            ComponentBalanceSummaryItem(
                component_id=row[0], status=row[1], total_quantity=row[2]
            )
            for row in rows
        ]

    def check_available_global(self, session: Session, component_id: int) -> int:
        """Sum AVAILABLE quantity across all locations."""
        balances = ComponentInventoryBalanceRepository(session).list(component_id=component_id)
        return sum(b.quantity for b in balances if b.status == ComponentStockStatus.AVAILABLE)

    def check_available(
        self, session: Session, component_id: int, location_id: int
    ) -> int:
        balance = ComponentInventoryBalanceRepository(session).get_by_key(
            component_id, location_id, ComponentStockStatus.AVAILABLE
        )
        return balance.quantity if balance is not None else 0

    # ── Core business logic ───────────────────────────────────────────────────

    def adjust_balance(
        self,
        session: Session,
        *,
        component_id: int,
        location_id: int,
        status: ComponentStockStatus,
        delta: int,
        notes: str | None = None,
        performed_by: int | None = None,
    ) -> ComponentInventoryBalance:
        bal_repo = ComponentInventoryBalanceRepository(session)
        mvt_repo = ComponentInventoryMovementRepository(session)

        balance = bal_repo.get_by_key(component_id, location_id, status)
        current_qty = balance.quantity if balance is not None else 0
        new_qty = current_qty + delta

        if new_qty < 0:
            raise ValueError(
                f"Insufficient stock: available={current_qty}, requested delta={delta}"
            )

        balance = bal_repo.upsert(component_id, location_id, status, new_qty)

        movement = ComponentInventoryMovement(
            component_id=component_id,
            location_id=location_id,
            movement_type=ComponentMovementType.ADJUST,
            quantity=abs(delta),
            to_status=status.value,
            notes=notes,
            performed_by=performed_by,
        )
        mvt_repo.create(movement)

        session.commit()
        session.refresh(balance)
        return balance

    def reserve_components(
        self,
        session: Session,
        *,
        component_id: int,
        location_id: int,
        quantity: int,
        performed_by: int | None = None,
    ) -> ComponentInventoryBalance:
        """Move stock from AVAILABLE → RESERVED."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        bal_repo = ComponentInventoryBalanceRepository(session)
        mvt_repo = ComponentInventoryMovementRepository(session)

        avail = bal_repo.get_by_key(component_id, location_id, ComponentStockStatus.AVAILABLE)
        available = avail.quantity if avail is not None else 0

        if available < quantity:
            raise ValueError(
                f"Insufficient available stock: available={available}, requested={quantity}"
            )

        bal_repo.upsert(component_id, location_id, ComponentStockStatus.AVAILABLE, available - quantity)

        reserved = bal_repo.get_by_key(component_id, location_id, ComponentStockStatus.RESERVED)
        reserved_qty = reserved.quantity if reserved is not None else 0
        new_reserved = bal_repo.upsert(
            component_id, location_id, ComponentStockStatus.RESERVED, reserved_qty + quantity
        )

        movement = ComponentInventoryMovement(
            component_id=component_id,
            location_id=location_id,
            movement_type=ComponentMovementType.RESERVE,
            quantity=quantity,
            from_status=ComponentStockStatus.AVAILABLE.value,
            to_status=ComponentStockStatus.RESERVED.value,
            performed_by=performed_by,
        )
        mvt_repo.create(movement)

        session.commit()
        session.refresh(new_reserved)
        return new_reserved

    # ── Movements ─────────────────────────────────────────────────────────────

    def list_movements(
        self,
        session: Session,
        component_id: int | None = None,
        location_id: int | None = None,
    ) -> list[ComponentInventoryMovement]:
        return ComponentInventoryMovementRepository(session).list(component_id, location_id)
