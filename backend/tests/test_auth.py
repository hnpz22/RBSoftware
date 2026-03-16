"""Auth endpoint tests."""
from fastapi.testclient import TestClient


def test_login_success(client: TestClient, test_user) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "test@robotschool.com", "password": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@robotschool.com"
    assert data["first_name"] == "Test"
    assert "id" not in data  # internal id must never be exposed
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_login_wrong_password(client: TestClient, test_user) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "test@robotschool.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "nobody@robotschool.com", "password": "secret123"},
    )
    assert response.status_code == 401


def test_refresh_token(client: TestClient, test_user) -> None:
    login = client.post(
        "/auth/login",
        json={"email": "test@robotschool.com", "password": "secret123"},
    )
    assert login.status_code == 200

    response = client.post("/auth/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@robotschool.com"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_refresh_without_cookie_returns_401(client: TestClient) -> None:
    response = client.post("/auth/refresh")
    assert response.status_code == 401


def test_me_authenticated(client: TestClient, test_user) -> None:
    client.post(
        "/auth/login",
        json={"email": "test@robotschool.com", "password": "secret123"},
    )
    response = client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@robotschool.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"


def test_me_unauthenticated(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_clears_cookies(client: TestClient, test_user) -> None:
    client.post(
        "/auth/login",
        json={"email": "test@robotschool.com", "password": "secret123"},
    )
    response = client.post("/auth/logout")
    assert response.status_code == 204
    # After logout, /me must reject the request
    me = client.get("/auth/me")
    assert me.status_code == 401
