from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.commercial.schemas import (
    ApproveRequest,
    ApproveResult,
    OrderCreate,
    OrderItemRead,
    OrderRead,
    OrderUpdate,
)
from app.domains.commercial.services import SalesOrderService

router = APIRouter(prefix="/commercial/orders", tags=["commercial"])

_svc = SalesOrderService()


def _build_order_read(svc: SalesOrderService, session: Session, order) -> OrderRead:
    items = svc.get_order_items(session, order.id)
    return OrderRead(
        public_id=order.public_id,
        external_id=order.external_id,
        source=order.source,
        status=order.status,
        fulfillment_status=order.fulfillment_status,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,
        shipping_address=order.shipping_address,
        billing_address=order.billing_address,
        notes=order.notes,
        qr_token=order.qr_token,
        created_by_name=svc.get_creator_name(session, order.created_by),
        approved_at=order.approved_at,
        snapshot_frozen_at=order.snapshot_frozen_at,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[OrderItemRead.model_validate(i) for i in items],
    )


# Register QR route BEFORE /{public_id} to avoid UUID path conflict
@router.get("/qr/{qr_token}", response_model=OrderRead)
def get_order_by_qr(
    qr_token: str,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> OrderRead:
    order = _svc.get_order_by_qr(session, qr_token)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return _build_order_read(_svc, session, order)


@router.get("", response_model=list[OrderRead])
def list_orders(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[OrderRead]:
    orders = _svc.list_orders(session)
    return [_build_order_read(_svc, session, o) for o in orders]


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> OrderRead:
    try:
        order = _svc.create_order(session, data, created_by=current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _build_order_read(_svc, session, order)


@router.get("/{public_id}", response_model=OrderRead)
def get_order(
    public_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> OrderRead:
    order = _svc.get_order(session, public_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return _build_order_read(_svc, session, order)


@router.patch("/{public_id}", response_model=OrderRead)
def update_order(
    public_id: UUID,
    data: OrderUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> OrderRead:
    try:
        order = _svc.update_order(session, public_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return _build_order_read(_svc, session, order)


@router.post("/{public_id}/approve", response_model=ApproveResult)
def approve_order(
    public_id: UUID,
    body: ApproveRequest,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ApproveResult:
    try:
        result = _svc.approve_order(
            session,
            order_public_id=public_id,
            location_id=body.location_id,
            performed_by=current_user.id,
            ip=request.client.host if request.client else None,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return result
