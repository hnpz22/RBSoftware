"""Shared test fixtures."""
import os

# Must be set before any app import so pydantic-settings can resolve required fields.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.database import get_session
from app.core.security import hash_password

# Import all models so SQLModel.metadata knows about every table before create_all
from app.domains.audit.models import AuditLog  # noqa: F401
from app.domains.auth.models import RefreshToken, User  # noqa: F401
from app.domains.catalog.models import KitBomItem, Product  # noqa: F401
from app.domains.commercial.models import SalesOrder, SalesOrderItem  # noqa: F401
from app.domains.production.models import (  # noqa: F401
    ProductionBatch,
    ProductionBatchItem,
    ProductionBatchSalesOrder,
    ProductionBlock,
    ProductionItemCounter,
)
from app.domains.inventory.models import (  # noqa: F401
    ComponentInventoryBalance,
    ComponentInventoryMovement,
    InventoryBalance,
    InventoryMovement,
    StockLocation,
)
from app.domains.integrations.models import IntegrationSyncState  # noqa: F401
from app.domains.fulfillment.models import (  # noqa: F401
    SalesOrderPackEvent,
    SalesOrderPackItem,
)
from app.domains.rbac.models import Permission, Role, RolePermission, UserRole  # noqa: F401
from app.main import app


@pytest.fixture(name="engine", scope="function")
def engine_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session", scope="function")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client", scope="function")
def client_fixture(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user", scope="function")
def test_user_fixture(session):
    user = User(
        email="test@robotschool.com",
        password_hash=hash_password("secret123"),
        first_name="Test",
        last_name="User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
