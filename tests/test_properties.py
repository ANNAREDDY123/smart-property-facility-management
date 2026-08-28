def get_admin_token(client):
    client.post(
        "/auth/register",
        json={
            "name": "Property Test Admin",
            "email": "pytest.property.admin@example.com",
            "password": "AdminPassword123!",
            "role": "Super Admin",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "pytest.property.admin@example.com",
            "password": "AdminPassword123!",
        },
    )

    return response.json()["access_token"]


def test_create_property(client):
    token = get_admin_token(client)

    response = client.post(
        "/properties",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "property_name": "Pytest Green Valley",
            "property_type": "Apartment",
            "address": "Test Main Road",
            "city": "Hyderabad",
            "state": "Telangana",
            "total_area": 50000,
            "total_units": 100,
            "status": "Active",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["property_name"] == "Pytest Green Valley"
    assert data["property_type"] == "Apartment"
    assert data["city"] == "Hyderabad"


def test_tenant_cannot_create_property(client):
    client.post(
        "/auth/register",
        json={
            "name": "Property Test Tenant",
            "email": "pytest.property.tenant@example.com",
            "password": "TenantPassword123!",
            "role": "Tenant",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "pytest.property.tenant@example.com",
            "password": "TenantPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/properties",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "property_name": "Unauthorized Property",
            "property_type": "Apartment",
            "address": "Test Address",
            "city": "Hyderabad",
            "state": "Telangana",
            "total_area": 10000,
            "total_units": 20,
            "status": "Active",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_invalid_property_type(client):
    token = get_admin_token(client)

    response = client.post(
        "/properties",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "property_name": "Invalid Property",
            "property_type": "Hotel",
            "address": "Test Address",
            "city": "Hyderabad",
            "state": "Telangana",
            "total_area": 10000,
            "total_units": 20,
            "status": "Active",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid property type. Allowed values: "
        "Apartment, Villa, Commercial, Office, Warehouse"
    )