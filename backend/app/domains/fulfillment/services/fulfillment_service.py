from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.audit.services.audit_service import AuditService
from app.domains.catalog.models.product import Product
from app.domains.commercial.models.sales_order import FulfillmentStatus, SalesOrder
from app.domains.commercial.models.sales_order_item import SalesOrderItem
from app.domains.commercial.services.sales_order_service import SalesOrderService
from app.domains.fulfillment.models.sales_order_pack_event import (
    PackEventType,
    SalesOrderPackEvent,
)
from app.domains.fulfillment.models.sales_order_pack_item import SalesOrderPackItem
from app.domains.fulfillment.repositories import (
    SalesOrderPackEventRepository,
    SalesOrderPackItemRepository,
)
from app.domains.fulfillment.schemas.fulfillment import (
    PackEventRead,
    PackItemRead,
    PackStatusResponse,
)
from app.domains.inventory.models.inventory_balance import StockStatus
from app.domains.inventory.services.inventory_service import InventoryService

_inv = InventoryService()
_commercial = SalesOrderService()
_audit = AuditService()


class FulfillmentService:

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_order_or_raise(self, session: Session, public_id: UUID) -> SalesOrder:
        order = _commercial.get_order(session, public_id)
        if order is None:
            raise LookupError("Order not found")
        return order

    def _ensure_pack_items(
        self, session: Session, order: SalesOrder
    ) -> list[SalesOrderPackItem]:
        """Ensure pack items exist for every order item; create if missing."""
        item_repo = SalesOrderPackItemRepository(session)
        order_items: list[SalesOrderItem] = _commercial.get_order_items(session, order.id)

        pack_items: list[SalesOrderPackItem] = []
        for oi in order_items:
            existing = item_repo.get_by_order_and_product(order.id, oi.product_id)
            if existing is None:
                existing = item_repo.create(
                    SalesOrderPackItem(
                        sales_order_id=order.id,
                        product_id=oi.product_id,
                        required_qty=oi.quantity,
                        confirmed_qty=0,
                    )
                )
            pack_items.append(existing)
        return pack_items

    # ── scan_order_qr ─────────────────────────────────────────────────────────

    def scan_order_qr(
        self, session: Session, qr_token: str
    ) -> PackStatusResponse:
        """Look up order by QR token, initialise pack items, return pack status."""
        order = _commercial.get_order_by_qr(session, qr_token)
        if order is None:
            raise LookupError("Order not found for QR token")

        pack_items = self._ensure_pack_items(session, order)
        session.commit()
        for pi in pack_items:
            session.refresh(pi)

        event_repo = SalesOrderPackEventRepository(session)
        events = event_repo.list_by_order_id(order.id)

        return PackStatusResponse(
            order_public_id=order.public_id,
            fulfillment_status=str(order.fulfillment_status),
            items=[PackItemRead.model_validate(pi) for pi in pack_items],
            events=[PackEventRead.model_validate(e) for e in events],
        )

    # ── get_pack_status ───────────────────────────────────────────────────────

    def get_pack_status(
        self, session: Session, order_public_id: UUID
    ) -> PackStatusResponse:
        order = self._get_order_or_raise(session, order_public_id)
        item_repo = SalesOrderPackItemRepository(session)
        event_repo = SalesOrderPackEventRepository(session)

        pack_items = item_repo.list_by_order_id(order.id)
        events = event_repo.list_by_order_id(order.id)

        return PackStatusResponse(
            order_public_id=order.public_id,
            fulfillment_status=str(order.fulfillment_status),
            items=[PackItemRead.model_validate(pi) for pi in pack_items],
            events=[PackEventRead.model_validate(e) for e in events],
        )

    # ── scan_kit_qr ───────────────────────────────────────────────────────────

    def scan_kit_qr(
        self,
        session: Session,
        order_public_id: UUID,
        product_qr: str,
        performed_by: int | None = None,
    ) -> PackItemRead:
        """Confirm one KIT unit by scanning its QR code."""
        order = self._get_order_or_raise(session, order_public_id)

        product = session.exec(
            select(Product).where(Product.qr_code == product_qr)
        ).first()
        if product is None:
            raise LookupError(f"Product not found for QR: {product_qr}")

        item_repo = SalesOrderPackItemRepository(session)
        pack_item = item_repo.get_by_order_and_product(order.id, product.id)
        if pack_item is None:
            raise LookupError("Product not part of this order")

        if pack_item.confirmed_qty >= pack_item.required_qty:
            raise ValueError("Already fully confirmed for this product")

        pack_item.confirmed_qty += 1
        item_repo.save(pack_item)

        event_repo = SalesOrderPackEventRepository(session)
        event_repo.create(
            SalesOrderPackEvent(
                sales_order_id=order.id,
                product_id=product.id,
                event_type=PackEventType.KIT_SCANNED.value,
                quantity=1,
                scanned_qr=product_qr,
                performed_by=performed_by,
            )
        )

        session.commit()
        session.refresh(pack_item)
        return PackItemRead.model_validate(pack_item)

    # ── confirm_component ─────────────────────────────────────────────────────

    def confirm_component(
        self,
        session: Session,
        order_public_id: UUID,
        product_public_id: UUID,
        quantity: int,
        performed_by: int | None = None,
    ) -> PackItemRead:
        """Manually confirm components for an order."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        order = self._get_order_or_raise(session, order_public_id)

        product = session.exec(
            select(Product).where(Product.public_id == product_public_id)
        ).first()
        if product is None:
            raise LookupError(f"Product not found: {product_public_id}")

        item_repo = SalesOrderPackItemRepository(session)
        pack_item = item_repo.get_by_order_and_product(order.id, product.id)
        if pack_item is None:
            raise LookupError("Product not part of this order")

        new_confirmed = pack_item.confirmed_qty + quantity
        if new_confirmed > pack_item.required_qty:
            raise ValueError(
                f"Would over-confirm: required={pack_item.required_qty}, "
                f"already={pack_item.confirmed_qty}, adding={quantity}"
            )

        pack_item.confirmed_qty = new_confirmed
        item_repo.save(pack_item)

        event_repo = SalesOrderPackEventRepository(session)
        event_repo.create(
            SalesOrderPackEvent(
                sales_order_id=order.id,
                product_id=product.id,
                event_type=PackEventType.COMPONENT_CONFIRMED.value,
                quantity=quantity,
                performed_by=performed_by,
            )
        )

        session.commit()
        session.refresh(pack_item)
        return PackItemRead.model_validate(pack_item)

    # ── close_packing ─────────────────────────────────────────────────────────

    def close_packing(
        self,
        session: Session,
        order_public_id: UUID,
        performed_by: int | None = None,
        ip: str | None = None,
    ) -> SalesOrder:
        """Validate all items confirmed, move RESERVED_WEB → PACKED, update status."""
        order = self._get_order_or_raise(session, order_public_id)

        if order.fulfillment_status == FulfillmentStatus.PACKED:
            raise ValueError("Order is already PACKED")
        if order.fulfillment_status == FulfillmentStatus.SHIPPED:
            raise ValueError("Order already SHIPPED")

        item_repo = SalesOrderPackItemRepository(session)
        pack_items = item_repo.list_by_order_id(order.id)

        if not pack_items:
            raise ValueError("No pack items found — run scan_order_qr first")

        unconfirmed = [pi for pi in pack_items if pi.confirmed_qty < pi.required_qty]
        if unconfirmed:
            detail = ", ".join(
                f"product_id={pi.product_id} ({pi.confirmed_qty}/{pi.required_qty})"
                for pi in unconfirmed
            )
            raise ValueError(f"Not all items confirmed: {detail}")

        # Move RESERVED_WEB → PACKED for each product
        order_items: list[SalesOrderItem] = _commercial.get_order_items(session, order.id)
        for oi in order_items:
            _inv.move_status_global(
                session,
                product_id=oi.product_id,
                from_status=StockStatus.RESERVED_WEB,
                to_status=StockStatus.PACKED,
                quantity=oi.quantity,
                performed_by=performed_by,
                notes=f"Packing order {order.public_id}",
            )

        # Update fulfillment status
        order = _commercial.update_fulfillment_status(
            session, order_public_id, FulfillmentStatus.PACKED.value
        )

        # Record event
        event_repo = SalesOrderPackEventRepository(session)
        event_repo.create(
            SalesOrderPackEvent(
                sales_order_id=order.id,
                event_type=PackEventType.PACK_CLOSED.value,
                performed_by=performed_by,
            )
        )
        session.commit()

        _audit.log(
            session,
            user_id=performed_by,
            action="fulfillment.order.packed",
            resource_type="sales_order",
            resource_id=str(order.public_id),
            payload={},
            ip=ip,
        )
        session.commit()

        return order

    # ── ship ──────────────────────────────────────────────────────────────────

    def ship(
        self,
        session: Session,
        order_public_id: UUID,
        performed_by: int | None = None,
        ip: str | None = None,
    ) -> SalesOrder:
        """Move PACKED → SHIPPED inventory and update fulfillment status."""
        order = self._get_order_or_raise(session, order_public_id)

        if order.fulfillment_status != FulfillmentStatus.PACKED:
            raise ValueError(
                f"Can only ship PACKED orders, current status: {order.fulfillment_status}"
            )

        order_items: list[SalesOrderItem] = _commercial.get_order_items(session, order.id)
        for oi in order_items:
            _inv.move_status_global(
                session,
                product_id=oi.product_id,
                from_status=StockStatus.PACKED,
                to_status=StockStatus.SHIPPED,
                quantity=oi.quantity,
                performed_by=performed_by,
                notes=f"Shipping order {order.public_id}",
            )

        order = _commercial.update_fulfillment_status(
            session, order_public_id, FulfillmentStatus.SHIPPED.value
        )

        _audit.log(
            session,
            user_id=performed_by,
            action="fulfillment.order.shipped",
            resource_type="sales_order",
            resource_id=str(order.public_id),
            payload={},
            ip=ip,
        )
        session.commit()

        return order
