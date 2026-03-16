from __future__ import annotations

from sqlmodel import Session, select

from app.domains.integrations.models.integration_sync_state import IntegrationSyncState


class IntegrationSyncStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, integration_name: str) -> IntegrationSyncState | None:
        return self._session.exec(
            select(IntegrationSyncState).where(
                IntegrationSyncState.integration_name == integration_name
            )
        ).first()

    def get_or_create(self, integration_name: str) -> IntegrationSyncState:
        state = self.get(integration_name)
        if state is None:
            state = IntegrationSyncState(integration_name=integration_name)
            self._session.add(state)
            self._session.flush()
            self._session.refresh(state)
        return state

    def save(self, state: IntegrationSyncState) -> IntegrationSyncState:
        self._session.add(state)
        self._session.flush()
        self._session.refresh(state)
        return state
