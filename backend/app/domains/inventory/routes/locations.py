from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.inventory.schemas import LocationCreate, LocationRead, LocationUpdate
from app.domains.inventory.services import InventoryService

router = APIRouter(prefix="/inventory/locations", tags=["inventory"])

_svc = InventoryService()


@router.get("", response_model=list[LocationRead])
def list_locations(
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> list[LocationRead]:
    locations = _svc.list_locations(session)
    return [LocationRead.model_validate(loc) for loc in locations]


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(
    data: LocationCreate,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> LocationRead:
    location = _svc.create_location(session, data)
    return LocationRead.model_validate(location)


@router.get("/{public_id}", response_model=LocationRead)
def get_location(
    public_id: UUID,
    session: Session = Depends(get_session),
    _=Depends(get_current_user),
) -> LocationRead:
    location = _svc.get_location(session, public_id)
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return LocationRead.model_validate(location)
