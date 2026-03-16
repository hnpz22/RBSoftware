from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.fulfillment.schemas.fulfillment import (
    ConfirmComponentRequest,
    PackStatusResponse,
    ScanKitRequest,
    ScanOrderRequest,
)
from app.domains.fulfillment.services.fulfillment_service import FulfillmentService

router = APIRouter(prefix="/fulfillment", tags=["fulfillment"])

_svc = FulfillmentService()


def _order_read(order) -> dict:
    return {
        "public_id": str(order.public_id),
        "status": str(order.status),
        "fulfillment_status": str(order.fulfillment_status),
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
    }


@router.get("/orders/{public_id}/pack-status", response_model=PackStatusResponse)
def get_pack_status(
    public_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    try:
        return _svc.get_pack_status(session, public_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/scan/order", response_model=PackStatusResponse)
def scan_order(
    body: ScanOrderRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    try:
        return _svc.scan_order_qr(session, body.qr_token)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/scan/kit", response_model=dict)
def scan_kit(
    body: ScanKitRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        item = _svc.scan_kit_qr(
            session,
            body.order_public_id,
            body.product_qr,
            performed_by=current_user.id,
        )
        return item.model_dump()
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/orders/{public_id}/confirm-component", response_model=dict)
def confirm_component(
    public_id: UUID,
    body: ConfirmComponentRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        item = _svc.confirm_component(
            session,
            public_id,
            body.product_public_id,
            body.quantity,
            performed_by=current_user.id,
        )
        return item.model_dump()
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/orders/{public_id}/close-packing", response_model=dict)
def close_packing(
    public_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        order = _svc.close_packing(
            session,
            public_id,
            performed_by=current_user.id,
            ip=request.client.host if request.client else None,
        )
        return _order_read(order)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/orders/{public_id}/ship", response_model=dict)
def ship_order(
    public_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        order = _svc.ship(
            session,
            public_id,
            performed_by=current_user.id,
            ip=request.client.host if request.client else None,
        )
        return _order_read(order)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
