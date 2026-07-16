from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.core.identifiers import parse_public_id
from app.core.security import hash_password, verify_password
from app.domains.auth.models import User
from app.domains.auth.repositories import UserRepository
from app.domains.auth.schemas import SchoolBrief, UserCreate, UserRead, UserUpdate
from app.domains.rbac.repositories import UserRoleRepository
from app.domains.auth.services.refresh_token_service import RefreshTokenService


def _normalize_group(name: str) -> str:
    """Normaliza un nombre de grupo/curso para matching robusto pero exacto.

    Mayúsculas, sin tildes, espacios colapsados y recortados. NO hace fuzzy:
    meter a un estudiante en el grupo equivocado es peor que no meterlo.
    """
    import unicodedata

    stripped = unicodedata.normalize("NFKD", name or "")
    stripped = "".join(c for c in stripped if not unicodedata.combining(c))
    return " ".join(stripped.upper().split())


class UserService:
    def register(
        self,
        session: Session,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: str | None = None,
        position: str | None = None,
    ) -> User:
        repo = UserRepository(session)
        if repo.get_by_email(email) is not None:
            raise ValueError(f"Email already registered: {email}")
        return repo.create(
            UserCreate(
                email=email,
                password_hash=hash_password(password),
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                position=position,
            )
        )

    def authenticate(self, session: Session, email: str, password: str) -> User | None:
        repo = UserRepository(session)
        user = repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    def get_by_id(self, session: Session, user_id: int) -> User | None:
        return UserRepository(session).get_by_id(user_id)

    def get_by_public_id(self, session: Session, public_id: UUID) -> User | None:
        return UserRepository(session).get_by_public_id(public_id)

    def _school_affiliations_by_user(
        self, session: Session
    ) -> dict[int, list[SchoolBrief]]:
        """Colegio(s) de cada usuario, para toda la tabla de una vez.

        No existe `users.school_id`: la afiliación se deriva por tres caminos
        distintos según el rol, así que son tres queries en vez de una. La
        alternativa (`/academic/users/{id}/school-affiliation`) es una llamada
        por usuario.

        Solo cuentan las afiliaciones ACTIVAS: un estudiante al que se le dio de
        baja la matrícula (el reinicio de ciclo hace `is_active=false` en masa)
        no sigue perteneciendo a su colegio anterior. Queda sin colegio, que es
        el estado real.
        """
        # Diferido: academic importa auth, a nivel de módulo sería circular.
        from app.domains.academic.models.lms_course import LmsCourse
        from app.domains.academic.models.lms_course_student import LmsCourseStudent
        from app.domains.academic.models.lms_grade import LmsGrade
        from app.domains.academic.models.lms_grade_director import LmsGradeDirector
        from app.domains.academic.models.school import School
        from app.domains.academic.models.school_teacher import SchoolTeacher

        pairs: set[tuple[int, int]] = set()  # (user_id, school_id)

        # Docentes. OJO: school_teachers es MEMBRESÍA, no rol — trae también
        # estudiantes. No filtramos por rol acá a propósito: esto responde "a qué
        # colegio pertenece", y el rol se resuelve aparte desde user_roles.
        pairs.update(
            session.exec(select(SchoolTeacher.user_id, SchoolTeacher.school_id)).all()
        )

        # Directores: el colegio cuelga del grado.
        pairs.update(
            session.exec(
                select(LmsGradeDirector.user_id, LmsGrade.school_id)
                .join(LmsGrade, LmsGrade.id == LmsGradeDirector.grade_id)
                .where(LmsGradeDirector.is_active == True)  # noqa: E712
            ).all()
        )

        # Estudiantes: lms_courses ya tiene school_id, sin pasar por el grado.
        pairs.update(
            session.exec(
                select(LmsCourseStudent.user_id, LmsCourse.school_id)
                .join(LmsCourse, LmsCourse.id == LmsCourseStudent.course_id)
                .where(LmsCourseStudent.is_active == True)  # noqa: E712
            ).all()
        )

        schools = {
            s.id: SchoolBrief(public_id=s.public_id, name=s.name)
            for s in session.exec(select(School)).all()
        }

        by_user: dict[int, list[SchoolBrief]] = {}
        for user_id, school_id in pairs:
            school = schools.get(school_id)
            if school is None:
                continue
            by_user.setdefault(user_id, []).append(school)
        for briefs in by_user.values():
            briefs.sort(key=lambda s: s.name)
        return by_user

    def list_users(self, session: Session) -> list[UserRead]:
        users = UserRepository(session).list()
        roles_by_user = UserRoleRepository(session).get_role_names_by_user()
        schools_by_user = self._school_affiliations_by_user(session)
        return [
            UserRead.model_validate(user).model_copy(
                update={
                    "roles": roles_by_user.get(user.id, []),
                    "schools": schools_by_user.get(user.id, []),
                }
            )
            for user in users
        ]

    def update_user(
        self,
        session: Session,
        public_id: UUID,
        **kwargs,
    ) -> User | None:
        repo = UserRepository(session)
        user = repo.get_by_public_id(public_id)
        if user is None:
            return None
        return repo.update(user, UserUpdate(**kwargs))

    def change_password(
        self,
        session: Session,
        public_id: UUID,
        new_password: str,
        current_user_public_id: UUID,
    ) -> User:
        repo = UserRepository(session)
        user = repo.get_by_public_id(public_id)
        if user is None:
            raise LookupError("User not found")
        if user.public_id != current_user_public_id:
            raise PermissionError("Cannot change another user's password")
        updated = repo.update(user, UserUpdate(password_hash=hash_password(new_password)))
        RefreshTokenService().revoke_all_for_user(session, user.id)
        return updated

    def import_from_csv(
        self,
        session: Session,
        csv_bytes: bytes,
        school_public_id: str,
        requesting_user_id: int,
    ) -> dict:
        """Importa estudiantes desde un CSV `grupo;nombre;apellido;email`.

        El curso de cada estudiante se resuelve por el nombre de su `grupo`
        (normalizado) dentro del colegio. Validación todo-o-nada: si alguna
        fila tiene un problema (grupo no reconocido, campo vacío, email mal
        formado o duplicado dentro del CSV), no se escribe nada y se devuelve
        el reporte completo para corregir y reimportar.

        Idempotente: dedup de usuario por email (el SSO también matchea por
        email), `enroll` reactiva matrículas soft-deleted y la membresía al
        colegio es no-op si ya existe. Reimportar el CSV corregido es seguro.
        Los estudiantes entran por SSO; el password se autogenera y es
        irrelevante.
        """
        import csv
        import io
        import secrets
        from difflib import get_close_matches

        from sqlmodel import select

        from app.domains.academic.models.lms_course import LmsCourse
        from app.domains.academic.models.school import School
        from app.domains.academic.repositories.course_student_repository import (
            CourseStudentRepository,
        )
        from app.domains.academic.services.academic_service import AcademicService
        from app.domains.rbac.models.role import Role
        from app.domains.rbac.models.user_role import UserRole

        school_uuid = parse_public_id(school_public_id, detail="school_id inválido")

        school = session.exec(
            select(School).where(School.public_id == school_uuid)
        ).first()
        if not school:
            raise LookupError("Colegio no encontrado")

        # Índice de cursos activos del colegio por nombre normalizado.
        courses = session.exec(
            select(LmsCourse).where(
                LmsCourse.school_id == school.id,
                LmsCourse.is_active == True,  # noqa: E712
            )
        ).all()
        course_by_group = {_normalize_group(c.name): c for c in courses}
        group_keys = list(course_by_group.keys())

        # ── Parseo y decodificación ──────────────────────────────────────────
        try:
            content = csv_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                content = csv_bytes.decode("cp1252")
            except UnicodeDecodeError:
                raise ValueError(
                    "No se pudo decodificar el archivo. "
                    "Guárdalo como UTF-8 o como CSV de Excel."
                )
        first_line = content.split("\n")[0]
        delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
        try:
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        except Exception:
            raise ValueError("El archivo no es un CSV válido")

        required = {"grupo", "nombre", "apellido", "email"}
        headers = {(h or "").strip().lower() for h in (reader.fieldnames or [])}
        missing = required - headers
        if missing:
            raise ValueError(f"Faltan columnas: {', '.join(sorted(missing))}")

        # ── Validación previa todo-o-nada ────────────────────────────────────
        # Recolecta TODOS los problemas antes de escribir. Si hay alguno,
        # aborta sin tocar la BD.
        errors: list[dict] = []
        valid_rows: list[dict] = []
        seen_emails: set[str] = set()

        for i, row in enumerate(reader, start=2):
            grupo_raw = (row.get("grupo") or "").strip()
            nombre = (row.get("nombre") or "").strip()
            apellido = (row.get("apellido") or "").strip()
            email = (row.get("email") or "").strip().lower()

            if not grupo_raw or not nombre or not apellido or not email:
                errors.append(
                    {
                        "row": i,
                        "email": email or "-",
                        "error": "Fila incompleta (grupo, nombre, apellido y email son obligatorios)",
                    }
                )
                continue

            if "@" not in email or "." not in email.split("@")[-1]:
                errors.append(
                    {"row": i, "email": email, "error": "Email con formato inválido"}
                )
                continue

            if email in seen_emails:
                errors.append(
                    {"row": i, "email": email, "error": "Email duplicado dentro del archivo"}
                )
                continue
            seen_emails.add(email)

            grupo_key = _normalize_group(grupo_raw)
            course = course_by_group.get(grupo_key)
            if course is None:
                suggestion = get_close_matches(grupo_key, group_keys, n=1, cutoff=0.6)
                hint = ""
                if suggestion:
                    nombre_sugerido = course_by_group[suggestion[0]].name
                    hint = f' — ¿quisiste decir "{nombre_sugerido}"?'
                errors.append(
                    {
                        "row": i,
                        "email": email,
                        "error": f'Grupo "{grupo_raw}" no existe en el colegio{hint}',
                    }
                )
                continue

            valid_rows.append(
                {
                    "email": email,
                    "nombre": nombre,
                    "apellido": apellido,
                    "course": course,
                }
            )

        if errors:
            # Todo-o-nada: no se escribió nada.
            return {
                "aborted": True,
                "created": [],
                "reused": [],
                "enrolled": [],
                "errors": errors,
                "total_rows": len(valid_rows) + len(errors),
                "created_count": 0,
                "reused_count": 0,
                "enrolled_count": 0,
                "error_count": len(errors),
            }

        # ── Escritura (solo si todo validó) ──────────────────────────────────
        student_role = session.exec(
            select(Role).where(Role.name == "STUDENT")
        ).first()

        user_repo = UserRepository(session)
        course_student_repo = CourseStudentRepository(session)
        academic_svc = AcademicService()

        created: list[str] = []
        reused: list[str] = []
        enrolled: list[str] = []

        for entry in valid_rows:
            email = entry["email"]
            course = entry["course"]

            user = user_repo.get_by_email(email)
            if user is None:
                # Password autogenerado: el estudiante entra por SSO.
                user = user_repo.create(
                    UserCreate(
                        email=email,
                        password_hash=hash_password(secrets.token_urlsafe(32)),
                        first_name=entry["nombre"],
                        last_name=entry["apellido"],
                        phone=None,
                        position=None,
                        is_active=True,
                    )
                )
                created.append(email)
            else:
                reused.append(email)

            # Asegurar rol STUDENT sin duplicar.
            if student_role:
                has_role = session.exec(
                    select(UserRole).where(
                        UserRole.user_id == user.id,
                        UserRole.role_id == student_role.id,
                    )
                ).first()
                if has_role is None:
                    session.add(UserRole(user_id=user.id, role_id=student_role.id))
                    session.commit()

            # Membresía al colegio (no-op si ya existe) + matrícula idempotente.
            academic_svc.add_member_to_school(
                session, school.id, user.id, requesting_user_id
            )
            course_student_repo.enroll(course.id, user.id)
            enrolled.append(email)

        return {
            "aborted": False,
            "created": created,
            "reused": reused,
            "enrolled": enrolled,
            "errors": [],
            "total_rows": len(valid_rows),
            "created_count": len(created),
            "reused_count": len(reused),
            "enrolled_count": len(enrolled),
            "error_count": 0,
        }
