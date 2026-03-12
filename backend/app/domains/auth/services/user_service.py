from __future__ import annotations

from app.domains.auth.repositories import UserRepository


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository
