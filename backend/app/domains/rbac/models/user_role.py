from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.domains.auth.models.user import User
    from app.domains.rbac.models.role import Role


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_pair"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    role_id: int = Field(
        sa_column=Column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
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

    user: "User" = Relationship()
    role: "Role" = Relationship(back_populates="user_roles")
