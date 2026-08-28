def get_admin_token(client):
    client.post(
        "/auth/register",
        json={
            "name": "Tenant Test Admin",
            "email": "pytest.tenant.admin@example.com",
            "password": "AdminPassword123!",
            "role": "Super Admin",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "pytest.tenant.admin@example.com",
            "password": "AdminPassword123!",
        },
    )

    return response.json()["access_token"]


def test_create_tenant(client):
    token = get_admin_token(client)

    response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Pytest Tenant",
            "email": "pytest.tenant1@example.com",
            "phone": "9876543210",
            "identification_number": "PYTEST-TEN-001",
            "emergency_contact": "Test Contact - 9876500000",
            "address": "Test Address, Hyderabad",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["full_name"] == "Pytest Tenant"
    assert data["email"] == "pytest.tenant1@example.com"
    assert data["identification_number"] == "PYTEST-TEN-001"


def test_duplicate_tenant_email_rejected(client):
    token = get_admin_token(client)

    tenant_data = {
        "full_name": "First Tenant",
        "email": "pytest.duplicate@example.com",
        "phone": "9876543210",
        "identification_number": "PYTEST-DUP-001",
        "emergency_contact": "Test Contact",
        "address": "Hyderabad",
    }

    first_response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json=tenant_data,
    )

    assert first_response.status_code == 200

    duplicate_data = {
        **tenant_data,
        "full_name": "Duplicate Tenant",
        "identification_number": "PYTEST-DUP-002",
    }

    second_response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json=duplicate_data,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Tenant email already exists"
    )


def test_duplicate_identification_number_rejected(client):
    token = get_admin_token(client)

    first_response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Identification Test One",
            "email": "pytest.id.one@example.com",
            "phone": "9876543211",
            "identification_number": "PYTEST-ID-001",
            "emergency_contact": "Test Contact",
            "address": "Hyderabad",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Identification Test Two",
            "email": "pytest.id.two@example.com",
            "phone": "9876543212",
            "identification_number": "PYTEST-ID-001",
            "emergency_contact": "Another Contact",
            "address": "Hyderabad",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Identification number already exists"
    )


def test_get_tenant(client):
    token = get_admin_token(client)

    create_response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Get Tenant Test",
            "email": "pytest.gettenant@example.com",
            "phone": "9876543213",
            "identification_number": "PYTEST-GET-001",
            "emergency_contact": "Test Contact",
            "address": "Hyderabad",
        },
    )

    assert create_response.status_code == 200

    tenant_id = create_response.json()["id"]

    response = client.get(
        f"/tenants/{tenant_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == tenant_id


def test_update_tenant(client):
    token = get_admin_token(client)

    create_response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Update Tenant",
            "email": "pytest.update@example.com",
            "phone": "9876543214",
            "identification_number": "PYTEST-UPD-001",
            "emergency_contact": "Test Contact",
            "address": "Old Address",
        },
    )

    assert create_response.status_code == 200

    tenant_id = create_response.json()["id"]

    response = client.put(
        f"/tenants/{tenant_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "phone": "9999999999",
            "address": "New Address, Hyderabad",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["phone"] == "9999999999"
    assert data["address"] == "New Address, Hyderabad"