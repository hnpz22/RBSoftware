from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.domains.rbac.models.permission import Permission
    from app.domains.rbac.models.role import Role


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_pair"),
    )

    id: int | None = Field(default=None, primary_key=True)
    role_id: int = Field(
        sa_column=Column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    )
    permission_id: int = Field(
        sa_column=Column(ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )

    role: "Role" = Relationship(back_populates="role_permissions")
    permission: "Permission" = Relationship(back_populates="role_permissions")
