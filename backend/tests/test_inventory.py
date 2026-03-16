"""Inventory domain tests."""
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.domains.auth.models import User


# ── Auth fixture ───────────────────────────────────────────────────────────────


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, session):
    user = User(
        email="inventory@robotschool.com",
        password_hash=hash_password("pass123"),
        first_name="Inventory",
        last_name="Admin",
    )
    session.add(user)
    session.commit()
    client.post(
        "/auth/login",
        json={"email": "inventory@robotschool.com", "password": "pass123"},
    )
    return client


# ── Helpers ────────────────────────────────────────────────────────────────────


def _create_location(client: TestClient, name: str = "Main Warehouse") -> dict:
    return client.post(
        "/inventory/locations",
        json={"name": name, "type": "WAREHOUSE"},
    ).json()


def _create_product(client: TestClient, sku: str, product_type: str = "KIT") -> dict:
    return client.post(
        "/catalog/products",
        json={"sku": sku, "name": sku, "type": product_type},
    ).json()


# ── Locations ──────────────────────────────────────────────────────────────────


def test_create_location(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/inventory/locations",
        json={"name": "Bogotá HQ", "type": "SEDE", "address": "Calle 123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bogotá HQ"
    assert data["type"] == "SEDE"
    assert data["address"] == "Calle 123"
    assert "public_id" in data
    assert data["is_active"] is True


def test_list_locations(auth_client: TestClient) -> None:
    _create_location(auth_client, "WH-A")
    _create_location(auth_client, "WH-B")
    response = auth_client.get("/inventory/locations")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_get_location(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "GET-LOC")
    response = auth_client.get(f"/inventory/locations/{loc['public_id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "GET-LOC"


def test_get_location_not_found(auth_client: TestClient) -> None:
    response = auth_client.get("/inventory/locations/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_inventory_requires_auth(client: TestClient) -> None:
    assert client.get("/inventory/locations").status_code == 401
    assert client.get("/inventory/balances").status_code == 401
    assert client.get("/inventory/movements").status_code == 401


# ── Balances ───────────────────────────────────────────────────────────────────


def test_adjust_balance_creates_balance(auth_client: TestClient) -> None:
    product = _create_product(auth_client, "ADJ-KIT")
    loc = _create_location(auth_client, "ADJ-WH")

    response = auth_client.post(
        "/inventory/movements",
        json={
            "product_public_id": product["public_id"],
            "location_public_id": loc["public_id"],
            "status": "FREE",
            "delta": 10,
        },
    )
    assert response.status_code == 201
    mvt = response.json()
    assert mvt["quantity"] == 10
    assert mvt["movement_type"] == "ADJUST"

    # Balance should now show 10 FREE units
    resp = auth_client.get(
        f"/inventory/balances?product_id={product['public_id']}&location_id={loc['public_id']}"
    )
    assert resp.status_code == 200
    balances = resp.json()
    free = next(b for b in balances if b["status"] == "FREE")
    assert free["quantity"] == 10


def test_adjust_balance_increment(auth_client: TestClient) -> None:
    product = _create_product(auth_client, "INC-KIT")
    loc = _create_location(auth_client, "INC-WH")

    auth_client.post(
        "/inventory/movements",
        json={
            "product_public_id": product["public_id"],
            "location_public_id": loc["public_id"],
            "status": "FREE",
            "delta": 5,
        },
    )
    auth_client.post(
        "/inventory/movements",
        json={
            "product_public_id": product["public_id"],
            "location_public_id": loc["public_id"],
            "status": "FREE",
            "delta": 3,
        },
    )
    resp = auth_client.get(
        f"/inventory/balances?product_id={product['public_id']}&location_id={loc['public_id']}"
    )
    free = next(b for b in resp.json() if b["status"] == "FREE")
    assert free["quantity"] == 8


def test_adjust_balance_negative_delta_reduces_stock(auth_client: TestClient) -> None:
    product = _create_product(auth_client, "NEG-KIT")
    loc = _create_location(auth_client, "NEG-WH")

    auth_client.post(
        "/inventory/movements",
        json={
            "product_public_id": product["public_id"],
            "location_public_id": loc["public_id"],
            "status": "FREE",
            "delta": 10,
        },
    )
    response = auth_client.post(
        "/inventory/movements",
        json={
            "product_public_id": product["public_id"],
            "location_public_id": loc["public_id"],
            "status": "FREE",
            "delta": -4,
        },
    )
    assert response.status_code == 201

    resp = auth_client.get(
        f"/inventory/balances?product_id={product['public_id']}&location_id={loc['public_id']}"
    )
    free = next(b for b in resp.json() if b["status"] == "FREE")
    assert free["quantity"] == 6


def test_adjust_balance_cannot_go_negative(auth_client: TestClient) -> None:
    product = _create_product(auth_client, "NEGFAIL-KIT")
    loc = _create_location(auth_client, "NEGFAIL-WH")

    response = auth_client.post(
        "/inventory/movements",
        json={
            "product_public_id": product["public_id"],
            "location_public_id": loc["public_id"],
            "status": "FREE",
            "delta": -5,
        },
    )
    assert response.status_code == 422


def test_balance_summary(auth_client: TestClient) -> None:
    product = _create_product(auth_client, "SUM-KIT")
    loc = _create_location(auth_client, "SUM-WH")

    auth_client.post(
        "/inventory/movements",
        json={
            "product_public_id": product["public_id"],
            "location_public_id": loc["public_id"],
            "status": "FREE",
            "delta": 20,
        },
    )
    auth_client.post(
        "/inventory/movements",
        json={
            "product_public_id": product["public_id"],
            "location_public_id": loc["public_id"],
            "status": "DAMAGED",
            "delta": 3,
        },
    )

    resp = auth_client.get("/inventory/balances/summary")
    assert resp.status_code == 200
    items = resp.json()
    assert any(i["status"] == "FREE" and i["total_quantity"] >= 20 for i in items)
    assert any(i["status"] == "DAMAGED" and i["total_quantity"] >= 3 for i in items)


def test_list_movements(auth_client: TestClient) -> None:
    product = _create_product(auth_client, "MVT-KIT")
    loc = _create_location(auth_client, "MVT-WH")

    for delta in (10, 5, -3):
        auth_client.post(
            "/inventory/movements",
            json={
                "product_public_id": product["public_id"],
                "location_public_id": loc["public_id"],
                "status": "FREE",
                "delta": delta,
            },
        )

    resp = auth_client.get(
        f"/inventory/movements?product_id={product['public_id']}&location_id={loc['public_id']}"
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 3


# ── Component inventory ────────────────────────────────────────────────────────


def test_component_adjust_balance(auth_client: TestClient) -> None:
    comp = _create_product(auth_client, "ADJ-COMP", "COMPONENT")
    loc = _create_location(auth_client, "COMP-WH")

    response = auth_client.post(
        "/inventory/components/movements",
        json={
            "component_public_id": comp["public_id"],
            "location_public_id": loc["public_id"],
            "status": "AVAILABLE",
            "delta": 50,
        },
    )
    assert response.status_code == 201
    assert response.json()["quantity"] == 50

    resp = auth_client.get(
        f"/inventory/components/balances?component_id={comp['public_id']}&location_id={loc['public_id']}"
    )
    assert resp.status_code == 200
    avail = next(b for b in resp.json() if b["status"] == "AVAILABLE")
    assert avail["quantity"] == 50


def test_component_balance_summary(auth_client: TestClient) -> None:
    comp = _create_product(auth_client, "SUM-COMP", "COMPONENT")
    loc = _create_location(auth_client, "SUMCOMP-WH")

    auth_client.post(
        "/inventory/components/movements",
        json={
            "component_public_id": comp["public_id"],
            "location_public_id": loc["public_id"],
            "status": "AVAILABLE",
            "delta": 100,
        },
    )

    resp = auth_client.get("/inventory/components/balances/summary")
    assert resp.status_code == 200
    items = resp.json()
    assert any(i["status"] == "AVAILABLE" and i["total_quantity"] >= 100 for i in items)


def test_component_cannot_go_negative(auth_client: TestClient) -> None:
    comp = _create_product(auth_client, "CNEG-COMP", "COMPONENT")
    loc = _create_location(auth_client, "CNEG-WH")

    response = auth_client.post(
        "/inventory/components/movements",
        json={
            "component_public_id": comp["public_id"],
            "location_public_id": loc["public_id"],
            "status": "AVAILABLE",
            "delta": -10,
        },
    )
    assert response.status_code == 422


def test_component_list_movements(auth_client: TestClient) -> None:
    comp = _create_product(auth_client, "CMVT-COMP", "COMPONENT")
    loc = _create_location(auth_client, "CMVT-WH")

    for delta in (20, 10):
        auth_client.post(
            "/inventory/components/movements",
            json={
                "component_public_id": comp["public_id"],
                "location_public_id": loc["public_id"],
                "status": "AVAILABLE",
                "delta": delta,
            },
        )

    resp = auth_client.get(
        f"/inventory/components/movements?component_id={comp['public_id']}"
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2
