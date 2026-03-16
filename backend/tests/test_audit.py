"""Audit endpoint and integration tests."""
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.domains.audit.models import AuditLog
from app.domains.audit.services import AuditService
from app.domains.auth.models import User


# ── AuditService unit tests ────────────────────────────────────────────────────


def test_audit_service_creates_log(session) -> None:
    svc = AuditService()
    entry = svc.log(
        session,
        user_id=None,
        action="test.action",
        resource_type="test_resource",
        resource_id="abc-123",
        payload={"key": "value"},
        ip="127.0.0.1",
    )
    assert entry.id is not None
    assert entry.action == "test.action"
    assert entry.resource_type == "test_resource"
    assert entry.payload == {"key": "value"}
    assert entry.ip_address == "127.0.0.1"


def test_audit_service_list_filters_by_resource_type(session) -> None:
    svc = AuditService()
    svc.log(session, user_id=None, action="a.b", resource_type="order", resource_id="1")
    svc.log(session, user_id=None, action="a.b", resource_type="user", resource_id="2")
    svc.log(session, user_id=None, action="a.b", resource_type="order", resource_id="3")

    orders = svc.list(session, resource_type="order")
    assert len(orders) == 2
    assert all(e.resource_type == "order" for e in orders)


def test_audit_service_list_filters_by_user_id(session) -> None:
    svc = AuditService()
    svc.log(session, user_id=1, action="a.b", resource_type="x", resource_id="1")
    svc.log(session, user_id=2, action="a.b", resource_type="x", resource_id="2")
    svc.log(session, user_id=1, action="a.b", resource_type="x", resource_id="3")

    result = svc.list(session, user_id=1)
    assert len(result) == 2
    assert all(e.user_id == 1 for e in result)


def test_audit_service_list_respects_limit(session) -> None:
    svc = AuditService()
    for i in range(10):
        svc.log(session, user_id=None, action="x", resource_type="y", resource_id=str(i))

    result = svc.list(session, limit=3)
    assert len(result) == 3


# ── Auth integration: audit entries created on login ──────────────────────────


def test_login_creates_audit_entry(client: TestClient, session, test_user) -> None:
    client.post("/auth/login", json={"email": "test@robotschool.com", "password": "secret123"})

    entries = session.query(AuditLog).filter_by(action="auth.login").all()
    assert len(entries) == 1
    assert entries[0].user_id == test_user.id


def test_failed_login_creates_audit_entry(client: TestClient, session, test_user) -> None:
    client.post("/auth/login", json={"email": "test@robotschool.com", "password": "wrong"})

    entries = session.query(AuditLog).filter_by(action="auth.login_failed").all()
    assert len(entries) == 1
    assert entries[0].user_id is None


def test_refresh_failure_creates_audit_entry(client: TestClient, session) -> None:
    # Inject a bad cookie manually
    client.cookies.set("refresh_token", "invalid-token")
    client.post("/auth/refresh")

    entries = session.query(AuditLog).filter_by(action="auth.refresh_failed").all()
    assert len(entries) == 1


def test_logout_creates_audit_entry(client: TestClient, session, test_user) -> None:
    client.post("/auth/login", json={"email": "test@robotschool.com", "password": "secret123"})
    client.post("/auth/logout")

    entries = session.query(AuditLog).filter_by(action="auth.logout").all()
    assert len(entries) == 1


# ── RBAC integration: audit entries created on assignments ────────────────────


def _setup_role_and_permission(client: TestClient):
    role = client.post("/rbac/roles", json={"name": "audit_test_role"}).json()
    perm = client.post(
        "/rbac/permissions", json={"code": "catalog.product.read"}
    ).json()
    return role, perm


def test_assign_permission_creates_audit_entry(
    client: TestClient, session, test_user
) -> None:
    client.post("/auth/login", json={"email": "test@robotschool.com", "password": "secret123"})
    role, perm = _setup_role_and_permission(client)
    client.post(f"/rbac/roles/{role['public_id']}/permissions/{perm['public_id']}")

    entries = session.query(AuditLog).filter_by(
        action="rbac.assign_permission_to_role"
    ).all()
    assert len(entries) == 1
    assert entries[0].user_id == test_user.id


def test_assign_role_creates_audit_entry(client: TestClient, session, test_user) -> None:
    client.post("/auth/login", json={"email": "test@robotschool.com", "password": "secret123"})
    role = client.post("/rbac/roles", json={"name": "ops_team"}).json()
    client.post(f"/rbac/users/{test_user.public_id}/roles/{role['public_id']}")

    entries = session.query(AuditLog).filter_by(action="rbac.assign_role_to_user").all()
    assert len(entries) == 1
    assert entries[0].user_id == test_user.id


# ── GET /audit/logs endpoint ───────────────────────────────────────────────────


def test_get_audit_logs_requires_auth(client: TestClient) -> None:
    response = client.get("/audit/logs")
    assert response.status_code == 401


def test_get_audit_logs_returns_list(client: TestClient, session, test_user) -> None:
    client.post("/auth/login", json={"email": "test@robotschool.com", "password": "secret123"})

    response = client.get("/audit/logs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # at least the login event
    assert all("action" in e for e in data)
    assert all("id" in e for e in data)


def test_get_audit_logs_filter_by_resource_type(
    client: TestClient, session, test_user
) -> None:
    client.post("/auth/login", json={"email": "test@robotschool.com", "password": "secret123"})

    response = client.get("/audit/logs?resource_type=user")
    assert response.status_code == 200
    data = response.json()
    assert all(e["resource_type"] == "user" for e in data)


def test_get_audit_logs_limit(client: TestClient, session, test_user) -> None:
    # Login first to get auth cookie, then generate several failed attempts
    client.post("/auth/login", json={"email": "test@robotschool.com", "password": "secret123"})
    for _ in range(5):
        client.post(
            "/auth/login", json={"email": "test@robotschool.com", "password": "wrong"}
        )

    response = client.get("/audit/logs?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2
