import pytest


def test_get_current_user(client, test_user_data):
    """Тест получения информации о текущем пользователе"""
    # Регистрируем и логинимся
    client.post("/api/v1/auth/register", json=test_user_data)

    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Получаем информацию о пользователе
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]


def test_protected_endpoint_without_token(client):
    """Тест защищенного endpoint без токена"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_protected_endpoint_invalid_token(client):
    """Тест защищенного endpoint с неверным токеном"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
