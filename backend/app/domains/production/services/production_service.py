from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.domains.catalog.models.product import Product, ProductType
from app.domains.catalog.services.catalog_service import CatalogService
from app.domains.commercial.models.sales_order import SalesOrder
from app.domains.commercial.services.sales_order_service import SalesOrderService
from app.domains.inventory.services.component_inventory_service import ComponentInventoryService
from app.domains.inventory.services.inventory_service import InventoryService
from app.domains.production.models.production_batch import (
    BatchKind,
    ProductionBatch,
    ProductionStatus,
)
from app.domains.production.models.production_batch_item import ProductionBatchItem
from app.domains.production.models.production_batch_sales_order import (
    BatchLinkMode,
    ProductionBatchSalesOrder,
)
from app.domains.production.models.production_block import ProductionBlock
from app.domains.production.repositories import (
    ProductionBatchItemRepository,
    ProductionBatchRepository,
    ProductionBatchSalesOrderRepository,
    ProductionBlockRepository,
)
from app.domains.production.schemas.batch import (
    BatchCreate,
    BatchStatusUpdate,
    BomComponentDetail,
    LinkedOrderRead,
    MasterSheetItem,
    MasterSheetResponse,
)

_catalog = CatalogService()
_inv = InventoryService()
_comp_inv = ComponentInventoryService()
_commercial = SalesOrderService()

_VALID_TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"IN_PROGRESS", "CANCELLED"},
    "IN_PROGRESS": {"DONE", "CANCELLED"},
}


class ProductionService:

    # ── Batch CRUD ─────────────────────────────────────────────────────────────

    def create_batch(
        self,
        session: Session,
        data: BatchCreate,
        created_by: int | None = None,
    ) -> ProductionBatch:
        """Manual batch creation with explicit items and optional order links."""
        batch = ProductionBatch(
            kind=data.kind,
            name=data.name,
            notes=data.notes,
            created_by=created_by,
        )
        batch_repo = ProductionBatchRepository(session)
        item_repo = ProductionBatchItemRepository(session)
        link_repo = ProductionBatchSalesOrderRepository(session)

        batch_repo.create(batch)

        for item_data in data.items:
            product = session.exec(
                select(Product).where(Product.public_id == item_data.product_public_id)
            ).first()
            if product is None:
                raise LookupError(f"Product not found: {item_data.product_public_id}")

            to_produce = max(
                0, item_data.required_qty_total - item_data.available_stock_qty
            )
            batch_item = ProductionBatchItem(
                batch_id=batch.id,
                product_id=product.id,
                required_qty_total=item_data.required_qty_total,
                available_stock_qty=item_data.available_stock_qty,
                to_produce_qty=to_produce,
                produced_qty=0,
            )
            item_repo.create(batch_item)
            self._create_blocks_for_item(session, batch_item, product)

        for order_public_id in data.sales_order_public_ids:
            order = session.exec(
                select(SalesOrder).where(SalesOrder.public_id == order_public_id)
            ).first()
            if order is not None:
                link_repo.create(
                    ProductionBatchSalesOrder(
                        batch_id=batch.id,
                        sales_order_id=order.id,
                        link_mode=BatchLinkMode.FULL,
                    )
                )

        session.commit()
        session.refresh(batch)
        return batch

    def get_batch(self, session: Session, public_id: UUID) -> ProductionBatch | None:
        return ProductionBatchRepository(session).get_by_public_id(public_id)

    def list_batches(self, session: Session) -> list[ProductionBatch]:
        return ProductionBatchRepository(session).list()

    # ── Status transitions ─────────────────────────────────────────────────────

    def update_status(
        self,
        session: Session,
        public_id: UUID,
        data: BatchStatusUpdate,
        performed_by: int | None = None,
    ) -> ProductionBatch:
        repo = ProductionBatchRepository(session)
        batch = repo.get_by_public_id(public_id)
        if batch is None:
            raise LookupError("Batch not found")

        current = str(batch.status)
        new = data.status.value
        allowed = _VALID_TRANSITIONS.get(current, set())
        if new not in allowed:
            raise ValueError(f"Cannot transition from {current} to {new}")

        now = datetime.now(timezone.utc)
        if new == "IN_PROGRESS":
            batch.started_at = now
        elif new == "DONE":
            batch.completed_at = now

        batch.status = new
        repo.save(batch)
        session.commit()
        session.refresh(batch)
        return batch

    # ── create_batch_from_orders ───────────────────────────────────────────────

    def create_batch_from_orders(
        self,
        session: Session,
        sales_order_ids: list[int],
        kind: str = "SALES",
        name: str | None = None,
        created_by: int | None = None,
    ) -> ProductionBatch:
        """
        Consolidate items from a list of APPROVED sales orders into a production batch.
        to_produce_qty = required_qty_total - available FREE stock.
        """
        if not sales_order_ids:
            raise ValueError("No order IDs provided")

        # Load all items for the provided orders
        all_items = _commercial.get_order_items_for_orders(session, sales_order_ids)
        if not all_items:
            raise ValueError("No items found in the provided orders")

        # Consolidate quantities per product
        product_qty: dict[int, int] = defaultdict(int)
        for item in all_items:
            product_qty[item.product_id] += item.quantity

        # Create the batch
        batch = ProductionBatch(
            kind=BatchKind(kind),
            name=name,
            cutoff_at=datetime.now(timezone.utc),
            created_by=created_by,
        )
        batch_repo = ProductionBatchRepository(session)
        item_repo = ProductionBatchItemRepository(session)
        link_repo = ProductionBatchSalesOrderRepository(session)

        batch_repo.create(batch)

        # Create batch items
        batch_items: list[ProductionBatchItem] = []
        for product_id, total_qty in product_qty.items():
            product = session.get(Product, product_id)
            if product is None:
                continue

            available = _inv.check_available_global(session, product_id)
            to_produce = max(0, total_qty - available)

            batch_item = ProductionBatchItem(
                batch_id=batch.id,
                product_id=product_id,
                required_qty_total=total_qty,
                available_stock_qty=available,
                to_produce_qty=to_produce,
                produced_qty=0,
            )
            item_repo.create(batch_item)
            batch_items.append(batch_item)

        # Link sales orders to batch
        for order_id in sales_order_ids:
            link_repo.create(
                ProductionBatchSalesOrder(
                    batch_id=batch.id,
                    sales_order_id=order_id,
                    link_mode=BatchLinkMode.FULL,
                )
            )

        # Create production blocks for insufficient components
        for batch_item in batch_items:
            if batch_item.to_produce_qty <= 0:
                continue
            product = session.get(Product, batch_item.product_id)
            if product is None or product.type != ProductType.KIT:
                continue
            self._create_blocks_for_item(session, batch_item, product)

        session.commit()
        session.refresh(batch)
        return batch

    # ── Cutoff ────────────────────────────────────────────────────────────────

    def cutoff(
        self,
        session: Session,
        name: str | None = None,
        created_by: int | None = None,
    ) -> ProductionBatch:
        """
        Collect all APPROVED sales orders and create an automatic SALES batch.
        """
        approved_orders = _commercial.get_approved_orders(session)
        if not approved_orders:
            raise ValueError("No APPROVED orders found for cutoff")

        order_ids = [o.id for o in approved_orders]
        return self.create_batch_from_orders(
            session,
            sales_order_ids=order_ids,
            kind="SALES",
            name=name or f"Cutoff {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            created_by=created_by,
        )

    # ── Master sheet ──────────────────────────────────────────────────────────

    def get_master_sheet(
        self, session: Session, public_id: UUID
    ) -> MasterSheetResponse:
        batch = ProductionBatchRepository(session).get_by_public_id(public_id)
        if batch is None:
            raise LookupError("Batch not found")

        batch_items = ProductionBatchItemRepository(session).list_by_batch_id(batch.id)
        links = ProductionBatchSalesOrderRepository(session).list_by_batch_id(batch.id)
        block_repo = ProductionBlockRepository(session)

        sheet_items: list[MasterSheetItem] = []
        for bi in batch_items:
            product = session.get(Product, bi.product_id)
            if product is None:
                continue

            blocks_raw = block_repo.list_by_batch_item_id(bi.id)
            from app.domains.production.schemas.batch import BlockRead

            blocks = [BlockRead.model_validate(b) for b in blocks_raw]

            # BOM details
            bom: list[BomComponentDetail] = []
            if product.type == ProductType.KIT:
                bom_entries = _catalog.get_bom_by_product_id(session, product.id)
                for bom_item, component in bom_entries:
                    needed = bom_item.quantity * bi.to_produce_qty
                    available_comp = _comp_inv.check_available_global(
                        session, component.id
                    )
                    bom.append(
                        BomComponentDetail(
                            component_id=component.id,
                            component_sku=component.sku,
                            component_name=component.name,
                            qty_per_kit=bom_item.quantity,
                            total_needed=needed,
                            available=available_comp,
                            missing=max(0, needed - available_comp),
                        )
                    )

            sheet_items.append(
                MasterSheetItem(
                    batch_item_id=bi.id,
                    product_id=product.id,
                    product_sku=product.sku,
                    product_name=product.name,
                    required_qty_total=bi.required_qty_total,
                    available_stock_qty=bi.available_stock_qty,
                    to_produce_qty=bi.to_produce_qty,
                    produced_qty=bi.produced_qty,
                    bom=bom,
                    blocks=blocks,
                )
            )

        linked_orders = [
            LinkedOrderRead(
                sales_order_id=lnk.sales_order_id,
                link_mode=str(lnk.link_mode),
            )
            for lnk in links
        ]

        return MasterSheetResponse(
            batch_public_id=batch.public_id,
            kind=str(batch.kind),
            status=str(batch.status),
            name=batch.name,
            cutoff_at=batch.cutoff_at,
            items=sheet_items,
            linked_orders=linked_orders,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _create_blocks_for_item(
        self,
        session: Session,
        batch_item: ProductionBatchItem,
        product: Product,
    ) -> None:
        """Create production blocks for any insufficient components for a KIT."""
        if product.type != ProductType.KIT or batch_item.to_produce_qty <= 0:
            return

        block_repo = ProductionBlockRepository(session)
        bom_entries = _catalog.get_bom_by_product_id(session, product.id)

        for bom_item, component in bom_entries:
            needed = bom_item.quantity * batch_item.to_produce_qty
            available_comp = _comp_inv.check_available_global(session, component.id)
            if available_comp < needed:
                block_repo.create(
                    ProductionBlock(
                        batch_item_id=batch_item.id,
                        component_id=component.id,
                        missing_qty=needed - available_comp,
                    )
                )
