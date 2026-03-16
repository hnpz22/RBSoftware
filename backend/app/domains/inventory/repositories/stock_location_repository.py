from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.inventory.models.stock_location import StockLocation
from app.domains.inventory.schemas.location import LocationCreate, LocationUpdate


class StockLocationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: LocationCreate) -> StockLocation:
        location = StockLocation.model_validate(payload)
        self.session.add(location)
        self.session.commit()
        self.session.refresh(location)
        return location

    def get_by_id(self, location_id: int) -> StockLocation | None:
        return self.session.get(StockLocation, location_id)

    def get_by_public_id(self, public_id: UUID) -> StockLocation | None:
        return self.session.exec(
            select(StockLocation).where(StockLocation.public_id == public_id)
        ).first()

    def list(self, is_active: bool | None = None) -> list[StockLocation]:
        stmt = select(StockLocation)
        if is_active is not None:
            stmt = stmt.where(StockLocation.is_active == is_active)
        return list(self.session.exec(stmt.order_by(StockLocation.id)).all())

    def update(self, location: StockLocation, payload: LocationUpdate) -> StockLocation:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(location, field, value)
        self.session.add(location)
        self.session.commit()
        self.session.refresh(location)
        return location
