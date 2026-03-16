"""RBAC domain repositories."""

from app.domains.rbac.repositories.permission_repository import PermissionRepository
from app.domains.rbac.repositories.role_permission_repository import RolePermissionRepository
from app.domains.rbac.repositories.role_repository import RoleRepository
from app.domains.rbac.repositories.user_role_repository import UserRoleRepository

__all__ = [
    "RoleRepository",
    "PermissionRepository",
    "RolePermissionRepository",
    "UserRoleRepository",
]
