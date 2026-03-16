from __future__ import annotations

from sqlalchemy import select as sa_select
from sqlmodel import Session, select

from app.domains.catalog.models.kit_bom_item import KitBomItem
from app.domains.catalog.models.product import Product


class KitBomItemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, kit_id: int, component_id: int, quantity: int, notes: str | None) -> KitBomItem:
        item = KitBomItem(kit_id=kit_id, component_id=component_id, quantity=quantity, notes=notes)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def get_by_pair(self, kit_id: int, component_id: int) -> KitBomItem | None:
        return self.session.exec(
            select(KitBomItem)
            .where(KitBomItem.kit_id == kit_id)
            .where(KitBomItem.component_id == component_id)
        ).first()

    def list_by_kit_id(self, kit_id: int) -> list[KitBomItem]:
        return list(
            self.session.exec(
                select(KitBomItem)
                .where(KitBomItem.kit_id == kit_id)
                .order_by(KitBomItem.id)
            ).all()
        )

    def list_by_kit_id_with_components(
        self, kit_id: int
    ) -> list[tuple[KitBomItem, Product]]:
        """Returns BOM items joined with their component product in one query."""
        rows = self.session.exec(
            select(KitBomItem, Product)
            .join(Product, KitBomItem.component_id == Product.id)  # type: ignore[arg-type]
            .where(KitBomItem.kit_id == kit_id)
            .order_by(KitBomItem.id)
        ).all()
        return list(rows)

    def delete(self, item: KitBomItem) -> None:
        self.session.delete(item)
        self.session.commit()

    def count_by_kit_id(self, kit_id: int) -> int:
        return len(self.list_by_kit_id(kit_id))
