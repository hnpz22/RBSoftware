#!/usr/bin/env python3
"""
Seed inicial de datos.
Idempotente: no falla ni duplica si los datos ya existen.

Uso dentro del contenedor:
    python scripts/seed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que el directorio del backend está en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.domains.auth.models import User
from app.domains.auth.services.user_service import UserService
from app.domains.inventory.models.stock_location import LocationType, StockLocation
from app.domains.inventory.schemas.location import LocationCreate
from app.domains.inventory.services.inventory_service import InventoryService
from app.domains.rbac.models import Role, UserRole
from app.domains.rbac.repositories import RoleRepository, UserRoleRepository
from app.domains.rbac.schemas import RoleCreate, UserRoleCreate

engine = create_engine(settings.database_url)


# ── Usuarios ──────────────────────────────────────────────────────────────────

USERS = [
    dict(
        email="admin@robotschool.com",
        password="Admin1234!",
        first_name="Admin",
        last_name="RobotSchool",
        position="Administrador",
    ),
    dict(
        email="supertrainer@robotschool.com",
        password="SuperTrainer1234!",
        first_name="Ana",
        last_name="Supervisora",
        position="Coordinadora de Capacitación",
    ),
]


def seed_users(session: Session) -> None:
    svc = UserService()
    for u in USERS:
        existing = session.exec(select(User).where(User.email == u["email"])).first()
        if existing:
            print(f"  [skip] usuario '{u['email']}' ya existe")
            continue
        svc.register(session, **u)
        print(f"  [ok]   usuario '{u['email']}' creado")


# ── Ubicaciones de stock ───────────────────────────────────────────────────────

LOCATIONS = [
    LocationCreate(name="Bodega Principal", type=LocationType.WAREHOUSE),
    LocationCreate(name="Sede Bogotá", type=LocationType.SEDE),
    LocationCreate(name="Sede 2", type=LocationType.SEDE),
    LocationCreate(name="Sede 3", type=LocationType.SEDE),
]


def seed_locations(session: Session) -> None:
    svc = InventoryService()
    for loc in LOCATIONS:
        existing = session.exec(
            select(StockLocation).where(StockLocation.name == loc.name)
        ).first()
        if existing:
            print(f"  [skip] ubicación '{loc.name}' ya existe")
            continue
        svc.create_location(session, loc)
        print(f"  [ok]   ubicación '{loc.name}' creada")


# ── Roles RBAC ────────────────────────────────────────────────────────────────

ROLES = [
    RoleCreate(name="ADMIN", description="Acceso total al sistema"),
    RoleCreate(name="DIRECTOR", description="Director de grado en colegio"),
    RoleCreate(name="TEACHER", description="Docente de curso"),
    RoleCreate(name="STUDENT", description="Estudiante matriculado"),
    RoleCreate(name="OPERATIVO", description="Personal de producción y bodega"),
    RoleCreate(name="COMERCIAL", description="Personal de ventas y órdenes"),
    RoleCreate(name="TRAINER", description="Instructor de capacitación docente de RobotSchool"),
    RoleCreate(
        name="SUPER_TRAINER",
        description=(
            "Instructor jefe de RobotSchool. Puede ver y gestionar todos los "
            "programas y asignar TRAINERs."
        ),
    ),
]


def seed_roles(session: Session) -> None:
    repo = RoleRepository(session)
    for role_data in ROLES:
        existing = repo.get_by_name(role_data.name)
        if existing:
            print(f"  [skip] rol '{role_data.name}' ya existe")
            continue
        repo.create(role_data)
        print(f"  [ok]   rol '{role_data.name}' creado")


# ── Asignación usuario → rol ──────────────────────────────────────────────────

USER_ROLE_ASSIGNMENTS = [
    ("admin@robotschool.com", "ADMIN"),
    ("director4@sanpedro.edu.co", "DIRECTOR"),
    ("docente1@sanpedro.edu.co", "TEACHER"),
    ("estudiante1@sanpedro.edu.co", "STUDENT"),
    ("estudiante2@sanpedro.edu.co", "STUDENT"),
    ("trainer@robotschool.com", "TRAINER"),
    ("supertrainer@robotschool.com", "SUPER_TRAINER"),
]


def seed_user_roles(session: Session) -> None:
    role_repo = RoleRepository(session)
    ur_repo = UserRoleRepository(session)
    for email, role_name in USER_ROLE_ASSIGNMENTS:
        user = session.exec(select(User).where(User.email == email)).first()
        if user is None:
            print(f"  [warn] usuario '{email}' no existe, saltando asignación")
            continue
        role = role_repo.get_by_name(role_name)
        if role is None:
            print(f"  [warn] rol '{role_name}' no existe, saltando asignación")
            continue
        existing = [ur for ur in ur_repo.list_by_user_id(user.id) if ur.role_id == role.id]
        if existing:
            print(f"  [skip] '{email}' ya tiene rol '{role_name}'")
            continue
        ur_repo.create(UserRoleCreate(user_id=user.id, role_id=role.id))
        print(f"  [ok]   '{email}' → rol '{role_name}' asignado")


# ── Académico ────────────────────────────────────────────────────────────────


def seed_academic(session: Session) -> None:
    from app.domains.academic.models.school import School
    from app.domains.academic.models.lms_grade import LmsGrade
    from app.domains.academic.models.lms_course import LmsCourse
    from app.domains.academic.models.lms_unit import LmsUnit
    from app.domains.academic.models.lms_material import LmsMaterial
    from app.domains.academic.models.lms_assignment import LmsAssignment
    from app.domains.academic.repositories import (
        SchoolRepository, GradeRepository, CourseRepository,
        CourseStudentRepository, GradeDirectorRepository,
        UnitRepository, MaterialRepository, AssignmentRepository,
    )
    from app.domains.academic.schemas import (
        SchoolCreate, GradeCreate, CourseCreate,
        UnitCreate, MaterialCreate, AssignmentCreate,
    )

    svc = UserService()

    # — Colegio —
    school = session.exec(select(School).where(School.name == "Colegio San Pedro")).first()
    if school:
        print("  [skip] colegio 'Colegio San Pedro' ya existe")
    else:
        school = SchoolRepository(session).create(
            SchoolCreate(name="Colegio San Pedro", city="Bogotá")
        )
        print("  [ok]   colegio 'Colegio San Pedro' creado")

    # — Grado —
    grade = session.exec(
        select(LmsGrade).where(LmsGrade.name == "4to Primaria", LmsGrade.school_id == school.id)
    ).first()
    if grade:
        print("  [skip] grado '4to Primaria' ya existe")
    else:
        grade = GradeRepository(session).create(school.id, GradeCreate(name="4to Primaria"))
        print("  [ok]   grado '4to Primaria' creado")

    # — Usuarios académicos —
    academic_users = [
        dict(email="director4@sanpedro.edu.co", password="Director1234!",
             first_name="Carlos", last_name="Ruiz", position="Director de Grado"),
        dict(email="docente1@sanpedro.edu.co", password="Docente1234!",
             first_name="María", last_name="García", position="Docente"),
        dict(email="estudiante1@sanpedro.edu.co", password="Estudiante1234!",
             first_name="Juan", last_name="Pérez"),
        dict(email="estudiante2@sanpedro.edu.co", password="Estudiante1234!",
             first_name="Ana", last_name="López"),
    ]
    users: dict[str, User] = {}
    for u in academic_users:
        existing = session.exec(select(User).where(User.email == u["email"])).first()
        if existing:
            print(f"  [skip] usuario '{u['email']}' ya existe")
            users[u["email"]] = existing
        else:
            users[u["email"]] = svc.register(session, **u)
            print(f"  [ok]   usuario '{u['email']}' creado")

    # — Director —
    director = users["director4@sanpedro.edu.co"]
    director_repo = GradeDirectorRepository(session)
    if director_repo.is_director_of_grade(grade.id, director.id):
        print("  [skip] director ya asignado a '4to Primaria'")
    else:
        director_repo.assign(grade.id, director.id)
        print("  [ok]   director asignado a '4to Primaria'")

    # — Curso —
    teacher = users["docente1@sanpedro.edu.co"]
    course = session.exec(
        select(LmsCourse).where(LmsCourse.name == "4to A", LmsCourse.grade_id == grade.id)
    ).first()
    if course:
        print("  [skip] curso '4to A' ya existe")
    else:
        course = CourseRepository(session).create(
            grade.id, school.id, teacher.id, CourseCreate(name="4to A")
        )
        print("  [ok]   curso '4to A' creado")

    # — Estudiantes enrolled —
    cs_repo = CourseStudentRepository(session)
    for email in ["estudiante1@sanpedro.edu.co", "estudiante2@sanpedro.edu.co"]:
        student = users[email]
        if cs_repo.is_enrolled(course.id, student.id):
            print(f"  [skip] '{email}' ya enrolled en '4to A'")
        else:
            cs_repo.enroll(course.id, student.id)
            print(f"  [ok]   '{email}' enrolled en '4to A'")

    # — Unidad —
    unit = session.exec(
        select(LmsUnit).where(
            LmsUnit.title == "Introducción a la Robótica", LmsUnit.course_id == course.id
        )
    ).first()
    if unit:
        print("  [skip] unidad 'Introducción a la Robótica' ya existe")
    else:
        unit = UnitRepository(session).create(
            course.id,
            UnitCreate(title="Introducción a la Robótica", order_index=0),
        )
        unit.is_published = True
        session.add(unit)
        session.commit()
        session.refresh(unit)
        print("  [ok]   unidad 'Introducción a la Robótica' creada")

    # — Material —
    mat = session.exec(
        select(LmsMaterial).where(
            LmsMaterial.title == "Bienvenidos al curso", LmsMaterial.unit_id == unit.id
        )
    ).first()
    if mat:
        print("  [skip] material 'Bienvenidos al curso' ya existe")
    else:
        MaterialRepository(session).create(
            unit.id,
            MaterialCreate(
                title="Bienvenidos al curso",
                type="TEXT",
                content="En este curso aprenderán los fundamentos de la robótica.",
                is_published=True,
            ),
        )
        print("  [ok]   material 'Bienvenidos al curso' creado")

    # — Assignment —
    assign = session.exec(
        select(LmsAssignment).where(
            LmsAssignment.title == "Dibuja tu robot ideal", LmsAssignment.unit_id == unit.id
        )
    ).first()
    if assign:
        print("  [skip] assignment 'Dibuja tu robot ideal' ya existe")
    else:
        a = AssignmentRepository(session).create(
            unit.id,
            AssignmentCreate(
                title="Dibuja tu robot ideal",
                description="Dibuja y describe cómo sería tu robot ideal.",
                max_score=100,
            ),
        )
        a.is_published = True
        session.add(a)
        session.commit()
        print("  [ok]   assignment 'Dibuja tu robot ideal' creado")


# ── Capacitación ─────────────────────────────────────────────────────────────


def seed_training(session: Session) -> None:
    from app.domains.training.models.training_program import TrainingProgram
    from app.domains.training.models.training_module import TrainingModule
    from app.domains.training.models.training_lesson import TrainingLesson
    from app.domains.training.models.training_evaluation import TrainingEvaluation
    from app.domains.training.models.training_quiz_question import TrainingQuizQuestion
    from app.domains.training.models.training_enrollment import TrainingEnrollment

    svc = UserService()

    # — Usuario TRAINER —
    trainer_data = dict(
        email="trainer@robotschool.com",
        password="Trainer1234!",
        first_name="Carlos",
        last_name="Instructor",
        position="Instructor de Robótica",
    )
    trainer = session.exec(
        select(User).where(User.email == trainer_data["email"])
    ).first()
    if trainer:
        print(f"  [skip] usuario '{trainer_data['email']}' ya existe")
    else:
        trainer = svc.register(session, **trainer_data)
        print(f"  [ok]   usuario '{trainer_data['email']}' creado")

    # — Programa —
    program = session.exec(
        select(TrainingProgram).where(
            TrainingProgram.name == "Capacitación en Robótica Educativa"
        )
    ).first()
    if program:
        print("  [skip] programa 'Capacitación en Robótica Educativa' ya existe")
        if program.created_by != trainer.id:
            program.created_by = trainer.id
            session.add(program)
            session.commit()
            session.refresh(program)
            print("  [updated] created_by → trainer")
    else:
        program = TrainingProgram(
            name="Capacitación en Robótica Educativa",
            description="Programa oficial de RobotSchool para docentes",
            objective="Capacitar docentes en el uso de herramientas de robótica en el aula",
            duration_hours=20,
            is_active=True,
            is_published=True,
            created_by=trainer.id,
        )
        session.add(program)
        session.commit()
        session.refresh(program)
        print("  [ok]   programa 'Capacitación en Robótica Educativa' creado")

    # — Módulo 1 —
    module = session.exec(
        select(TrainingModule).where(
            TrainingModule.title == "Introducción a la Robótica",
            TrainingModule.program_id == program.id,
        )
    ).first()
    if module:
        print("  [skip] módulo 'Introducción a la Robótica' ya existe")
    else:
        module = TrainingModule(
            program_id=program.id,
            title="Introducción a la Robótica",
            order_index=0,
            is_published=True,
        )
        session.add(module)
        session.commit()
        session.refresh(module)
        print("  [ok]   módulo 'Introducción a la Robótica' creado")

    # — Lección 1 —
    lesson = session.exec(
        select(TrainingLesson).where(
            TrainingLesson.title == "¿Qué es la robótica educativa?",
            TrainingLesson.module_id == module.id,
        )
    ).first()
    if lesson:
        print("  [skip] lección '¿Qué es la robótica educativa?' ya existe")
    else:
        lesson = TrainingLesson(
            module_id=module.id,
            title="¿Qué es la robótica educativa?",
            type="TEXT",
            content=(
                "La robótica educativa es una herramienta pedagógica que permite "
                "a los estudiantes aprender conceptos de ciencia, tecnología, "
                "ingeniería y matemáticas (STEM) a través de la construcción y "
                "programación de robots."
            ),
            order_index=0,
            is_published=True,
        )
        session.add(lesson)
        session.commit()
        session.refresh(lesson)
        print("  [ok]   lección '¿Qué es la robótica educativa?' creada")

    # — Evaluación 1 (Quiz) —
    evaluation = session.exec(
        select(TrainingEvaluation).where(
            TrainingEvaluation.title == "Quiz de Introducción",
            TrainingEvaluation.module_id == module.id,
        )
    ).first()
    if evaluation:
        print("  [skip] evaluación 'Quiz de Introducción' ya existe")
    else:
        evaluation = TrainingEvaluation(
            module_id=module.id,
            title="Quiz de Introducción",
            type="QUIZ",
            passing_score=60,
            is_published=True,
        )
        session.add(evaluation)
        session.commit()
        session.refresh(evaluation)
        print("  [ok]   evaluación 'Quiz de Introducción' creada")

    # — Pregunta 1 —
    question = session.exec(
        select(TrainingQuizQuestion).where(
            TrainingQuizQuestion.evaluation_id == evaluation.id,
        )
    ).first()
    if question:
        print("  [skip] pregunta del quiz ya existe")
    else:
        question = TrainingQuizQuestion(
            evaluation_id=evaluation.id,
            question="¿Cuál es el objetivo principal de la robótica educativa?",
            options=[
                {"id": 0, "text": "Entretenimiento"},
                {"id": 1, "text": "Desarrollo del pensamiento computacional"},
                {"id": 2, "text": "Competencia deportiva"},
                {"id": 3, "text": "Ninguna de las anteriores"},
            ],
            correct_option=1,
            points=10,
            order_index=0,
        )
        session.add(question)
        session.commit()
        session.refresh(question)
        print("  [ok]   pregunta del quiz creada")

    # — Inscripción docente —
    docente = session.exec(
        select(User).where(User.email == "docente1@sanpedro.edu.co")
    ).first()
    if docente is None:
        print("  [warn] usuario 'docente1@sanpedro.edu.co' no existe, saltando inscripción")
        return

    enrollment = session.exec(
        select(TrainingEnrollment).where(
            TrainingEnrollment.program_id == program.id,
            TrainingEnrollment.user_id == docente.id,
        )
    ).first()
    if enrollment:
        print("  [skip] inscripción de 'docente1@sanpedro.edu.co' ya existe")
    else:
        from datetime import datetime, timezone

        enrollment = TrainingEnrollment(
            program_id=program.id,
            user_id=docente.id,
            enrolled_by=trainer.id,
            enrolled_at=datetime.now(timezone.utc),
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)
        print("  [ok]   'docente1@sanpedro.edu.co' inscrito en programa de capacitación")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("→ Iniciando seed...")
    with Session(engine) as session:
        print("\n→ Usuarios:")
        seed_users(session)

        print("\n→ Ubicaciones de stock:")
        seed_locations(session)

        print("\n→ Roles RBAC:")
        seed_roles(session)

        print("\n→ Académico (datos + usuarios):")
        seed_academic(session)

        print("\n→ Capacitación (datos + usuarios):")
        seed_training(session)

        print("\n→ Asignación de roles a usuarios:")
        seed_user_roles(session)

    print("\n✓ Seed completo.")


if __name__ == "__main__":
    main()
