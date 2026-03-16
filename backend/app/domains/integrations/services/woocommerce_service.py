from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Callable

from sqlmodel import Session, select

from app.core.config import settings
from app.domains.catalog.models.product import Product
from app.domains.commercial.models.sales_order import OrderStatus, SalesOrder
from app.domains.commercial.repositories import SalesOrderItemRepository, SalesOrderRepository
from app.domains.commercial.schemas.sales_order import OrderCreate, OrderItemCreate, OrderUpdate
from app.domains.commercial.services.sales_order_service import SalesOrderService
from app.domains.integrations.models.integration_sync_state import IntegrationSyncState
from app.domains.integrations.repositories import IntegrationSyncStateRepository
from app.domains.integrations.schemas.integration import SyncResult

logger = logging.getLogger(__name__)

_INTEGRATION = "woocommerce"

_commercial = SalesOrderService()


def _wc_address(addr: dict) -> str:
    parts = [
        addr.get("address_1", ""),
        addr.get("address_2", ""),
        addr.get("city", ""),
        addr.get("state", ""),
        addr.get("postcode", ""),
        addr.get("country", ""),
    ]
    return ", ".join(p for p in parts if p)


def _parse_wc_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


class WooCommerceService:
    """Sync orders from WooCommerce into the commercial domain."""

    # Accept an optional fetch function so tests can inject a mock without HTTP.
    def __init__(
        self,
        fetch_fn: Callable[[datetime], list[dict]] | None = None,
    ) -> None:
        self._fetch_fn = fetch_fn

    # ── HTTP layer ────────────────────────────────────────────────────────────

    def _fetch_wc_orders(self, after: datetime) -> list[dict]:
        """Fetch all WC orders modified after `after`, paginating as needed."""
        if self._fetch_fn is not None:
            return self._fetch_fn(after)

        if not settings.woo_url:
            raise RuntimeError("WOO_URL is not configured")

        import httpx

        results: list[dict] = []
        page = 1
        with httpx.Client(
            auth=(settings.woo_consumer_key or "", settings.woo_consumer_secret or ""),
            timeout=30.0,
        ) as client:
            while True:
                resp = client.get(
                    f"{settings.woo_url}/wp-json/wc/v3/orders",
                    params={
                        "after": after.isoformat(),
                        "per_page": 100,
                        "page": page,
                        "status": "any",
                    },
                )
                resp.raise_for_status()
                batch: list[dict] = resp.json()
                if not batch:
                    break
                results.extend(batch)
                if len(batch) < 100:
                    break
                page += 1
        return results

    # ── Order mapping ─────────────────────────────────────────────────────────

    def _map_line_items(
        self, session: Session, wc_line_items: list[dict]
    ) -> list[OrderItemCreate] | None:
        """Map WC line items to OrderItemCreate. Returns None if any SKU is unknown."""
        mapped: list[OrderItemCreate] = []
        for li in wc_line_items:
            sku = li.get("sku") or ""
            if not sku:
                logger.warning("WC line item missing SKU, skipping order")
                return None
            product = session.exec(
                select(Product).where(Product.sku == sku, Product.is_active == True)
            ).first()
            if product is None:
                logger.warning("No active product found for SKU=%s, skipping order", sku)
                return None
            mapped.append(
                OrderItemCreate(
                    product_public_id=product.public_id,
                    quantity=int(li.get("quantity", 1)),
                    unit_price=Decimal(str(li.get("price", "0"))),
                )
            )
        return mapped if mapped else None

    def process_wc_order_payload(
        self, session: Session, wc_order: dict
    ) -> tuple[SalesOrder | None, str]:
        """
        Upsert a single WC order payload.
        Returns (order, action) where action is 'created', 'updated', or 'skipped'.
        """
        external_id = str(wc_order.get("id", ""))
        if not external_id:
            return None, "skipped"

        billing = wc_order.get("billing") or {}
        customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
        customer_email = billing.get("email") or ""

        existing = SalesOrderRepository(session).get_by_external_id(external_id)

        if existing is None:
            # Create new order
            items = self._map_line_items(session, wc_order.get("line_items") or [])
            if items is None:
                return None, "skipped"

            data = OrderCreate(
                external_id=external_id,
                source="WEB",
                customer_name=customer_name or "WooCommerce Customer",
                customer_email=customer_email,
                customer_phone=billing.get("phone"),
                shipping_address=_wc_address(wc_order.get("shipping") or {}),
                billing_address=_wc_address(billing),
                notes=wc_order.get("customer_note"),
                items=items,
            )
            order = _commercial.create_order(session, data)
            return order, "created"
        else:
            # Update only if still PENDING or UNPAID
            if existing.status not in (OrderStatus.PENDING, OrderStatus.UNPAID):
                return existing, "skipped"

            update = OrderUpdate(
                customer_name=customer_name or None,
                customer_email=customer_email or None,
                customer_phone=billing.get("phone"),
                shipping_address=_wc_address(wc_order.get("shipping") or {}),
                billing_address=_wc_address(billing),
            )
            updated = _commercial.update_order(session, existing.public_id, update)
            return updated, "updated"

    # ── sync_orders ───────────────────────────────────────────────────────────

    def sync_orders(
        self, session: Session, since: datetime | None = None
    ) -> SyncResult:
        """
        Fetch WC orders modified since `since` (or last_cursor) and upsert them.
        Updates integration_sync_state when done.
        """
        state_repo = IntegrationSyncStateRepository(session)
        state = state_repo.get_or_create(_INTEGRATION)

        # Determine fetch window
        if since is not None:
            cutoff = since
        elif state.last_cursor:
            parsed = _parse_wc_datetime(state.last_cursor)
            cutoff = parsed if parsed is not None else datetime.now(timezone.utc) - timedelta(days=30)
        else:
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        try:
            wc_orders = self._fetch_wc_orders(cutoff)
        except Exception as exc:
            state.status = "ERROR"
            state.error_message = str(exc)[:500]
            state_repo.save(state)
            session.commit()
            raise

        created = updated = skipped = 0
        for wc_order in wc_orders:
            try:
                _, action = self.process_wc_order_payload(session, wc_order)
                if action == "created":
                    created += 1
                elif action == "updated":
                    updated += 1
                else:
                    skipped += 1
            except Exception as exc:
                logger.error("Failed to process WC order %s: %s", wc_order.get("id"), exc)
                skipped += 1

        now = datetime.now(timezone.utc)
        state.last_synced_at = now
        state.last_cursor = now.strftime("%Y-%m-%dT%H:%M:%S")
        state.status = "OK"
        state.error_message = None
        state_repo.save(state)
        session.commit()

        return SyncResult(
            orders_processed=len(wc_orders),
            orders_created=created,
            orders_updated=updated,
            status="OK",
        )

    # ── status ────────────────────────────────────────────────────────────────

    def get_status(self, session: Session) -> IntegrationSyncState:
        return IntegrationSyncStateRepository(session).get_or_create(_INTEGRATION)
