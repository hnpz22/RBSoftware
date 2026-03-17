from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.catalog.models.product import Product
from app.domains.inventory.models.stock_location import StockLocation
from app.domains.inventory.schemas import (
    BalanceRead,
    BalanceSummaryItem,
    ManualAdjustmentCreate,
    MovementRead,
    StockAlertItem,
)
from app.domains.inventory.services import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])

_svc = InventoryService()


def _resolve_product(session: Session, public_id: UUID) -> Product:
    product = session.exec(select(Product).where(Product.public_id == public_id)).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def _resolve_location(session: Session, public_id: UUID) -> StockLocation:
    location = session.exec(
        select(StockLocation).where(StockLocation.public_id == public_id)
    ).first()
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )
    return location


@router.get("/alerts", response_model=list[StockAlertItem])
def get_stock_alerts(
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[StockAlertItem]:
    return _svc.get_alerts(session)


@router.get("/balances/summary", response_model=list[BalanceSummaryItem])
def get_balance_summary(
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[BalanceSummaryItem]:
    return _svc.get_summary(session)


@router.get("/balances", response_model=list[BalanceRead])
def list_balances(
    product_id: UUID | None = Query(default=None),
    location_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[BalanceRead]:
    product_int_id: int | None = None
    location_int_id: int | None = None

    if product_id is not None:
        product_int_id = _resolve_product(session, product_id).id
    if location_id is not None:
        location_int_id = _resolve_location(session, location_id).id

    balances = _svc.list_balances(session, product_int_id, location_int_id)
    return [BalanceRead.model_validate(b) for b in balances]


@router.post("/movements", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
def create_movement(
    data: ManualAdjustmentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MovementRead:
    product = _resolve_product(session, data.product_public_id)
    location = _resolve_location(session, data.location_public_id)

    try:
        balance = _svc.adjust_balance(
            session,
            product_id=product.id,
            location_id=location.id,
            status=data.status,
            delta=data.delta,
            notes=data.notes,
            performed_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # Return the generated movement (latest for this product/location)
    movements = _svc.list_movements(session, product_id=product.id, location_id=location.id)
    return MovementRead.model_validate(movements[0])


@router.get("/movements", response_model=list[MovementRead])
def list_movements(
    product_id: UUID | None = Query(default=None),
    location_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[MovementRead]:
    product_int_id: int | None = None
    location_int_id: int | None = None

    if product_id is not None:
        product_int_id = _resolve_product(session, product_id).id
    if location_id is not None:
        location_int_id = _resolve_location(session, location_id).id

    movements = _svc.list_movements(session, product_int_id, location_int_id)
    return [MovementRead.model_validate(m) for m in movements]
