from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from app.domains.inventory.models.inventory_balance import InventoryBalance, StockStatus
from app.domains.inventory.models.inventory_movement import InventoryMovement, StockMovementType
from app.domains.inventory.models.stock_location import StockLocation
from app.domains.inventory.repositories import (
    InventoryBalanceRepository,
    InventoryMovementRepository,
    StockLocationRepository,
)
from app.domains.inventory.schemas.inventory import BalanceSummaryItem, StockAlertItem
from app.domains.inventory.schemas.location import LocationCreate, LocationUpdate


# ── Stock alert thresholds (tune here or move to settings later) ───────────────
STOCK_RED_THRESHOLD = 0      # total_free == 0 → RED
STOCK_YELLOW_THRESHOLD = 10  # total_free <= 10 → YELLOW, else GREEN


class InventoryService:

    # ── Locations ─────────────────────────────────────────────────────────────

    def create_location(self, session: Session, data: LocationCreate) -> StockLocation:
        return StockLocationRepository(session).create(data)

    def get_location(self, session: Session, public_id: UUID) -> StockLocation | None:
        return StockLocationRepository(session).get_by_public_id(public_id)

    def list_locations(self, session: Session) -> list[StockLocation]:
        return StockLocationRepository(session).list()

    def update_location(
        self, session: Session, public_id: UUID, data: LocationUpdate
    ) -> StockLocation | None:
        repo = StockLocationRepository(session)
        location = repo.get_by_public_id(public_id)
        if location is None:
            return None
        return repo.update(location, data)

    # ── Balances ──────────────────────────────────────────────────────────────

    def list_balances(
        self,
        session: Session,
        product_id: int | None = None,
        location_id: int | None = None,
    ) -> list[InventoryBalance]:
        return InventoryBalanceRepository(session).list(product_id, location_id)

    def get_summary(self, session: Session) -> list[BalanceSummaryItem]:
        rows = InventoryBalanceRepository(session).summary()
        return [
            BalanceSummaryItem(product_id=row[0], status=row[1], total_quantity=row[2])
            for row in rows
        ]

    # ── Core business logic ───────────────────────────────────────────────────

    def adjust_balance(
        self,
        session: Session,
        *,
        product_id: int,
        location_id: int,
        status: StockStatus,
        delta: int,
        notes: str | None = None,
        performed_by: int | None = None,
    ) -> InventoryBalance:
        """Add or subtract stock. Creates balance row if it doesn't exist."""
        bal_repo = InventoryBalanceRepository(session)
        mvt_repo = InventoryMovementRepository(session)

        balance = bal_repo.get_by_key(product_id, location_id, status)
        current_qty = balance.quantity if balance is not None else 0
        new_qty = current_qty + delta

        if new_qty < 0:
            raise ValueError(
                f"Insufficient stock: available={current_qty}, requested delta={delta}"
            )

        balance = bal_repo.upsert(product_id, location_id, status, new_qty)

        mvt_type = StockMovementType.ADJUST
        movement = InventoryMovement(
            product_id=product_id,
            location_id=location_id,
            movement_type=mvt_type,
            quantity=abs(delta),
            to_status=status.value,
            notes=notes,
            performed_by=performed_by,
        )
        mvt_repo.create(movement)

        session.commit()
        session.refresh(balance)
        return balance

    def reserve_for_order(
        self,
        session: Session,
        *,
        product_id: int,
        location_id: int,
        quantity: int,
        order_id: int | None = None,
        performed_by: int | None = None,
    ) -> InventoryBalance:
        """Move stock from FREE → RESERVED_WEB."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        bal_repo = InventoryBalanceRepository(session)
        mvt_repo = InventoryMovementRepository(session)

        free = bal_repo.get_by_key(product_id, location_id, StockStatus.FREE)
        available = free.quantity if free is not None else 0

        if available < quantity:
            raise ValueError(
                f"Insufficient free stock: available={available}, requested={quantity}"
            )

        # Decrease FREE
        bal_repo.upsert(product_id, location_id, StockStatus.FREE, available - quantity)

        # Increase RESERVED_WEB
        reserved = bal_repo.get_by_key(product_id, location_id, StockStatus.RESERVED_WEB)
        reserved_qty = reserved.quantity if reserved is not None else 0
        new_reserved = bal_repo.upsert(
            product_id, location_id, StockStatus.RESERVED_WEB, reserved_qty + quantity
        )

        movement = InventoryMovement(
            product_id=product_id,
            location_id=location_id,
            movement_type=StockMovementType.RESERVE,
            quantity=quantity,
            from_status=StockStatus.FREE.value,
            to_status=StockStatus.RESERVED_WEB.value,
            sales_order_id=order_id,
            performed_by=performed_by,
        )
        mvt_repo.create(movement)

        session.commit()
        session.refresh(new_reserved)
        return new_reserved

    def check_available(
        self, session: Session, product_id: int, location_id: int
    ) -> int:
        """Return free quantity for a product at a location."""
        balance = InventoryBalanceRepository(session).get_by_key(
            product_id, location_id, StockStatus.FREE
        )
        return balance.quantity if balance is not None else 0

    def check_available_global(self, session: Session, product_id: int) -> int:
        """Sum FREE quantity across all locations."""
        balances = InventoryBalanceRepository(session).list(product_id=product_id)
        return sum(b.quantity for b in balances if b.status == StockStatus.FREE)

    def move_status_global(
        self,
        session: Session,
        *,
        product_id: int,
        from_status: StockStatus,
        to_status: StockStatus,
        quantity: int,
        performed_by: int | None = None,
        notes: str | None = None,
    ) -> int:
        """Move `quantity` units from_status → to_status across all locations.

        Builds a plan first (read-only), then applies deltas.
        Returns the number of units actually moved (may be < quantity if stock is short).
        """
        balances = InventoryBalanceRepository(session).list(product_id=product_id)
        sources = sorted(
            [b for b in balances if b.status == from_status.value and b.quantity > 0],
            key=lambda b: b.id,
        )
        plan: list[tuple[int, int]] = []
        remaining = quantity
        for b in sources:
            if remaining <= 0:
                break
            to_move = min(b.quantity, remaining)
            plan.append((b.location_id, to_move))
            remaining -= to_move

        for location_id, to_move in plan:
            self.adjust_balance(
                session,
                product_id=product_id,
                location_id=location_id,
                status=from_status,
                delta=-to_move,
                notes=notes,
                performed_by=performed_by,
            )
            self.adjust_balance(
                session,
                product_id=product_id,
                location_id=location_id,
                status=to_status,
                delta=to_move,
                notes=notes,
                performed_by=performed_by,
            )

        return quantity - remaining

    # ── Stock alerts ──────────────────────────────────────────────────────────

    def get_alerts(self, session: Session) -> list[StockAlertItem]:
        """Return semaphore alert per active KIT product, sorted RED→YELLOW→GREEN."""
        from sqlmodel import select as _select

        from app.domains.catalog.models.product import Product, ProductType

        free_by_product = InventoryBalanceRepository(session).free_totals_by_product()

        products = session.exec(
            _select(Product).where(
                Product.is_active == True,  # noqa: E712
                Product.type == ProductType.KIT,
            )
        ).all()

        _color_order = {"RED": 0, "YELLOW": 1, "GREEN": 2}

        alerts: list[StockAlertItem] = []
        for product in products:
            total_free = free_by_product.get(product.id, 0)
            if total_free <= STOCK_RED_THRESHOLD:
                color = "RED"
            elif total_free <= STOCK_YELLOW_THRESHOLD:
                color = "YELLOW"
            else:
                color = "GREEN"
            alerts.append(
                StockAlertItem(
                    product_id=product.id,
                    product_name=product.name,
                    sku=product.sku,
                    total_free=total_free,
                    status_color=color,
                )
            )

        alerts.sort(key=lambda a: (_color_order[a.status_color], a.sku))
        return alerts

    # ── Movements ─────────────────────────────────────────────────────────────

    def list_movements(
        self,
        session: Session,
        product_id: int | None = None,
        location_id: int | None = None,
    ) -> list[InventoryMovement]:
        return InventoryMovementRepository(session).list(product_id, location_id)
