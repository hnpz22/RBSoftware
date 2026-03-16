from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.types import Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.domains.rbac.models.role_permission import RolePermission
    from app.domains.rbac.models.user_role import UserRole


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(Uuid(as_uuid=True, native_uuid=False), nullable=False, unique=True),
    )
    name: str = Field(sa_column=Column(String(100), nullable=False, unique=True, index=True))
    description: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
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

    role_permissions: list["RolePermission"] = Relationship(back_populates="role")
    user_roles: list["UserRole"] = Relationship(back_populates="role")
