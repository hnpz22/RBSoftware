"""RBAC endpoint tests."""
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.domains.auth.models import User


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, session):
    """Client already authenticated as a test user."""
    user = User(
        email="admin@robotschool.com",
        password_hash=hash_password("admin123"),
        first_name="Admin",
        last_name="User",
    )
    session.add(user)
    session.commit()
    client.post("/auth/login", json={"email": "admin@robotschool.com", "password": "admin123"})
    return client, user


# ── Roles ──────────────────────────────────────────────────────────────────────


def test_create_role(auth_client) -> None:
    client, _ = auth_client
    response = client.post("/rbac/roles", json={"name": "operator", "description": "Bodega"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "operator"
    assert "public_id" in data
    assert "id" not in data


def test_create_role_duplicate_returns_409(auth_client) -> None:
    client, _ = auth_client
    client.post("/rbac/roles", json={"name": "admin"})
    response = client.post("/rbac/roles", json={"name": "admin"})
    assert response.status_code == 409


def test_list_roles(auth_client) -> None:
    client, _ = auth_client
    client.post("/rbac/roles", json={"name": "viewer"})
    response = client.get("/rbac/roles")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_delete_role(auth_client) -> None:
    client, _ = auth_client
    created = client.post("/rbac/roles", json={"name": "temp_role"})
    public_id = created.json()["public_id"]
    response = client.delete(f"/rbac/roles/{public_id}")
    assert response.status_code == 204


def test_delete_role_not_found(auth_client) -> None:
    client, _ = auth_client
    response = client.delete("/rbac/roles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


# ── Permissions ────────────────────────────────────────────────────────────────


def test_create_permission(auth_client) -> None:
    client, _ = auth_client
    response = client.post(
        "/rbac/permissions",
        json={"code": "commercial.sales_order.approve", "description": "Approve orders"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "commercial.sales_order.approve"
    assert "id" not in data


def test_create_permission_duplicate_returns_409(auth_client) -> None:
    client, _ = auth_client
    client.post("/rbac/permissions", json={"code": "catalog.product.read"})
    response = client.post("/rbac/permissions", json={"code": "catalog.product.read"})
    assert response.status_code == 409


def test_list_permissions(auth_client) -> None:
    client, _ = auth_client
    client.post("/rbac/permissions", json={"code": "inventory.balance.read"})
    response = client.get("/rbac/permissions")
    assert response.status_code == 200
    assert len(response.json()) >= 1


# ── Role → Permission assignment ───────────────────────────────────────────────


def test_assign_permission_to_role(auth_client) -> None:
    client, _ = auth_client
    role = client.post("/rbac/roles", json={"name": "manager"}).json()
    perm = client.post(
        "/rbac/permissions", json={"code": "production.batch.create"}
    ).json()

    response = client.post(
        f"/rbac/roles/{role['public_id']}/permissions/{perm['public_id']}"
    )
    assert response.status_code == 204


def test_assign_permission_duplicate_returns_409(auth_client) -> None:
    client, _ = auth_client
    role = client.post("/rbac/roles", json={"name": "lead"}).json()
    perm = client.post("/rbac/permissions", json={"code": "fulfillment.pack.close"}).json()

    client.post(f"/rbac/roles/{role['public_id']}/permissions/{perm['public_id']}")
    response = client.post(
        f"/rbac/roles/{role['public_id']}/permissions/{perm['public_id']}"
    )
    assert response.status_code == 409


def test_remove_permission_from_role(auth_client) -> None:
    client, _ = auth_client
    role = client.post("/rbac/roles", json={"name": "auditor"}).json()
    perm = client.post("/rbac/permissions", json={"code": "audit.log.read"}).json()

    client.post(f"/rbac/roles/{role['public_id']}/permissions/{perm['public_id']}")
    response = client.delete(
        f"/rbac/roles/{role['public_id']}/permissions/{perm['public_id']}"
    )
    assert response.status_code == 204


# ── User → Role assignment ─────────────────────────────────────────────────────


def test_assign_role_to_user(auth_client) -> None:
    client, user = auth_client
    role = client.post("/rbac/roles", json={"name": "warehouse"}).json()

    response = client.post(f"/rbac/users/{user.public_id}/roles/{role['public_id']}")
    assert response.status_code == 204


def test_assign_role_duplicate_returns_409(auth_client) -> None:
    client, user = auth_client
    role = client.post("/rbac/roles", json={"name": "supervisor"}).json()

    client.post(f"/rbac/users/{user.public_id}/roles/{role['public_id']}")
    response = client.post(f"/rbac/users/{user.public_id}/roles/{role['public_id']}")
    assert response.status_code == 409


def test_remove_role_from_user(auth_client) -> None:
    client, user = auth_client
    role = client.post("/rbac/roles", json={"name": "packer"}).json()

    client.post(f"/rbac/users/{user.public_id}/roles/{role['public_id']}")
    response = client.delete(f"/rbac/users/{user.public_id}/roles/{role['public_id']}")
    assert response.status_code == 204


# ── User permissions ───────────────────────────────────────────────────────────


def test_get_user_permissions(auth_client) -> None:
    client, user = auth_client

    # Create role + 2 permissions + assign both to role + assign role to user
    role = client.post("/rbac/roles", json={"name": "full_ops"}).json()
    p1 = client.post("/rbac/permissions", json={"code": "production.batch.read"}).json()
    p2 = client.post("/rbac/permissions", json={"code": "inventory.balance.write"}).json()
    client.post(f"/rbac/roles/{role['public_id']}/permissions/{p1['public_id']}")
    client.post(f"/rbac/roles/{role['public_id']}/permissions/{p2['public_id']}")
    client.post(f"/rbac/users/{user.public_id}/roles/{role['public_id']}")

    response = client.get(f"/rbac/users/{user.public_id}/permissions")
    assert response.status_code == 200
    codes = response.json()
    assert "production.batch.read" in codes
    assert "inventory.balance.write" in codes


def test_get_user_permissions_deduplicates(auth_client) -> None:
    """Same permission via two roles must appear only once."""
    client, user = auth_client

    perm = client.post("/rbac/permissions", json={"code": "shared.resource.read"}).json()
    r1 = client.post("/rbac/roles", json={"name": "role_a"}).json()
    r2 = client.post("/rbac/roles", json={"name": "role_b"}).json()
    client.post(f"/rbac/roles/{r1['public_id']}/permissions/{perm['public_id']}")
    client.post(f"/rbac/roles/{r2['public_id']}/permissions/{perm['public_id']}")
    client.post(f"/rbac/users/{user.public_id}/roles/{r1['public_id']}")
    client.post(f"/rbac/users/{user.public_id}/roles/{r2['public_id']}")

    response = client.get(f"/rbac/users/{user.public_id}/permissions")
    codes = response.json()
    assert codes.count("shared.resource.read") == 1


def test_rbac_endpoints_require_auth(client: TestClient) -> None:
    """All RBAC endpoints must reject unauthenticated requests."""
    assert client.get("/rbac/roles").status_code == 401
    assert client.get("/rbac/permissions").status_code == 401
