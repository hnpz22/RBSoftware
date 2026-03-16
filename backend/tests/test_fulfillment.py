"""Fulfillment domain tests."""
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.domains.auth.models import User


# ── Auth fixture ───────────────────────────────────────────────────────────────


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, session):
    user = User(
        email="fulfillment@robotschool.com",
        password_hash=hash_password("pass123"),
        first_name="Fulfillment",
        last_name="Admin",
    )
    session.add(user)
    session.commit()
    client.post(
        "/auth/login",
        json={"email": "fulfillment@robotschool.com", "password": "pass123"},
    )
    return client


# ── Helpers ────────────────────────────────────────────────────────────────────


def _create_kit(client: TestClient, sku: str, qr_code: str | None = None) -> dict:
    payload = {"sku": sku, "name": sku, "type": "KIT"}
    if qr_code:
        payload["qr_code"] = qr_code
    return client.post("/catalog/products", json=payload).json()


def _create_location(client: TestClient, name: str = "WH") -> dict:
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


def _create_approved_order(
    client: TestClient, product_id: str, qty: int, location_id: str
) -> dict:
    order = client.post(
        "/commercial/orders",
        json={
            "source": "WEB",
            "customer_name": "Test",
            "customer_email": "test@example.com",
            "items": [
                {"product_public_id": product_id, "quantity": qty, "unit_price": "100.00"}
            ],
        },
    ).json()
    client.post(
        f"/commercial/orders/{order['public_id']}/approve",
        json={"location_id": location_id},
    )
    return order


# ── scan_order_qr ──────────────────────────────────────────────────────────────


def test_scan_order_qr(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "SCAN-WH")
    kit = _create_kit(auth_client, "SCAN-KIT", qr_code="QR-SCAN-KIT")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 5)

    order = _create_approved_order(auth_client, kit["public_id"], 2, loc["public_id"])

    # Get the QR token from the order
    order_detail = auth_client.get(f"/commercial/orders/{order['public_id']}").json()
    qr_token = order_detail["qr_token"]
    assert qr_token is not None

    resp = auth_client.post("/fulfillment/scan/order", json={"qr_token": qr_token})
    assert resp.status_code == 200
    data = resp.json()
    assert str(data["order_public_id"]) == order["public_id"]
    assert len(data["items"]) == 1
    assert data["items"][0]["required_qty"] == 2
    assert data["items"][0]["confirmed_qty"] == 0


def test_scan_order_qr_invalid_token(auth_client: TestClient) -> None:
    resp = auth_client.post("/fulfillment/scan/order", json={"qr_token": "bad-token"})
    assert resp.status_code == 404


# ── get_pack_status ────────────────────────────────────────────────────────────


def test_get_pack_status(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "STATUS-WH")
    kit = _create_kit(auth_client, "STATUS-KIT")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 3)
    order = _create_approved_order(auth_client, kit["public_id"], 1, loc["public_id"])

    # Initialise pack items via scan_order_qr
    order_detail = auth_client.get(f"/commercial/orders/{order['public_id']}").json()
    auth_client.post(
        "/fulfillment/scan/order", json={"qr_token": order_detail["qr_token"]}
    )

    resp = auth_client.get(f"/fulfillment/orders/{order['public_id']}/pack-status")
    assert resp.status_code == 200
    data = resp.json()
    assert str(data["order_public_id"]) == order["public_id"]
    assert len(data["items"]) == 1


def test_get_pack_status_not_found(auth_client: TestClient) -> None:
    resp = auth_client.get(
        "/fulfillment/orders/00000000-0000-0000-0000-000000000000/pack-status"
    )
    assert resp.status_code == 404


# ── scan_kit_qr ────────────────────────────────────────────────────────────────


def test_scan_kit_qr(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "KITQR-WH")
    kit = _create_kit(auth_client, "KITQR-KIT", qr_code="QR-KITQR-001")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 5)
    order = _create_approved_order(auth_client, kit["public_id"], 2, loc["public_id"])

    # Initialise pack items
    order_detail = auth_client.get(f"/commercial/orders/{order['public_id']}").json()
    auth_client.post(
        "/fulfillment/scan/order", json={"qr_token": order_detail["qr_token"]}
    )

    resp = auth_client.post(
        "/fulfillment/scan/kit",
        json={"order_public_id": order["public_id"], "product_qr": "QR-KITQR-001"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confirmed_qty"] == 1
    assert data["required_qty"] == 2


def test_scan_kit_qr_invalid_qr(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "BQRKITWH")
    kit = _create_kit(auth_client, "BQRKIT-KIT")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 2)
    order = _create_approved_order(auth_client, kit["public_id"], 1, loc["public_id"])

    order_detail = auth_client.get(f"/commercial/orders/{order['public_id']}").json()
    auth_client.post(
        "/fulfillment/scan/order", json={"qr_token": order_detail["qr_token"]}
    )

    resp = auth_client.post(
        "/fulfillment/scan/kit",
        json={"order_public_id": order["public_id"], "product_qr": "NO-SUCH-QR"},
    )
    assert resp.status_code == 404


def test_scan_kit_qr_over_confirm(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "OVER-WH")
    kit = _create_kit(auth_client, "OVER-KIT", qr_code="QR-OVER-001")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 5)
    order = _create_approved_order(auth_client, kit["public_id"], 1, loc["public_id"])

    order_detail = auth_client.get(f"/commercial/orders/{order['public_id']}").json()
    auth_client.post(
        "/fulfillment/scan/order", json={"qr_token": order_detail["qr_token"]}
    )

    # First scan — OK
    auth_client.post(
        "/fulfillment/scan/kit",
        json={"order_public_id": order["public_id"], "product_qr": "QR-OVER-001"},
    )
    # Second scan — should fail (already fully confirmed)
    resp = auth_client.post(
        "/fulfillment/scan/kit",
        json={"order_public_id": order["public_id"], "product_qr": "QR-OVER-001"},
    )
    assert resp.status_code == 422


# ── close_packing ──────────────────────────────────────────────────────────────


def test_close_packing_moves_inventory(auth_client: TestClient) -> None:
    """close_packing should move RESERVED_WEB → PACKED and set fulfillment_status=PACKED."""
    loc = _create_location(auth_client, "CLOSE-WH")
    kit = _create_kit(auth_client, "CLOSE-KIT", qr_code="QR-CLOSE-001")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 5)
    order = _create_approved_order(auth_client, kit["public_id"], 2, loc["public_id"])

    order_detail = auth_client.get(f"/commercial/orders/{order['public_id']}").json()
    auth_client.post(
        "/fulfillment/scan/order", json={"qr_token": order_detail["qr_token"]}
    )

    # Confirm both units by scanning twice
    for _ in range(2):
        auth_client.post(
            "/fulfillment/scan/kit",
            json={"order_public_id": order["public_id"], "product_qr": "QR-CLOSE-001"},
        )

    resp = auth_client.post(f"/fulfillment/orders/{order['public_id']}/close-packing")
    assert resp.status_code == 200
    data = resp.json()
    assert data["fulfillment_status"] == "PACKED"

    # Verify inventory moved to PACKED
    balances = auth_client.get(
        f"/inventory/balances",
        params={"product_public_id": kit["public_id"]},
    ).json()
    packed = [b for b in balances if b["status"] == "PACKED"]
    assert sum(b["quantity"] for b in packed) == 2


def test_close_packing_not_all_confirmed(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "NOTCONF-WH")
    kit = _create_kit(auth_client, "NOTCONF-KIT", qr_code="QR-NOTCONF-001")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 5)
    order = _create_approved_order(auth_client, kit["public_id"], 2, loc["public_id"])

    order_detail = auth_client.get(f"/commercial/orders/{order['public_id']}").json()
    auth_client.post(
        "/fulfillment/scan/order", json={"qr_token": order_detail["qr_token"]}
    )
    # Only confirm 1 out of 2
    auth_client.post(
        "/fulfillment/scan/kit",
        json={"order_public_id": order["public_id"], "product_qr": "QR-NOTCONF-001"},
    )

    resp = auth_client.post(f"/fulfillment/orders/{order['public_id']}/close-packing")
    assert resp.status_code == 422


# ── ship ───────────────────────────────────────────────────────────────────────


def test_ship_order(auth_client: TestClient) -> None:
    """ship should move PACKED → SHIPPED and set fulfillment_status=SHIPPED."""
    loc = _create_location(auth_client, "SHIP-WH")
    kit = _create_kit(auth_client, "SHIP-KIT", qr_code="QR-SHIP-001")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 3)
    order = _create_approved_order(auth_client, kit["public_id"], 1, loc["public_id"])

    # Scan, confirm, close
    order_detail = auth_client.get(f"/commercial/orders/{order['public_id']}").json()
    auth_client.post(
        "/fulfillment/scan/order", json={"qr_token": order_detail["qr_token"]}
    )
    auth_client.post(
        "/fulfillment/scan/kit",
        json={"order_public_id": order["public_id"], "product_qr": "QR-SHIP-001"},
    )
    auth_client.post(f"/fulfillment/orders/{order['public_id']}/close-packing")

    resp = auth_client.post(f"/fulfillment/orders/{order['public_id']}/ship")
    assert resp.status_code == 200
    assert resp.json()["fulfillment_status"] == "SHIPPED"

    # Verify inventory moved to SHIPPED
    balances = auth_client.get(
        "/inventory/balances",
        params={"product_public_id": kit["public_id"]},
    ).json()
    shipped = [b for b in balances if b["status"] == "SHIPPED"]
    assert sum(b["quantity"] for b in shipped) == 1


def test_ship_not_packed(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "NOPK-WH")
    kit = _create_kit(auth_client, "NOPK-KIT")
    _add_stock(auth_client, kit["public_id"], loc["public_id"], 2)
    order = _create_approved_order(auth_client, kit["public_id"], 1, loc["public_id"])

    # Try to ship without packing first
    resp = auth_client.post(f"/fulfillment/orders/{order['public_id']}/ship")
    assert resp.status_code == 422


def test_fulfillment_requires_auth(client: TestClient) -> None:
    resp = client.get(
        "/fulfillment/orders/00000000-0000-0000-0000-000000000000/pack-status"
    )
    assert resp.status_code == 401
