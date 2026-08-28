def test_register(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test Tenant",
            "email": "pytest.tenant@example.com",
            "password": "TestPassword123!",
            "role": "Tenant",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Test Tenant"
    assert data["email"] == "pytest.tenant@example.com"
    assert data["role"] == "Tenant"
    assert data["is_active"] is True


def test_login(client):
    # Register a separate user for this test
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Login Test User",
            "email": "pytest.login@example.com",
            "password": "TestPassword123!",
            "role": "Tenant",
        },
    )

    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        json={
            "email": "pytest.login@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    # Register user
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Wrong Password User",
            "email": "pytest.wrongpassword@example.com",
            "password": "CorrectPassword123!",
            "role": "Tenant",
        },
    )

    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        json={
            "email": "pytest.wrongpassword@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"