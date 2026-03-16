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
from app.domains.rbac.models import Role
from app.domains.rbac.repositories import RoleRepository
from app.domains.rbac.schemas import RoleCreate

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
    RoleCreate(name="ADMIN", description="Acceso completo a todos los módulos"),
    RoleCreate(name="OPERATIVO", description="Producción, fulfillment e inventario"),
    RoleCreate(name="COMERCIAL", description="Órdenes y catálogo"),
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

    print("\n✓ Seed completo.")


if __name__ == "__main__":
    main()
