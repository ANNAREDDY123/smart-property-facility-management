import uuid


def unique_id():
    return uuid.uuid4().hex[:8]


def get_admin_token(client):
    unique = unique_id()
    email = f"pytest.maintenance.admin.{unique}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Maintenance Test Admin {unique}",
            "email": email,
            "password": "AdminPassword123!",
            "role": "Super Admin",
        },
    )

    assert register_response.status_code == 200, (
        f"Admin registration failed: "
        f"{register_response.status_code} "
        f"{register_response.text}"
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "AdminPassword123!",
        },
    )

    assert login_response.status_code == 200, (
        f"Admin login failed: "
        f"{login_response.status_code} "
        f"{login_response.text}"
    )

    return login_response.json()["access_token"]


def create_test_tenant(client, token):
    unique = unique_id()

    response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": f"Maintenance Test Tenant {unique}",
            "email": f"pytest.maintenance.tenant.{unique}@example.com",
            "phone": f"98765{unique[:5]}",
            "identification_number": f"PYTEST-MNT-{unique}",
            "emergency_contact": "Test Contact",
            "address": "Hyderabad",
        },
    )

    assert response.status_code == 200, (
        f"Tenant creation failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    return response.json()["id"]


def create_test_unit(client, token):
    unique = unique_id()

    property_response = client.post(
        "/properties",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_name": f"Maintenance Test Property {unique}",
            "property_type": "Apartment",
            "address": f"Maintenance Road {unique}",
            "city": "Hyderabad",
            "state": "Telangana",
            "total_area": 50000,
            "total_units": 100,
            "status": "Active",
        },
    )

    assert property_response.status_code == 200, (
        f"Property creation failed: "
        f"{property_response.status_code} "
        f"{property_response.text}"
    )

    property_id = property_response.json()["id"]

    building_response = client.post(
        "/buildings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_id": property_id,
            "building_name": f"Maintenance Tower {unique}",
            "number_of_floors": 10,
            "total_units": 100,
        },
    )

    assert building_response.status_code == 200, (
        f"Building creation failed: "
        f"{building_response.status_code} "
        f"{building_response.text}"
    )

    building_id = building_response.json()["id"]

    unit_response = client.post(
        "/units",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "building_id": building_id,
            "unit_number": f"MNT-{unique}",
            "floor_number": 1,
            "unit_type": "2BHK",
            "area": 1200,
            "monthly_rent": 25000,
            "status": "Available",
        },
    )

    assert unit_response.status_code == 200, (
        f"Unit creation failed: "
        f"{unit_response.status_code} "
        f"{unit_response.text}"
    )

    return unit_response.json()["id"]


def create_test_maintenance_request(client, token):
    tenant_id = create_test_tenant(client, token)
    unit_id = create_test_unit(client, token)

    response = client.post(
        "/maintenance-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "tenant_id": tenant_id,
            "title": "Water leakage",
            "description": "Bathroom pipe is leaking.",
            "priority": "High",
            "status": "Open",
        },
    )

    assert response.status_code == 200, (
        f"Maintenance request creation failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    return response.json()


def test_create_maintenance_request(client):
    token = get_admin_token(client)

    request = create_test_maintenance_request(
        client,
        token,
    )

    assert request["id"] > 0
    assert request["unit_id"] > 0
    assert request["tenant_id"] > 0
    assert request["title"] == "Water leakage"
    assert request["description"] == "Bathroom pipe is leaking."
    assert request["priority"] == "High"
    assert request["status"] == "Open"


def test_get_maintenance_requests(client):
    token = get_admin_token(client)

    request = create_test_maintenance_request(
        client,
        token,
    )

    response = client.get(
        "/maintenance-requests",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    requests = response.json()

    assert isinstance(requests, list)
    assert any(
        item["id"] == request["id"]
        for item in requests
    )


def test_get_maintenance_request_by_id(client):
    token = get_admin_token(client)

    request = create_test_maintenance_request(
        client,
        token,
    )

    request_id = request["id"]

    response = client.get(
        f"/maintenance-requests/{request_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == request_id
    assert data["title"] == "Water leakage"


def test_update_maintenance_request(client):
    token = get_admin_token(client)

    request = create_test_maintenance_request(
        client,
        token,
    )

    request_id = request["id"]

    response = client.put(
        f"/maintenance-requests/{request_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated water leakage",
            "description": "Pipe requires urgent replacement.",
            "priority": "Critical",
            "status": "In Progress",
        },
    )

    assert response.status_code == 200, (
        f"Maintenance update failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    data = response.json()

    assert data["id"] == request_id
    assert data["title"] == "Updated water leakage"
    assert data["priority"] == "Critical"
    assert data["status"] == "In Progress"


def test_create_maintenance_request_invalid_unit(client):
    token = get_admin_token(client)

    response = client.post(
        "/maintenance-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": 999999,
            "tenant_id": None,
            "title": "Invalid unit test",
            "description": "Testing invalid unit.",
            "priority": "High",
            "status": "Open",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unit not found"


def test_create_maintenance_request_invalid_priority(client):
    token = get_admin_token(client)

    unit_id = create_test_unit(client, token)

    response = client.post(
        "/maintenance-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "tenant_id": None,
            "title": "Invalid priority test",
            "description": "Testing invalid priority.",
            "priority": "Urgent",
            "status": "Open",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid maintenance priority"
    )


def test_create_maintenance_request_invalid_status(client):
    token = get_admin_token(client)

    unit_id = create_test_unit(client, token)

    response = client.post(
        "/maintenance-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "tenant_id": None,
            "title": "Invalid status test",
            "description": "Testing invalid status.",
            "priority": "Medium",
            "status": "InvalidStatus",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid maintenance status"
    )


def test_delete_maintenance_request(client):
    token = get_admin_token(client)

    request = create_test_maintenance_request(
        client,
        token,
    )

    request_id = request["id"]

    response = client.delete(
        f"/maintenance-requests/{request_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "Maintenance request deleted successfully"
    )

    get_response = client.get(
        f"/maintenance-requests/{request_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 404
    assert (
        get_response.json()["detail"]
        == "Maintenance request not found"
    )