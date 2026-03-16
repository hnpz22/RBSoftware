from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.integrations.schemas.integration import (
    SyncRequest,
    SyncResult,
    SyncStatusResponse,
)
from app.domains.integrations.services.woocommerce_service import WooCommerceService

router = APIRouter(prefix="/integrations", tags=["integrations"])

_svc = WooCommerceService()


@router.get("/woocommerce/status", response_model=SyncStatusResponse)
def get_status(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    state = _svc.get_status(session)
    session.commit()  # persist get_or_create if it created a new row
    return SyncStatusResponse.model_validate(state)


@router.post("/woocommerce/sync", response_model=SyncResult, status_code=status.HTTP_200_OK)
def manual_sync(
    body: SyncRequest = SyncRequest(),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    try:
        return _svc.sync_orders(session, since=body.since)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"WooCommerce sync failed: {exc}",
        )


@router.post("/webhooks/woocommerce", status_code=status.HTTP_200_OK)
async def woocommerce_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Receive WooCommerce webhook payloads (order.created / order.updated).
    No auth required — payload is processed directly.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    try:
        _, action = _svc.process_wc_order_payload(session, payload)
        session.commit()
        return {"action": action}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
