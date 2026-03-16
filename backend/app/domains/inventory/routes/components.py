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
    ComponentBalanceRead,
    ComponentBalanceSummaryItem,
    ComponentManualAdjustmentCreate,
    ComponentMovementRead,
)
from app.domains.inventory.services import ComponentInventoryService

router = APIRouter(prefix="/inventory/components", tags=["inventory"])

_svc = ComponentInventoryService()


def _resolve_product(session: Session, public_id: UUID) -> Product:
    product = session.exec(select(Product).where(Product.public_id == public_id)).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
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


@router.get("/balances/summary", response_model=list[ComponentBalanceSummaryItem])
def get_component_balance_summary(
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[ComponentBalanceSummaryItem]:
    return _svc.get_summary(session)


@router.get("/balances", response_model=list[ComponentBalanceRead])
def list_component_balances(
    component_id: UUID | None = Query(default=None),
    location_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[ComponentBalanceRead]:
    comp_int_id: int | None = None
    loc_int_id: int | None = None

    if component_id is not None:
        comp_int_id = _resolve_product(session, component_id).id
    if location_id is not None:
        loc_int_id = _resolve_location(session, location_id).id

    balances = _svc.list_balances(session, comp_int_id, loc_int_id)
    return [ComponentBalanceRead.model_validate(b) for b in balances]


@router.post(
    "/movements", response_model=ComponentMovementRead, status_code=status.HTTP_201_CREATED
)
def create_component_movement(
    data: ComponentManualAdjustmentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ComponentMovementRead:
    component = _resolve_product(session, data.component_public_id)
    location = _resolve_location(session, data.location_public_id)

    try:
        _svc.adjust_balance(
            session,
            component_id=component.id,
            location_id=location.id,
            status=data.status,
            delta=data.delta,
            notes=data.notes,
            performed_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    movements = _svc.list_movements(session, component_id=component.id, location_id=location.id)
    return ComponentMovementRead.model_validate(movements[0])


@router.get("/movements", response_model=list[ComponentMovementRead])
def list_component_movements(
    component_id: UUID | None = Query(default=None),
    location_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[ComponentMovementRead]:
    comp_int_id: int | None = None
    loc_int_id: int | None = None

    if component_id is not None:
        comp_int_id = _resolve_product(session, component_id).id
    if location_id is not None:
        loc_int_id = _resolve_location(session, location_id).id

    movements = _svc.list_movements(session, comp_int_id, loc_int_id)
    return [ComponentMovementRead.model_validate(m) for m in movements]
