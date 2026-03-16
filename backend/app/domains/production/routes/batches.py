from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.production.schemas import (
    BatchCreate,
    BatchItemRead,
    BatchRead,
    BatchStatusUpdate,
    BlockRead,
    LinkedOrderRead,
    MasterSheetResponse,
)
from app.domains.production.services import ProductionService

router = APIRouter(prefix="/production/batches", tags=["production"])

_svc = ProductionService()


def _build_batch_read(svc: ProductionService, session: Session, batch) -> BatchRead:
    from app.domains.production.repositories import (
        ProductionBatchItemRepository,
        ProductionBatchSalesOrderRepository,
        ProductionBlockRepository,
    )

    items_raw = ProductionBatchItemRepository(session).list_by_batch_id(batch.id)
    links_raw = ProductionBatchSalesOrderRepository(session).list_by_batch_id(batch.id)
    block_repo = ProductionBlockRepository(session)

    items = []
    for bi in items_raw:
        blocks_raw = block_repo.list_by_batch_item_id(bi.id)
        items.append(
            BatchItemRead(
                id=bi.id,
                product_id=bi.product_id,
                required_qty_total=bi.required_qty_total,
                available_stock_qty=bi.available_stock_qty,
                to_produce_qty=bi.to_produce_qty,
                produced_qty=bi.produced_qty,
                blocks=[BlockRead.model_validate(b) for b in blocks_raw],
            )
        )

    linked = [
        LinkedOrderRead(
            sales_order_id=lnk.sales_order_id,
            link_mode=str(lnk.link_mode),
        )
        for lnk in links_raw
    ]

    return BatchRead(
        public_id=batch.public_id,
        kind=batch.kind,
        status=batch.status,
        name=batch.name,
        notes=batch.notes,
        cutoff_at=batch.cutoff_at,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=items,
        linked_orders=linked,
    )


# Register fixed-path routes BEFORE /{public_id} to avoid UUID path conflict

@router.post("/cutoff", response_model=BatchRead, status_code=status.HTTP_201_CREATED)
def cutoff(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BatchRead:
    try:
        batch = _svc.cutoff(session, created_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _build_batch_read(_svc, session, batch)


@router.get("", response_model=list[BatchRead])
def list_batches(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[BatchRead]:
    batches = _svc.list_batches(session)
    return [_build_batch_read(_svc, session, b) for b in batches]


@router.post("", response_model=BatchRead, status_code=status.HTTP_201_CREATED)
def create_batch(
    data: BatchCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BatchRead:
    try:
        batch = _svc.create_batch(session, data, created_by=current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _build_batch_read(_svc, session, batch)


@router.get("/{public_id}", response_model=BatchRead)
def get_batch(
    public_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> BatchRead:
    batch = _svc.get_batch(session, public_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return _build_batch_read(_svc, session, batch)


@router.patch("/{public_id}/status", response_model=BatchRead)
def update_batch_status(
    public_id: UUID,
    data: BatchStatusUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BatchRead:
    try:
        batch = _svc.update_status(session, public_id, data, performed_by=current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _build_batch_read(_svc, session, batch)


@router.get("/{public_id}/master-sheet", response_model=MasterSheetResponse)
def get_master_sheet(
    public_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> MasterSheetResponse:
    try:
        return _svc.get_master_sheet(session, public_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
