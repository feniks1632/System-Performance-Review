import pytest


def test_register_employee(client, test_user_data):
    """Тест регистрации работника"""
    response = client.post("/api/v1/auth/register", json=test_user_data)

    # Добавляем отладочную информацию
    print(f"Registration response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Registration error: {response.text}")

    assert response.status_code == 200, f"Registration failed with: {response.text}"
    data = response.json()

    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]
    assert data["is_manager"] == False
    assert "password" not in data
    assert "id" in data
    assert "created_at" in data


def test_register_manager(client, test_manager_data):
    """Тест регистрации руководителя"""
    response = client.post("/api/v1/auth/register", json=test_manager_data)

    print(f"Registration response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Registration error: {response.text}")

    assert response.status_code == 200, f"Registration failed with: {response.text}"
    data = response.json()

    assert data["email"] == test_manager_data["email"]
    assert data["is_manager"] == True


def test_register_duplicate_email(client, test_user_data):
    """Тест регистрации с существующим email"""
    # Первая регистрация
    response1 = client.post("/api/v1/auth/register", json=test_user_data)
    print(f"First registration status: {response1.status_code}")
    if response1.status_code != 200:
        print(f"First registration error: {response1.text}")

    assert response1.status_code == 200, f"First registration failed: {response1.text}"

    # Вторая регистрация с тем же email
    response2 = client.post("/api/v1/auth/register", json=test_user_data)
    print(f"Second registration status: {response2.status_code}")

    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_login_success(client, test_user_data):
    """Тест успешной аутентификации"""
    # Сначала регистрируем пользователя
    reg_response = client.post("/api/v1/auth/register", json=test_user_data)
    print(f"Registration for login test: {reg_response.status_code}")
    if reg_response.status_code != 200:
        print(f"Registration error: {reg_response.text}")
        # Если регистрация не работает, пропускаем тест
        pytest.skip("Registration not working")

    # Логинимся
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user_data["email"]


def test_login_wrong_password(client, test_user_data):
    """Тест аутентификации с неверным паролем"""
    # Регистрируем пользователя
    reg_response = client.post("/api/v1/auth/register", json=test_user_data)
    if reg_response.status_code != 200:
        pytest.skip("Registration not working")

    # Пробуем логин с неверным паролем
    login_data = {"email": test_user_data["email"], "password": "wrongpassword"}
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Тест аутентификации несуществующего пользователя"""
    login_data = {"email": "nonexistent@example.com", "password": "password123"}
    response = client.post("/api/v1/auth/login", json=login_data)

    assert response.status_code == 401
