from __future__ import annotations

import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.domains.audit.services.audit_service import AuditService
from app.domains.catalog.models.product import Product
from app.domains.commercial.models.sales_order import OrderStatus, SalesOrder
from app.domains.commercial.models.sales_order_item import SalesOrderItem
from app.domains.commercial.repositories import SalesOrderItemRepository, SalesOrderRepository
from app.domains.commercial.schemas.sales_order import (
    ApproveResult,
    OrderCreate,
    OrderUpdate,
)
from app.domains.inventory.services.inventory_service import InventoryService

_audit = AuditService()
_inv = InventoryService()


class SalesOrderService:

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def create_order(
        self, session: Session, data: OrderCreate, created_by: int | None = None
    ) -> SalesOrder:
        order_repo = SalesOrderRepository(session)
        item_repo = SalesOrderItemRepository(session)

        order = SalesOrder(
            external_id=data.external_id,
            source=data.source,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            customer_phone=data.customer_phone,
            shipping_address=data.shipping_address,
            billing_address=data.billing_address,
            notes=data.notes,
            created_by=created_by,
        )
        order_repo.create(order)

        for item_data in data.items:
            product = session.exec(
                select(Product).where(Product.public_id == item_data.product_public_id)
            ).first()
            if product is None:
                raise LookupError(
                    f"Product not found: {item_data.product_public_id}"
                )
            item = SalesOrderItem(
                sales_order_id=order.id,
                product_id=product.id,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
            )
            item_repo.create(item)

        session.commit()
        session.refresh(order)
        return order

    def get_order(self, session: Session, public_id: UUID) -> SalesOrder | None:
        return SalesOrderRepository(session).get_by_public_id(public_id)

    def get_order_by_qr(self, session: Session, qr_token: str) -> SalesOrder | None:
        return SalesOrderRepository(session).get_by_qr_token(qr_token)

    def list_orders(self, session: Session) -> list[SalesOrder]:
        return SalesOrderRepository(session).list()

    def update_order(
        self, session: Session, public_id: UUID, data: OrderUpdate
    ) -> SalesOrder | None:
        repo = SalesOrderRepository(session)
        order = repo.get_by_public_id(public_id)
        if order is None:
            return None
        if order.status != OrderStatus.PENDING:
            raise ValueError("Only PENDING orders can be updated")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(order, field, value)
        repo.save(order)
        session.commit()
        session.refresh(order)
        return order

    # ── Approve ───────────────────────────────────────────────────────────────

    def approve_order(
        self,
        session: Session,
        order_public_id: UUID,
        location_id: UUID,
        performed_by: int | None = None,
        ip: str | None = None,
    ) -> ApproveResult:
        order_repo = SalesOrderRepository(session)
        item_repo = SalesOrderItemRepository(session)

        order = order_repo.get_by_public_id(order_public_id)
        if order is None:
            raise LookupError("Order not found")
        if order.status not in (OrderStatus.PENDING, OrderStatus.UNPAID):
            raise ValueError(
                f"Cannot approve order with status {order.status}"
            )

        location = _inv.get_location(session, location_id)
        if location is None:
            raise LookupError("Location not found")

        items = item_repo.list_by_order_id(order.id)

        # Phase 1: compute reservation plan (read-only)
        plan: list[tuple[SalesOrderItem, Product, int]] = []
        for item in items:
            product = session.get(Product, item.product_id)
            if product is None:
                continue
            available = _inv.check_available(session, product.id, location.id)
            to_reserve = min(available, item.quantity)
            plan.append((item, product, to_reserve))

        # Phase 2: freeze snapshot + update order
        now = datetime.now(timezone.utc)
        for item, product, _ in plan:
            item.snapshot_name = product.name
            item.snapshot_sku = product.sku
            item_repo.save(item)

        order.status = OrderStatus.APPROVED
        order.approved_at = now
        order.snapshot_frozen_at = now
        order.qr_token = secrets.token_urlsafe(32)
        order_repo.save(order)
        session.commit()

        # Phase 3: reserve inventory (each call commits internally)
        reserved: dict[str, int] = {}
        missing: dict[str, int] = {}
        for item, product, to_reserve in plan:
            if to_reserve > 0:
                _inv.reserve_for_order(
                    session,
                    product_id=product.id,
                    location_id=location.id,
                    quantity=to_reserve,
                    order_id=order.id,
                    performed_by=performed_by,
                )
            reserved[product.sku] = to_reserve
            missing[product.sku] = item.quantity - to_reserve

        # Phase 4: audit
        session.refresh(order)
        _audit.log(
            session,
            user_id=performed_by,
            action="commercial.order.approved",
            resource_type="sales_order",
            resource_id=str(order.public_id),
            payload={"reserved": reserved, "missing": missing},
            ip=ip,
        )
        session.commit()

        return ApproveResult(
            order_public_id=order.public_id,
            qr_token=order.qr_token,
            reserved=reserved,
            missing=missing,
        )

    # ── Creator name helper ────────────────────────────────────────────────────

    def get_creator_name(self, session: Session, user_id: int | None) -> str | None:
        if user_id is None:
            return None
        from app.domains.auth.models import User  # local import to avoid circular
        user = session.get(User, user_id)
        if user is None:
            return None
        return f"{user.first_name} {user.last_name}"

    # ── Item loading helper ────────────────────────────────────────────────────

    def get_order_items(
        self, session: Session, order_id: int
    ) -> list[SalesOrderItem]:
        return SalesOrderItemRepository(session).list_by_order_id(order_id)

    def get_approved_orders(self, session: Session) -> list[SalesOrder]:
        """Return all APPROVED orders."""
        return list(
            session.exec(
                select(SalesOrder).where(SalesOrder.status == OrderStatus.APPROVED)
            ).all()
        )

    def update_fulfillment_status(
        self, session: Session, order_public_id: UUID, new_status: str
    ) -> SalesOrder | None:
        repo = SalesOrderRepository(session)
        order = repo.get_by_public_id(order_public_id)
        if order is None:
            return None
        order.fulfillment_status = new_status
        repo.save(order)
        session.commit()
        session.refresh(order)
        return order

    def get_order_items_for_orders(
        self, session: Session, order_ids: list[int]
    ) -> list[SalesOrderItem]:
        """Get all items for a list of internal order IDs."""
        if not order_ids:
            return []
        items = []
        for oid in order_ids:
            items.extend(SalesOrderItemRepository(session).list_by_order_id(oid))
        return items
