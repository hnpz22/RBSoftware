"""AUTH domain route scaffolds."""

from app.domains.auth.routes.refresh_tokens import router as refresh_tokens_router
from app.domains.auth.routes.users import router as users_router

__all__ = ["users_router", "refresh_tokens_router"]
