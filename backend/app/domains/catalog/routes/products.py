from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.catalog.schemas import (
    KitBomItemAdd,
    KitBomItemRead,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from app.domains.catalog.services import CatalogService

router = APIRouter(prefix="/catalog/products", tags=["catalog"])

_svc = CatalogService()


# ── Products ──────────────────────────────────────────────────────────────────


@router.get("", response_model=list[ProductRead])
def list_products(
    is_active: bool | None = Query(default=True),
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[ProductRead]:
    products = _svc.list_products(session, is_active=is_active)
    return [ProductRead.model_validate(p) for p in products]


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> ProductRead:
    try:
        product = _svc.create_product(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ProductRead.model_validate(product)


@router.get("/{public_id}", response_model=ProductRead)
def get_product(
    public_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> ProductRead:
    product = _svc.get_product(session, public_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductRead.model_validate(product)


@router.patch("/{public_id}", response_model=ProductRead)
def update_product(
    public_id: UUID,
    data: ProductUpdate,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> ProductRead:
    try:
        product = _svc.update_product(session, public_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductRead.model_validate(product)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    public_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> None:
    deleted = _svc.delete_product(session, public_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


# ── BOM ───────────────────────────────────────────────────────────────────────


@router.get("/{public_id}/bom", response_model=list[KitBomItemRead])
def get_bom(
    public_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[KitBomItemRead]:
    try:
        entries = _svc.get_bom(session, public_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return [
        KitBomItemRead(
            component_public_id=component.public_id,
            component_sku=component.sku,
            component_name=component.name,
            quantity=item.quantity,
            notes=item.notes,
            created_at=item.created_at,
        )
        for item, component in entries
    ]


@router.post(
    "/{public_id}/bom",
    response_model=KitBomItemRead,
    status_code=status.HTTP_201_CREATED,
)
def add_to_bom(
    public_id: UUID,
    data: KitBomItemAdd,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> KitBomItemRead:
    try:
        item, component = _svc.add_to_bom(
            session,
            kit_public_id=public_id,
            component_public_id=data.component_id,
            quantity=data.quantity,
            notes=data.notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return KitBomItemRead(
        component_public_id=component.public_id,
        component_sku=component.sku,
        component_name=component.name,
        quantity=item.quantity,
        notes=item.notes,
        created_at=item.created_at,
    )


@router.delete(
    "/{kit_id}/bom/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_from_bom(
    kit_id: UUID,
    component_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> None:
    removed = _svc.remove_from_bom(session, kit_id, component_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM entry not found",
        )
