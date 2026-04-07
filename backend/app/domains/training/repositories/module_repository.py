from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.domains.training.models.training_module import TrainingModule
from app.domains.training.schemas.training_module import ModuleCreate, ModuleUpdate


class ModuleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, module_id: int) -> TrainingModule | None:
        return self.session.get(TrainingModule, module_id)

    def get_by_public_id(self, public_id: UUID) -> TrainingModule | None:
        stmt = select(TrainingModule).where(TrainingModule.public_id == public_id)
        return self.session.exec(stmt).first()

    def list_by_program(
        self, program_id: int, published_only: bool = False
    ) -> list[TrainingModule]:
        stmt = select(TrainingModule).where(TrainingModule.program_id == program_id)
        if published_only:
            stmt = stmt.where(TrainingModule.is_published.is_(True))
        stmt = stmt.order_by(TrainingModule.order_index)
        return list(self.session.exec(stmt).all())

    def create(self, program_id: int, payload: ModuleCreate) -> TrainingModule:
        module = TrainingModule.model_validate(payload, update={"program_id": program_id})
        self.session.add(module)
        self.session.commit()
        self.session.refresh(module)
        return module

    def update(self, module: TrainingModule, payload: ModuleUpdate) -> TrainingModule:
        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(module, field_name, value)
        self.session.add(module)
        self.session.commit()
        self.session.refresh(module)
        return module
