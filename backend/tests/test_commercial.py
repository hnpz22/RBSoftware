"""Commercial domain tests."""
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.domains.auth.models import User


# ── Auth fixture ───────────────────────────────────────────────────────────────


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, session):
    user = User(
        email="commercial@robotschool.com",
        password_hash=hash_password("pass123"),
        first_name="Commercial",
        last_name="Admin",
    )
    session.add(user)
    session.commit()
    client.post(
        "/auth/login",
        json={"email": "commercial@robotschool.com", "password": "pass123"},
    )
    return client


# ── Helpers ────────────────────────────────────────────────────────────────────


def _create_kit(client: TestClient, sku: str) -> dict:
    return client.post(
        "/catalog/products",
        json={"sku": sku, "name": sku, "type": "KIT"},
    ).json()


def _create_location(client: TestClient, name: str = "Main WH") -> dict:
    return client.post(
        "/inventory/locations",
        json={"name": name, "type": "WAREHOUSE"},
    ).json()


def _add_stock(client: TestClient, product_id: str, location_id: str, qty: int) -> None:
    client.post(
        "/inventory/movements",
        json={
            "product_public_id": product_id,
            "location_public_id": location_id,
            "status": "FREE",
            "delta": qty,
        },
    )


def _create_order(client: TestClient, items: list[dict], **kwargs) -> dict:
    payload = {
        "source": "WEB",
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "items": items,
        **kwargs,
    }
    return client.post("/commercial/orders", json=payload).json()


# ── Order CRUD ─────────────────────────────────────────────────────────────────


def test_create_order(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "ORD-KIT")
    response = auth_client.post(
        "/commercial/orders",
        json={
            "source": "WEB",
            "customer_name": "Alice",
            "customer_email": "alice@example.com",
            "items": [
                {"product_public_id": kit["public_id"], "quantity": 2, "unit_price": "150.00"}
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["customer_name"] == "Alice"
    assert "public_id" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


def test_create_order_product_not_found(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/commercial/orders",
        json={
            "source": "WEB",
            "customer_name": "Alice",
            "customer_email": "alice@example.com",
            "items": [
                {
                    "product_public_id": "00000000-0000-0000-0000-000000000000",
                    "quantity": 1,
                    "unit_price": "100.00",
                }
            ],
        },
    )
    assert response.status_code == 404


def test_list_orders(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "LIST-KIT")
    _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 1, "unit_price": "50.00"}],
    )
    response = auth_client.get("/commercial/orders")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_order(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "GET-ORD-KIT")
    order = _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 1, "unit_price": "50.00"}],
    )
    response = auth_client.get(f"/commercial/orders/{order['public_id']}")
    assert response.status_code == 200
    assert response.json()["public_id"] == order["public_id"]


def test_get_order_not_found(auth_client: TestClient) -> None:
    response = auth_client.get("/commercial/orders/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_patch_order_pending(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "PATCH-KIT")
    order = _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 1, "unit_price": "50.00"}],
    )
    response = auth_client.patch(
        f"/commercial/orders/{order['public_id']}",
        json={"customer_name": "Updated Name", "notes": "Rush delivery"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["customer_name"] == "Updated Name"
    assert data["notes"] == "Rush delivery"


def test_patch_order_non_pending_rejected(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "PATCH-APPR-KIT")
    loc = _create_location(auth_client, "PATCH-APPR-WH")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 10)
    order = _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 1, "unit_price": "50.00"}],
    )
    auth_client.post(
        f"/commercial/orders/{order['public_id']}/approve",
        json={"location_id": loc["public_id"]},
    )
    response = auth_client.patch(
        f"/commercial/orders/{order['public_id']}",
        json={"customer_name": "New Name"},
    )
    assert response.status_code == 422


def test_commercial_requires_auth(client: TestClient) -> None:
    assert client.get("/commercial/orders").status_code == 401
    assert client.post("/commercial/orders", json={}).status_code == 401


# ── Approve order ──────────────────────────────────────────────────────────────


def test_approve_order_reserves_available_stock(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "APR-KIT-1")
    loc = _create_location(auth_client, "APR-WH-1")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 10)

    order = _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 3, "unit_price": "100.00"}],
    )

    response = auth_client.post(
        f"/commercial/orders/{order['public_id']}/approve",
        json={"location_id": loc["public_id"]},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["reserved"]["APR-KIT-1"] == 3
    assert result["missing"]["APR-KIT-1"] == 0
    assert result["qr_token"] is not None
    assert result["order_public_id"] == order["public_id"]

    # Check order is now APPROVED with qr_token
    order_data = auth_client.get(f"/commercial/orders/{order['public_id']}").json()
    assert order_data["status"] == "APPROVED"
    assert order_data["qr_token"] is not None
    # Check snapshot was frozen
    assert order_data["items"][0]["snapshot_sku"] == "APR-KIT-1"
    assert order_data["items"][0]["snapshot_name"] == "APR-KIT-1"

    # Check inventory was reserved
    balances = auth_client.get(
        f"/inventory/balances?product_id={kit['public_id']}&location_id={loc['public_id']}"
    ).json()
    free = next((b for b in balances if b["status"] == "FREE"), None)
    reserved = next((b for b in balances if b["status"] == "RESERVED_WEB"), None)
    assert free["quantity"] == 7  # 10 - 3
    assert reserved["quantity"] == 3


def test_approve_order_calculates_missing_correctly(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "APR-KIT-2")
    loc = _create_location(auth_client, "APR-WH-2")
    # Only 2 units available but order requests 5
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 2)

    order = _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 5, "unit_price": "100.00"}],
    )

    response = auth_client.post(
        f"/commercial/orders/{order['public_id']}/approve",
        json={"location_id": loc["public_id"]},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["reserved"]["APR-KIT-2"] == 2   # only 2 were available
    assert result["missing"]["APR-KIT-2"] == 3    # 5 - 2 = 3 missing


def test_approve_order_no_stock_all_missing(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "APR-KIT-3")
    loc = _create_location(auth_client, "APR-WH-3")
    # No stock added

    order = _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 4, "unit_price": "100.00"}],
    )

    response = auth_client.post(
        f"/commercial/orders/{order['public_id']}/approve",
        json={"location_id": loc["public_id"]},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["reserved"]["APR-KIT-3"] == 0
    assert result["missing"]["APR-KIT-3"] == 4


def test_approve_order_already_approved(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "APR-DUP-KIT")
    loc = _create_location(auth_client, "APR-DUP-WH")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 5)
    order = _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 1, "unit_price": "50.00"}],
    )
    auth_client.post(
        f"/commercial/orders/{order['public_id']}/approve",
        json={"location_id": loc["public_id"]},
    )
    # Second approve should fail
    response = auth_client.post(
        f"/commercial/orders/{order['public_id']}/approve",
        json={"location_id": loc["public_id"]},
    )
    assert response.status_code == 422


def test_approve_order_location_not_found(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "APR-NOLOC-KIT")
    order = _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 1, "unit_price": "50.00"}],
    )
    response = auth_client.post(
        f"/commercial/orders/{order['public_id']}/approve",
        json={"location_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


# ── QR lookup ──────────────────────────────────────────────────────────────────


def test_get_order_by_qr_token(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "QR-KIT")
    loc = _create_location(auth_client, "QR-WH")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 5)
    order = _create_order(
        auth_client,
        [{"product_public_id": kit["public_id"], "quantity": 1, "unit_price": "50.00"}],
    )
    result = auth_client.post(
        f"/commercial/orders/{order['public_id']}/approve",
        json={"location_id": loc["public_id"]},
    ).json()

    response = auth_client.get(f"/commercial/orders/qr/{result['qr_token']}")
    assert response.status_code == 200
    assert response.json()["public_id"] == order["public_id"]


def test_qr_not_found(auth_client: TestClient) -> None:
    response = auth_client.get("/commercial/orders/qr/nonexistent-token-xyz")
    assert response.status_code == 404
