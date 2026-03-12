from __future__ import annotations

from app.domains.auth.repositories import RefreshTokenRepository


class RefreshTokenService:
    def __init__(self, repository: RefreshTokenRepository) -> None:
        self.repository = repository
