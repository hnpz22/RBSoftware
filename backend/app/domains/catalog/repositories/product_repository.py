from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.catalog.models.product import Product, ProductType
from app.domains.catalog.schemas.product import ProductCreate, ProductUpdate


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: ProductCreate) -> Product:
        product = Product.model_validate(payload)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def get_by_id(self, product_id: int) -> Product | None:
        return self.session.get(Product, product_id)

    def get_by_public_id(self, public_id: UUID) -> Product | None:
        return self.session.exec(
            select(Product).where(Product.public_id == public_id)
        ).first()

    def get_by_sku(self, sku: str) -> Product | None:
        return self.session.exec(
            select(Product).where(Product.sku == sku)
        ).first()

    def list(self, is_active: bool | None = True) -> list[Product]:
        stmt = select(Product)
        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)
        stmt = stmt.order_by(Product.id)
        return list(self.session.exec(stmt).all())

    def update(self, product: Product, payload: ProductUpdate) -> Product:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(product, field_name, value)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def soft_delete(self, product: Product) -> Product:
        product.is_active = False
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product
