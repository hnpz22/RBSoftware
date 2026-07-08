"""Visibilidad del repositorio por línea de trabajo y colegio.

El árbol de carpetas del repositorio es global, pero la visibilidad se controla
con `repository_folder_shares`. Reglas (ver feature "Repositorio LMS - Compartir
Carpetas por Linea y Colegio"):

1. Scope efectivo de una carpeta = sus shares propios; si no tiene, se hereda
   subiendo por `parent_id` hasta el ancestro más cercano con shares (override).
2. Sin shares en toda la cadena => carpeta privada (solo creador + ADMIN/SUPER_TRAINER).
3. Un usuario la ve si su conjunto de líneas/colegios intersecta el scope efectivo.
4. Usuario sin scope (sin línea ni colegio) no ve ninguna carpeta compartida.
5. ADMIN / SUPER_TRAINER ven todo (bypass).

El filtro se aplica en backend tanto en los listados como al servir el archivo
(`/view`, `/download`): ocultar solo en la UI daría falsa privacidad.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlmodel import Session, select

from app.domains.academic.models.lms_course import LmsCourse
from app.domains.academic.models.lms_course_student import LmsCourseStudent
from app.domains.academic.models.school import School, WorkLine
from app.domains.academic.models.school_teacher import SchoolTeacher
from app.domains.auth.models import User
from app.domains.rbac.repositories import UserRoleRepository
from app.domains.repository.models.repository_file import RepositoryFile
from app.domains.repository.models.repository_file_share import RepositoryFileShare
from app.domains.repository.models.repository_folder import RepositoryFolder
from app.domains.repository.models.repository_folder_share import (
    RepositoryFolderShare,
    ShareScopeType,
)

BYPASS_ROLES = {"ADMIN", "SUPER_TRAINER"}


@dataclass
class UserScopes:
    """Líneas y colegios a los que pertenece un usuario.

    `bypass=True` => ADMIN/SUPER_TRAINER, ve todo. En ese caso work_lines y
    school_ids se ignoran.
    """

    bypass: bool = False
    work_lines: set[WorkLine] = field(default_factory=set)
    school_ids: set[int] = field(default_factory=set)

    @property
    def has_any(self) -> bool:
        return self.bypass or bool(self.work_lines) or bool(self.school_ids)


def get_user_scopes(session: Session, user: User) -> UserScopes:
    """Construye el scope de un usuario.

    No existe relación directa usuario->línea/colegio: se deriva de
    `school_teachers` (docentes/trainers) y de las matrículas de curso
    (`lms_course_students` -> `lms_courses.school_id`). El work_line se toma del
    colegio asociado. ADMIN/SUPER_TRAINER hacen bypass.
    """
    roles = set(UserRoleRepository(session).get_role_names_for_user(user.id))
    if roles & BYPASS_ROLES:
        return UserScopes(bypass=True)

    school_ids: set[int] = set()

    # Colegios donde es docente/trainer.
    school_ids.update(
        session.exec(
            select(SchoolTeacher.school_id).where(SchoolTeacher.user_id == user.id)
        ).all()
    )

    # Colegios donde está matriculado como estudiante (matrícula activa).
    school_ids.update(
        session.exec(
            select(LmsCourse.school_id)
            .join(LmsCourseStudent, LmsCourseStudent.course_id == LmsCourse.id)
            .where(
                LmsCourseStudent.user_id == user.id,
                LmsCourseStudent.is_active == True,  # noqa: E712
            )
        ).all()
    )

    work_lines: set[WorkLine] = set()
    if school_ids:
        rows = session.exec(
            select(School.work_line).where(
                School.id.in_(school_ids),  # type: ignore[union-attr]
                School.work_line.is_not(None),  # type: ignore[union-attr]
            )
        ).all()
        work_lines = {wl for wl in rows if wl is not None}

    return UserScopes(bypass=False, work_lines=work_lines, school_ids=school_ids)


def folder_effective_shares(
    session: Session, folder: RepositoryFolder
) -> list[RepositoryFolderShare]:
    """Shares efectivos de una carpeta: los propios, o los del ancestro más
    cercano que tenga. Lista vacía => privada (nadie salvo dueño/admin).

    El override es "reemplaza, no suma": si una subcarpeta tiene shares propios,
    no se mira hacia arriba.
    """
    current: RepositoryFolder | None = folder
    visited: set[int] = set()
    while current is not None and current.id not in visited:
        visited.add(current.id)
        shares = session.exec(
            select(RepositoryFolderShare).where(
                RepositoryFolderShare.folder_id == current.id
            )
        ).all()
        if shares:
            return list(shares)
        current = (
            session.get(RepositoryFolder, current.parent_id)
            if current.parent_id
            else None
        )
    return []


def _scope_matches(
    shares: list[RepositoryFolderShare] | list[RepositoryFileShare],
    scopes: UserScopes,
) -> bool:
    """¿Alguno de los shares intersecta las líneas/colegios del usuario?

    Funciona para shares de carpeta o de archivo: ambos exponen
    `scope_type`, `work_line` y `school_id`.
    """
    for share in shares:
        if (
            share.scope_type == ShareScopeType.work_line
            and share.work_line is not None
            and share.work_line in scopes.work_lines
        ):
            return True
        if (
            share.scope_type == ShareScopeType.school
            and share.school_id is not None
            and share.school_id in scopes.school_ids
        ):
            return True
    return False


def can_see_folder(
    session: Session,
    folder: RepositoryFolder,
    user: User,
    scopes: UserScopes,
) -> bool:
    """¿Puede `user` (con `scopes` ya calculados) ver esta carpeta?"""
    if scopes.bypass:
        return True
    if folder.created_by is not None and folder.created_by == user.id:
        return True

    shares = folder_effective_shares(session, folder)
    if not shares:
        return False  # privada y no es el dueño

    return _scope_matches(shares, scopes)


def file_own_shares(
    session: Session, file: RepositoryFile
) -> list[RepositoryFileShare]:
    """Shares propios del archivo (sin herencia)."""
    return list(
        session.exec(
            select(RepositoryFileShare).where(RepositoryFileShare.file_id == file.id)
        ).all()
    )


def can_see_file(
    session: Session,
    file: RepositoryFile,
    user: User,
    scopes: UserScopes,
) -> bool:
    """Visibilidad de un archivo.

    Si el archivo tiene shares propios, esos REEMPLAZAN lo heredado (override):
    se decide solo por intersección de scope. Si no tiene, hereda la visibilidad
    de su carpeta vía `can_see_folder` (que incluye la rama del creador de la
    carpeta). Bypass (ADMIN/SUPER_TRAINER) y quien lo subió lo ven siempre. Un
    archivo en la raíz (`folder_id=None`) sin shares propios no tiene scope
    heredable => solo bypass / uploader.
    """
    if scopes.bypass:
        return True
    if file.uploaded_by is not None and file.uploaded_by == user.id:
        return True

    own = file_own_shares(session, file)
    if own:
        return _scope_matches(own, scopes)

    # Sin shares propios: hereda de la carpeta (incl. rama del creador).
    if file.folder_id is None:
        return False
    folder = session.get(RepositoryFolder, file.folder_id)
    if folder is None:
        return False
    return can_see_folder(session, folder, user, scopes)
