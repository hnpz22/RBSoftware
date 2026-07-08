from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlmodel import Field, SQLModel

from app.domains.academic.models.school import WorkLine
from app.domains.repository.models.repository_folder_share import ShareScopeType


class RepositoryFileShare(SQLModel, table=True):
    """Compartición de un archivo individual del repositorio con una línea o
    un colegio.

    Espejo de `RepositoryFolderShare` a nivel de archivo. Semántica de
    **override**: si un archivo tiene shares propios, esos REEMPLAZAN el scope
    heredado de su carpeta (igual que una subcarpeta con shares propios ignora
    lo heredado); si no tiene, el archivo hereda de la carpeta. Permite tanto
    restringir un documento dentro de una carpeta amplia como compartirlo con
    un colegio que no ve la carpeta contenedora (accesible por buscador / link
    directo). Ver feature "Repositorio LMS - Compartir Carpetas por Linea y
    Colegio".
    """

    __tablename__ = "repository_file_shares"
    __table_args__ = (
        UniqueConstraint(
            "file_id",
            "scope_type",
            "work_line",
            "school_id",
            name="uq_repository_file_shares_scope",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    file_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("repository_files.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    scope_type: ShareScopeType = Field(
        sa_column=Column(
            SAEnum(ShareScopeType, values_callable=lambda x: [e.value for e in x]),
            nullable=False,
        )
    )
    # Solo uno de los dos según scope_type.
    work_line: WorkLine | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(WorkLine, values_callable=lambda x: [e.value for e in x]),
            nullable=True,
        ),
    )
    school_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    created_by: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime, nullable=False),
    )
