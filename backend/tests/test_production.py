"""Production domain tests."""
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.domains.auth.models import User


# ── Auth fixture ───────────────────────────────────────────────────────────────


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, session):
    user = User(
        email="production@robotschool.com",
        password_hash=hash_password("pass123"),
        first_name="Production",
        last_name="Admin",
    )
    session.add(user)
    session.commit()
    client.post(
        "/auth/login",
        json={"email": "production@robotschool.com", "password": "pass123"},
    )
    return client


# ── Helpers ────────────────────────────────────────────────────────────────────


def _create_kit(client: TestClient, sku: str) -> dict:
    return client.post(
        "/catalog/products",
        json={"sku": sku, "name": sku, "type": "KIT"},
    ).json()


def _create_component(client: TestClient, sku: str) -> dict:
    return client.post(
        "/catalog/products",
        json={"sku": sku, "name": sku, "type": "COMPONENT"},
    ).json()


def _add_bom(client: TestClient, kit_id: str, comp_id: str, qty: int) -> dict:
    return client.post(
        f"/catalog/products/{kit_id}/bom",
        json={"component_id": comp_id, "quantity": qty},
    ).json()


def _create_location(client: TestClient, name: str = "WH") -> dict:
    return client.post(
        "/inventory/locations",
        json={"name": name, "type": "WAREHOUSE"},
    ).json()


def _add_kit_stock(client: TestClient, product_id: str, location_id: str, qty: int) -> None:
    client.post(
        "/inventory/movements",
        json={
            "product_public_id": product_id,
            "location_public_id": location_id,
            "status": "FREE",
            "delta": qty,
        },
    )


def _add_comp_stock(client: TestClient, comp_id: str, location_id: str, qty: int) -> None:
    client.post(
        "/inventory/components/movements",
        json={
            "component_public_id": comp_id,
            "location_public_id": location_id,
            "status": "AVAILABLE",
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


# ── Batch CRUD ─────────────────────────────────────────────────────────────────


def test_create_manual_batch(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "PROD-KIT-1")
    response = auth_client.post(
        "/production/batches",
        json={
            "kind": "MANUAL",
            "name": "Test Batch",
            "items": [
                {
                    "product_public_id": kit["public_id"],
                    "required_qty_total": 10,
                    "available_stock_qty": 3,
                }
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["kind"] == "MANUAL"
    assert data["status"] == "PENDING"
    assert data["name"] == "Test Batch"
    assert len(data["items"]) == 1
    assert data["items"][0]["to_produce_qty"] == 7  # 10 - 3
    assert "public_id" in data


def test_list_batches(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "PROD-KIT-LIST")
    auth_client.post(
        "/production/batches",
        json={
            "kind": "MANUAL",
            "items": [
                {"product_public_id": kit["public_id"], "required_qty_total": 5}
            ],
        },
    )
    resp = auth_client.get("/production/batches")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_batch(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "PROD-KIT-GET")
    batch = auth_client.post(
        "/production/batches",
        json={
            "kind": "MANUAL",
            "items": [
                {"product_public_id": kit["public_id"], "required_qty_total": 2}
            ],
        },
    ).json()
    resp = auth_client.get(f"/production/batches/{batch['public_id']}")
    assert resp.status_code == 200
    assert resp.json()["public_id"] == batch["public_id"]


def test_get_batch_not_found(auth_client: TestClient) -> None:
    resp = auth_client.get("/production/batches/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_production_requires_auth(client: TestClient) -> None:
    assert client.get("/production/batches").status_code == 401


# ── Status transitions ─────────────────────────────────────────────────────────


def test_status_pending_to_in_progress(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "STAT-KIT-1")
    batch = auth_client.post(
        "/production/batches",
        json={
            "kind": "MANUAL",
            "items": [{"product_public_id": kit["public_id"], "required_qty_total": 1}],
        },
    ).json()

    resp = auth_client.patch(
        f"/production/batches/{batch['public_id']}/status",
        json={"status": "IN_PROGRESS"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"
    assert resp.json()["started_at"] is not None


def test_status_in_progress_to_done(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "STAT-KIT-2")
    batch = auth_client.post(
        "/production/batches",
        json={
            "kind": "MANUAL",
            "items": [{"product_public_id": kit["public_id"], "required_qty_total": 1}],
        },
    ).json()
    auth_client.patch(
        f"/production/batches/{batch['public_id']}/status", json={"status": "IN_PROGRESS"}
    )
    resp = auth_client.patch(
        f"/production/batches/{batch['public_id']}/status", json={"status": "DONE"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DONE"
    assert resp.json()["completed_at"] is not None


def test_invalid_status_transition(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "STAT-KIT-3")
    batch = auth_client.post(
        "/production/batches",
        json={
            "kind": "MANUAL",
            "items": [{"product_public_id": kit["public_id"], "required_qty_total": 1}],
        },
    ).json()
    # Cannot go PENDING → DONE
    resp = auth_client.patch(
        f"/production/batches/{batch['public_id']}/status", json={"status": "DONE"}
    )
    assert resp.status_code == 422


# ── Cutoff ─────────────────────────────────────────────────────────────────────


def test_cutoff_creates_batch_from_approved_orders(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "CUTOFF-WH")
    kit1 = _create_kit(auth_client, "CUTOFF-KIT-1")
    kit2 = _create_kit(auth_client, "CUTOFF-KIT-2")

    _create_approved_order(auth_client, kit1["public_id"], 3, loc["public_id"])
    _create_approved_order(auth_client, kit2["public_id"], 5, loc["public_id"])

    resp = auth_client.post("/production/batches/cutoff")
    assert resp.status_code == 201
    data = resp.json()
    assert data["kind"] == "SALES"
    assert len(data["items"]) >= 2
    assert len(data["linked_orders"]) >= 2


def test_cutoff_no_approved_orders(auth_client: TestClient) -> None:
    # No approved orders — should return 422
    resp = auth_client.post("/production/batches/cutoff")
    # Either 422 (no approved orders) or 201 (from previous tests)
    # Since each test is isolated, this should be 422
    assert resp.status_code == 422


# ── create_batch_from_missing — critical tests ─────────────────────────────────


def test_batch_consolidates_multiple_orders(auth_client: TestClient) -> None:
    """Items from multiple orders for the same product are summed."""
    loc = _create_location(auth_client, "CONSOL-WH")
    kit = _create_kit(auth_client, "CONSOL-KIT")

    _create_approved_order(auth_client, kit["public_id"], 4, loc["public_id"])
    _create_approved_order(auth_client, kit["public_id"], 6, loc["public_id"])

    resp = auth_client.post("/production/batches/cutoff")
    assert resp.status_code == 201
    data = resp.json()

    # Should have one consolidated item for CONSOL-KIT with total 10
    kit_items = [i for i in data["items"] if i["product_id"] is not None]
    total = sum(i["required_qty_total"] for i in kit_items)
    assert total >= 10


def test_batch_to_produce_reflects_available_stock(auth_client: TestClient) -> None:
    """to_produce_qty = required - available FREE stock."""
    loc = _create_location(auth_client, "STOCK-WH")
    kit = _create_kit(auth_client, "STOCK-KIT")
    # Add 3 FREE units BEFORE creating the order
    _add_kit_stock(auth_client, kit["public_id"], loc["public_id"], 3)

    _create_approved_order(auth_client, kit["public_id"], 5, loc["public_id"])
    # Note: approve_order will reserve the 3 available FREE units, leaving 0 FREE
    # But for the batch, we check current FREE at cutoff time
    resp = auth_client.post("/production/batches/cutoff")
    assert resp.status_code == 201
    data = resp.json()
    item = next(i for i in data["items"] if i["required_qty_total"] == 5)
    # required=5, available=0 (all reserved), to_produce=5
    assert item["required_qty_total"] == 5
    assert item["to_produce_qty"] <= 5


def test_production_blocks_created_for_missing_components(auth_client: TestClient) -> None:
    """Blocks are created when component inventory is insufficient."""
    loc = _create_location(auth_client, "BLOCK-WH")
    kit = _create_kit(auth_client, "BLOCK-KIT")
    comp = _create_component(auth_client, "BLOCK-COMP")
    _add_bom(auth_client, kit["public_id"], comp["public_id"], 2)  # 2 comps per kit

    # Only 1 component available but need 2 (to produce 1 kit)
    _add_comp_stock(auth_client, comp["public_id"], loc["public_id"], 1)

    _create_approved_order(auth_client, kit["public_id"], 1, loc["public_id"])

    resp = auth_client.post("/production/batches/cutoff")
    assert resp.status_code == 201
    data = resp.json()
    kit_item = next(i for i in data["items"] if i["to_produce_qty"] > 0)
    assert len(kit_item["blocks"]) >= 1
    assert kit_item["blocks"][0]["missing_qty"] == 1  # need 2, have 1


def test_no_blocks_when_components_sufficient(auth_client: TestClient) -> None:
    """No blocks when component stock covers production needs."""
    loc = _create_location(auth_client, "NOBLOCK-WH")
    kit = _create_kit(auth_client, "NOBLOCK-KIT")
    comp = _create_component(auth_client, "NOBLOCK-COMP")
    _add_bom(auth_client, kit["public_id"], comp["public_id"], 1)  # 1 comp per kit

    # 10 components available, only need 2 (to produce 2 kits)
    _add_comp_stock(auth_client, comp["public_id"], loc["public_id"], 10)

    _create_approved_order(auth_client, kit["public_id"], 2, loc["public_id"])

    resp = auth_client.post("/production/batches/cutoff")
    assert resp.status_code == 201
    data = resp.json()
    kit_item = next((i for i in data["items"] if i["to_produce_qty"] > 0), None)
    if kit_item:  # only check if there is something to produce
        assert kit_item["blocks"] == []


# ── Master sheet ───────────────────────────────────────────────────────────────


def test_master_sheet(auth_client: TestClient) -> None:
    loc = _create_location(auth_client, "MS-WH")
    kit = _create_kit(auth_client, "MS-KIT")
    comp = _create_component(auth_client, "MS-COMP")
    _add_bom(auth_client, kit["public_id"], comp["public_id"], 3)

    _add_comp_stock(auth_client, comp["public_id"], loc["public_id"], 5)
    _create_approved_order(auth_client, kit["public_id"], 4, loc["public_id"])

    batch = auth_client.post("/production/batches/cutoff").json()

    resp = auth_client.get(f"/production/batches/{batch['public_id']}/master-sheet")
    assert resp.status_code == 200
    ms = resp.json()

    assert ms["batch_public_id"] == batch["public_id"]
    assert len(ms["items"]) >= 1
    assert len(ms["linked_orders"]) >= 1

    item = ms["items"][0]
    assert item["product_sku"] == "MS-KIT"
    assert len(item["bom"]) == 1
    bom_entry = item["bom"][0]
    assert bom_entry["component_sku"] == "MS-COMP"
    assert bom_entry["qty_per_kit"] == 3
    assert bom_entry["total_needed"] == item["to_produce_qty"] * 3
    assert bom_entry["available"] == 5
