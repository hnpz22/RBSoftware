"""Integrations domain tests — WooCommerce sync."""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.domains.auth.models import User


# ── Auth fixture ───────────────────────────────────────────────────────────────


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, session):
    user = User(
        email="integrations@robotschool.com",
        password_hash=hash_password("pass123"),
        first_name="Integrations",
        last_name="Admin",
    )
    session.add(user)
    session.commit()
    client.post(
        "/auth/login",
        json={"email": "integrations@robotschool.com", "password": "pass123"},
    )
    return client


# ── Helpers ────────────────────────────────────────────────────────────────────


def _create_kit(client: TestClient, sku: str) -> dict:
    return client.post(
        "/catalog/products",
        json={"sku": sku, "name": sku, "type": "KIT"},
    ).json()


def _wc_order(wc_id: int, sku: str, qty: int = 2, price: str = "99.00") -> dict:
    """Build a minimal WooCommerce order payload."""
    return {
        "id": wc_id,
        "status": "processing",
        "billing": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@woo.test",
            "phone": "+34600000001",
            "address_1": "Calle Test 1",
            "city": "Madrid",
            "state": "MD",
            "postcode": "28001",
            "country": "ES",
        },
        "shipping": {
            "address_1": "Calle Test 1",
            "city": "Madrid",
            "country": "ES",
        },
        "customer_note": "Test order",
        "date_modified": "2026-03-15T00:00:00",
        "line_items": [
            {
                "id": 1,
                "product_id": 999,
                "name": sku,
                "sku": sku,
                "quantity": qty,
                "price": price,
            }
        ],
    }


# ── Status ─────────────────────────────────────────────────────────────────────


def test_status_never_synced(auth_client: TestClient) -> None:
    resp = auth_client.get("/integrations/woocommerce/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["integration_name"] == "woocommerce"
    assert data["status"] == "NEVER"
    assert data["last_synced_at"] is None


def test_integrations_requires_auth(client: TestClient) -> None:
    assert client.get("/integrations/woocommerce/status").status_code == 401


# ── Webhook: process_wc_order_payload ─────────────────────────────────────────


def test_webhook_creates_order(auth_client: TestClient, client: TestClient) -> None:
    """POST webhook with valid WC payload creates a SalesOrder."""
    kit = _create_kit(auth_client, "WOO-KIT-1")
    payload = _wc_order(wc_id=1001, sku="WOO-KIT-1", qty=2)

    resp = client.post("/integrations/webhooks/woocommerce", json=payload)
    assert resp.status_code == 200
    assert resp.json()["action"] == "created"

    # Verify order exists in commercial domain
    orders = auth_client.get("/commercial/orders").json()
    woo_order = next((o for o in orders if o.get("external_id") == "1001"), None)
    assert woo_order is not None
    assert woo_order["customer_name"] == "John Doe"
    assert woo_order["customer_email"] == "john@woo.test"
    assert woo_order["source"] == "WEB"


def test_webhook_updates_pending_order(auth_client: TestClient, client: TestClient) -> None:
    """Second webhook for same WC ID updates customer info if order is PENDING."""
    _create_kit(auth_client, "WOO-KIT-2")
    payload = _wc_order(wc_id=1002, sku="WOO-KIT-2")
    client.post("/integrations/webhooks/woocommerce", json=payload)

    # Update billing name
    payload["billing"]["first_name"] = "Jane"
    resp = client.post("/integrations/webhooks/woocommerce", json=payload)
    assert resp.status_code == 200
    assert resp.json()["action"] == "updated"

    orders = auth_client.get("/commercial/orders").json()
    woo_order = next(o for o in orders if o.get("external_id") == "1002")
    assert woo_order["customer_name"] == "Jane Doe"


def test_webhook_skips_unknown_sku(auth_client: TestClient, client: TestClient) -> None:
    """Webhook with unknown SKU returns action=skipped, no order created."""
    payload = _wc_order(wc_id=1003, sku="DOES-NOT-EXIST")
    resp = client.post("/integrations/webhooks/woocommerce", json=payload)
    assert resp.status_code == 200
    assert resp.json()["action"] == "skipped"

    orders = auth_client.get("/commercial/orders").json()
    assert not any(o.get("external_id") == "1003" for o in orders)


def test_webhook_skips_update_when_approved(
    auth_client: TestClient, client: TestClient
) -> None:
    """Webhook does not update an order that has already been approved."""
    from app.core.security import hash_password

    kit = _create_kit(auth_client, "WOO-KIT-4")
    payload = _wc_order(wc_id=1004, sku="WOO-KIT-4")
    client.post("/integrations/webhooks/woocommerce", json=payload)

    # Approve the order
    orders = auth_client.get("/commercial/orders").json()
    woo_order = next(o for o in orders if o.get("external_id") == "1004")
    loc = auth_client.post(
        "/inventory/locations",
        json={"name": "WOO-WH", "type": "WAREHOUSE"},
    ).json()
    auth_client.post(
        f"/commercial/orders/{woo_order['public_id']}/approve",
        json={"location_id": loc["public_id"]},
    )

    # Send updated webhook — should be skipped
    payload["billing"]["first_name"] = "Changed"
    resp = client.post("/integrations/webhooks/woocommerce", json=payload)
    assert resp.status_code == 200
    assert resp.json()["action"] == "skipped"

    orders = auth_client.get("/commercial/orders").json()
    woo_order = next(o for o in orders if o.get("external_id") == "1004")
    assert woo_order["customer_name"] == "John Doe"  # unchanged


# ── Manual sync (mocked fetch) ─────────────────────────────────────────────────


def test_manual_sync_with_mock(auth_client: TestClient, session, monkeypatch) -> None:
    """POST /sync processes orders returned by a mocked fetch function."""
    from app.domains.integrations.routes.woocommerce import _svc

    _create_kit(auth_client, "WOO-SYNC-KIT")

    def mock_fetch(after: datetime) -> list[dict]:
        return [_wc_order(wc_id=2001, sku="WOO-SYNC-KIT", qty=3)]

    monkeypatch.setattr(_svc, "_fetch_fn", mock_fetch)

    resp = auth_client.post("/integrations/woocommerce/sync", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["orders_created"] == 1
    assert data["orders_processed"] == 1
    assert data["status"] == "OK"

    # Status should now show last_synced_at
    status_resp = auth_client.get("/integrations/woocommerce/status").json()
    assert status_resp["status"] == "OK"
    assert status_resp["last_synced_at"] is not None


def test_manual_sync_updates_cursor(auth_client: TestClient, monkeypatch) -> None:
    """Second sync with same WC ID counts as updated, not created."""
    from app.domains.integrations.routes.woocommerce import _svc

    _create_kit(auth_client, "WOO-CURSOR-KIT")

    def mock_fetch(after: datetime) -> list[dict]:
        return [_wc_order(wc_id=3001, sku="WOO-CURSOR-KIT")]

    monkeypatch.setattr(_svc, "_fetch_fn", mock_fetch)

    auth_client.post("/integrations/woocommerce/sync", json={})
    resp = auth_client.post("/integrations/woocommerce/sync", json={})
    data = resp.json()
    assert data["orders_created"] == 0
    assert data["orders_updated"] == 1


def test_manual_sync_no_woo_url(auth_client: TestClient, monkeypatch) -> None:
    """Sync without WOO_URL configured returns 503."""
    from app.domains.integrations.routes.woocommerce import _svc
    from app.core import config

    monkeypatch.setattr(_svc, "_fetch_fn", None)
    monkeypatch.setattr(config.settings, "woo_url", None)

    resp = auth_client.post("/integrations/woocommerce/sync", json={})
    assert resp.status_code == 503


def test_webhook_invalid_json(client: TestClient) -> None:
    resp = client.post(
        "/integrations/webhooks/woocommerce",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
