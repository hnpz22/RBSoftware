"""RBAC domain schemas."""

from app.domains.rbac.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate
from app.domains.rbac.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.domains.rbac.schemas.role_permission import (
    RolePermissionCreate,
    RolePermissionRead,
    RolePermissionUpdate,
)
from app.domains.rbac.schemas.user_role import UserRoleCreate, UserRoleRead, UserRoleUpdate

__all__ = [
    "RoleCreate",
    "RoleRead",
    "RoleUpdate",
    "PermissionCreate",
    "PermissionRead",
    "PermissionUpdate",
    "RolePermissionCreate",
    "RolePermissionRead",
    "RolePermissionUpdate",
    "UserRoleCreate",
    "UserRoleRead",
    "UserRoleUpdate",
]
