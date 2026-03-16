"""Catalog endpoint tests."""
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.domains.auth.models import User


# ── Auth fixture ───────────────────────────────────────────────────────────────

@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, session):
    user = User(
        email="catalog@robotschool.com",
        password_hash=hash_password("pass123"),
        first_name="Catalog",
        last_name="Admin",
    )
    session.add(user)
    session.commit()
    client.post(
        "/auth/login",
        json={"email": "catalog@robotschool.com", "password": "pass123"},
    )
    return client


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_kit(client: TestClient, sku: str = "KIT-001", name: str = "Explorer Kit") -> dict:
    return client.post(
        "/catalog/products",
        json={"sku": sku, "name": name, "type": "KIT"},
    ).json()


def _create_component(
    client: TestClient, sku: str = "COMP-001", name: str = "Arduino Uno"
) -> dict:
    return client.post(
        "/catalog/products",
        json={"sku": sku, "name": name, "type": "COMPONENT"},
    ).json()


# ── Product CRUD ───────────────────────────────────────────────────────────────

def test_create_kit(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/catalog/products",
        json={"sku": "KIT-100", "name": "Starter Kit", "type": "KIT"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "KIT"
    assert data["sku"] == "KIT-100"
    assert "public_id" in data
    assert "id" not in data
    assert data["is_active"] is True


def test_create_component(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/catalog/products",
        json={
            "sku": "COMP-100",
            "name": "Arduino Nano",
            "type": "COMPONENT",
            "cut_file_key": "chassis/nano_v2.dxf",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "COMPONENT"
    assert data["cut_file_key"] == "chassis/nano_v2.dxf"


def test_create_kit_with_cut_file_rejected(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/catalog/products",
        json={"sku": "KIT-BAD", "name": "Bad Kit", "type": "KIT", "cut_file_key": "file.dxf"},
    )
    assert response.status_code == 422


def test_create_product_duplicate_sku(auth_client: TestClient) -> None:
    auth_client.post("/catalog/products", json={"sku": "DUP-001", "name": "P1", "type": "KIT"})
    response = auth_client.post(
        "/catalog/products", json={"sku": "DUP-001", "name": "P2", "type": "COMPONENT"}
    )
    assert response.status_code == 422


def test_list_products(auth_client: TestClient) -> None:
    _create_kit(auth_client, "LIST-KIT")
    _create_component(auth_client, "LIST-COMP")
    response = auth_client.get("/catalog/products")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_get_product(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "GET-KIT")
    response = auth_client.get(f"/catalog/products/{kit['public_id']}")
    assert response.status_code == 200
    assert response.json()["sku"] == "GET-KIT"


def test_get_product_not_found(auth_client: TestClient) -> None:
    response = auth_client.get("/catalog/products/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_patch_product(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "PATCH-KIT")
    response = auth_client.patch(
        f"/catalog/products/{kit['public_id']}",
        json={"name": "Updated Kit Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Kit Name"


def test_soft_delete_product(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "DEL-KIT")
    delete_resp = auth_client.delete(f"/catalog/products/{kit['public_id']}")
    assert delete_resp.status_code == 204

    # Should no longer appear in the default active list
    list_resp = auth_client.get("/catalog/products")
    skus = [p["sku"] for p in list_resp.json()]
    assert "DEL-KIT" not in skus

    # But appears when querying all
    all_resp = auth_client.get("/catalog/products?is_active=false")
    skus_all = [p["sku"] for p in all_resp.json()]
    assert "DEL-KIT" in skus_all


def test_catalog_requires_auth(client: TestClient) -> None:
    assert client.get("/catalog/products").status_code == 401
    assert client.post("/catalog/products", json={}).status_code == 401


# ── BOM ───────────────────────────────────────────────────────────────────────

def test_add_component_to_kit_bom(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "BOM-KIT")
    comp = _create_component(auth_client, "BOM-COMP")

    response = auth_client.post(
        f"/catalog/products/{kit['public_id']}/bom",
        json={"component_id": comp["public_id"], "quantity": 2, "notes": "red LEDs"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["component_sku"] == "BOM-COMP"
    assert data["quantity"] == 2
    assert data["notes"] == "red LEDs"


def test_cannot_add_kit_as_component_of_itself(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "SELF-KIT")

    response = auth_client.post(
        f"/catalog/products/{kit['public_id']}/bom",
        json={"component_id": kit["public_id"], "quantity": 1},
    )
    assert response.status_code == 422


def test_cannot_add_kit_type_as_bom_component(auth_client: TestClient) -> None:
    kit1 = _create_kit(auth_client, "PARENT-KIT")
    kit2 = _create_kit(auth_client, "CHILD-KIT")

    response = auth_client.post(
        f"/catalog/products/{kit1['public_id']}/bom",
        json={"component_id": kit2["public_id"], "quantity": 1},
    )
    assert response.status_code == 422


def test_cannot_add_duplicate_component_to_bom(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "DUP-BOM-KIT")
    comp = _create_component(auth_client, "DUP-BOM-COMP")

    auth_client.post(
        f"/catalog/products/{kit['public_id']}/bom",
        json={"component_id": comp["public_id"], "quantity": 1},
    )
    response = auth_client.post(
        f"/catalog/products/{kit['public_id']}/bom",
        json={"component_id": comp["public_id"], "quantity": 2},
    )
    assert response.status_code == 422


def test_get_bom(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "LIST-BOM-KIT")
    c1 = _create_component(auth_client, "BOM-C1")
    c2 = _create_component(auth_client, "BOM-C2")

    auth_client.post(
        f"/catalog/products/{kit['public_id']}/bom",
        json={"component_id": c1["public_id"], "quantity": 1},
    )
    auth_client.post(
        f"/catalog/products/{kit['public_id']}/bom",
        json={"component_id": c2["public_id"], "quantity": 3},
    )

    response = auth_client.get(f"/catalog/products/{kit['public_id']}/bom")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    skus = {i["component_sku"] for i in items}
    assert skus == {"BOM-C1", "BOM-C2"}


def test_get_bom_on_component_returns_422(auth_client: TestClient) -> None:
    comp = _create_component(auth_client, "NOT-A-KIT")
    response = auth_client.get(f"/catalog/products/{comp['public_id']}/bom")
    assert response.status_code == 422


def test_remove_from_bom(auth_client: TestClient) -> None:
    kit = _create_kit(auth_client, "RM-BOM-KIT")
    comp = _create_component(auth_client, "RM-BOM-COMP")

    auth_client.post(
        f"/catalog/products/{kit['public_id']}/bom",
        json={"component_id": comp["public_id"], "quantity": 1},
    )
    response = auth_client.delete(
        f"/catalog/products/{kit['public_id']}/bom/{comp['public_id']}"
    )
    assert response.status_code == 204

    bom = auth_client.get(f"/catalog/products/{kit['public_id']}/bom").json()
    assert len(bom) == 0
