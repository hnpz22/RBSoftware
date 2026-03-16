from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from app.domains.catalog.models.kit_bom_item import KitBomItem
from app.domains.catalog.models.product import Product, ProductType
from app.domains.catalog.repositories import KitBomItemRepository, ProductRepository
from app.domains.catalog.schemas.product import ProductCreate, ProductUpdate


class CatalogService:

    # ── Products ──────────────────────────────────────────────────────────────

    def create_product(self, session: Session, data: ProductCreate) -> Product:
        repo = ProductRepository(session)
        if repo.get_by_sku(data.sku) is not None:
            raise ValueError(f"SKU already exists: {data.sku}")
        self._validate_type_rules(data.type, data.cut_file_key)
        return repo.create(data)

    def get_product(self, session: Session, public_id: UUID) -> Product | None:
        return ProductRepository(session).get_by_public_id(public_id)

    def list_products(self, session: Session, is_active: bool | None = True) -> list[Product]:
        return ProductRepository(session).list(is_active=is_active)

    def update_product(
        self, session: Session, public_id: UUID, data: ProductUpdate
    ) -> Product | None:
        repo = ProductRepository(session)
        product = repo.get_by_public_id(public_id)
        if product is None:
            return None

        # Determine the effective type after update
        new_type = data.type if data.type is not None else product.type
        new_cut_file_key = data.cut_file_key if "cut_file_key" in data.model_fields_set else product.cut_file_key

        self._validate_type_rules(new_type, new_cut_file_key)

        # Changing KIT → COMPONENT while BOM items exist is not allowed
        if product.type == ProductType.KIT and new_type == ProductType.COMPONENT:
            if KitBomItemRepository(session).count_by_kit_id(product.id) > 0:
                raise ValueError(
                    "Cannot change type to COMPONENT: kit has existing BOM items"
                )

        # SKU uniqueness check on update
        if data.sku is not None and data.sku != product.sku:
            if repo.get_by_sku(data.sku) is not None:
                raise ValueError(f"SKU already exists: {data.sku}")

        return repo.update(product, data)

    def delete_product(self, session: Session, public_id: UUID) -> bool:
        repo = ProductRepository(session)
        product = repo.get_by_public_id(public_id)
        if product is None:
            return False
        repo.soft_delete(product)
        return True

    # ── BOM ───────────────────────────────────────────────────────────────────

    def get_bom(
        self, session: Session, kit_public_id: UUID
    ) -> list[tuple[KitBomItem, Product]]:
        kit = ProductRepository(session).get_by_public_id(kit_public_id)
        if kit is None:
            raise LookupError("Product not found")
        if kit.type != ProductType.KIT:
            raise ValueError("Product is not a KIT")
        return KitBomItemRepository(session).list_by_kit_id_with_components(kit.id)

    def add_to_bom(
        self,
        session: Session,
        kit_public_id: UUID,
        component_public_id: UUID,
        quantity: int,
        notes: str | None = None,
    ) -> tuple[KitBomItem, Product]:
        prod_repo = ProductRepository(session)
        kit = prod_repo.get_by_public_id(kit_public_id)
        if kit is None:
            raise LookupError("Kit not found")
        if kit.type != ProductType.KIT:
            raise ValueError("Product is not a KIT")

        component = prod_repo.get_by_public_id(component_public_id)
        if component is None:
            raise LookupError("Component not found")
        if component.type != ProductType.COMPONENT:
            raise ValueError("Target product is not a COMPONENT")

        if kit.id == component.id:
            raise ValueError("A kit cannot be a component of itself")

        bom_repo = KitBomItemRepository(session)
        if bom_repo.get_by_pair(kit.id, component.id) is not None:
            raise ValueError("Component is already in this kit's BOM")

        item = bom_repo.create(kit.id, component.id, quantity, notes)
        return item, component

    def remove_from_bom(
        self,
        session: Session,
        kit_public_id: UUID,
        component_public_id: UUID,
    ) -> bool:
        prod_repo = ProductRepository(session)
        kit = prod_repo.get_by_public_id(kit_public_id)
        if kit is None or kit.type != ProductType.KIT:
            return False

        component = prod_repo.get_by_public_id(component_public_id)
        if component is None:
            return False

        bom_repo = KitBomItemRepository(session)
        item = bom_repo.get_by_pair(kit.id, component.id)
        if item is None:
            return False

        bom_repo.delete(item)
        return True

    def get_bom_by_product_id(
        self, session: Session, product_id: int
    ) -> list[tuple[KitBomItem, Product]]:
        """Return BOM entries (item, component) for a kit identified by internal id."""
        return KitBomItemRepository(session).list_by_kit_id_with_components(product_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _validate_type_rules(product_type: ProductType, cut_file_key: str | None) -> None:
        if product_type == ProductType.KIT and cut_file_key is not None:
            raise ValueError("cut_file_key is only valid for COMPONENT products")
