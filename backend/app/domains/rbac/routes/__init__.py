"""RBAC domain route scaffolds."""

from app.domains.rbac.routes.permissions import router as permissions_router
from app.domains.rbac.routes.role_permissions import router as role_permissions_router
from app.domains.rbac.routes.roles import router as roles_router
from app.domains.rbac.routes.user_roles import router as user_roles_router

__all__ = [
    "roles_router",
    "permissions_router",
    "role_permissions_router",
    "user_roles_router",
]
