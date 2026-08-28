import uuid


def get_admin_token(client):
    unique = uuid.uuid4().hex[:8]
    email = f"pytest.maintenance.api.admin.{unique}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Maintenance API Admin {unique}",
            "email": email,
            "password": "AdminPassword123!",
            "role": "Super Admin",
        },
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "AdminPassword123!",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def create_test_unit(client, token):
    unique = uuid.uuid4().hex[:8]

    property_response = client.post(
        "/properties",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_name": f"Maintenance API Property {unique}",
            "property_type": "Apartment",
            "address": "Maintenance API Road",
            "city": "Hyderabad",
            "state": "Telangana",
            "total_area": 50000,
            "total_units": 100,
            "status": "Active",
        },
    )

    assert property_response.status_code == 200

    property_id = property_response.json()["id"]

    building_response = client.post(
        "/buildings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_id": property_id,
            "building_name": f"Maintenance API Tower {unique}",
            "number_of_floors": 10,
            "total_units": 100,
        },
    )

    assert building_response.status_code == 200

    building_id = building_response.json()["id"]

    unit_response = client.post(
        "/units",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "building_id": building_id,
            "unit_number": f"MAINT-{unique}",
            "floor_number": 1,
            "unit_type": "2BHK",
            "area": 1200,
            "monthly_rent": 25000,
            "status": "Available",
        },
    )

    assert unit_response.status_code == 200

    return unit_response.json()["id"]


def create_maintenance_staff(client):
    unique = uuid.uuid4().hex[:8]
    email = f"pytest.maintenance.staff.{unique}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "name": f"Maintenance Staff {unique}",
            "email": email,
            "password": "StaffPassword123!",
            "role": "Maintenance Staff",
        },
    )

    assert response.status_code == 200

    # The registration response gives us the user ID.
    return response.json()["id"]


def create_test_request(client, token):
    unit_id = create_test_unit(
        client,
        token,
    )

    response = client.post(
        "/maintenance/requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "category": "Plumbing",
            "title": "Leaking kitchen tap",
            "description": "Kitchen tap is leaking continuously.",
            "priority": "High",
            "estimated_cost": 1500,
            "actual_cost": 0,
            "status": "Open",
        },
    )

    assert response.status_code == 200

    return response.json()


def test_create_maintenance_request_api(client):
    token = get_admin_token(client)

    request_data = create_test_request(
        client,
        token,
    )

    assert request_data["category"] == "Plumbing"
    assert request_data["priority"] == "High"
    assert request_data["status"] == "Open"
    assert request_data["estimated_cost"] == 1500
    assert request_data["actual_cost"] == 0


def test_get_maintenance_requests_api(client):
    token = get_admin_token(client)

    request_data = create_test_request(
        client,
        token,
    )

    response = client.get(
        "/maintenance/requests",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    requests = response.json()

    assert isinstance(requests, list)
    assert any(
        item["id"] == request_data["id"]
        for item in requests
    )


def test_get_maintenance_request_by_id_api(client):
    token = get_admin_token(client)

    request_data = create_test_request(
        client,
        token,
    )

    request_id = request_data["id"]

    response = client.get(
        f"/maintenance/requests/{request_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == request_id


def test_assign_maintenance_request_api(client):
    token = get_admin_token(client)

    request_data = create_test_request(
        client,
        token,
    )

    staff_id = create_maintenance_staff(client)

    request_id = request_data["id"]

    response = client.put(
        f"/maintenance/requests/{request_id}/assign",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "staff_id": staff_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["assigned_staff"] == staff_id
    assert data["status"] == "Assigned"


def test_update_maintenance_status_api(client):
    token = get_admin_token(client)

    request_data = create_test_request(
        client,
        token,
    )

    request_id = request_data["id"]

    response = client.put(
        f"/maintenance/requests/{request_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "status": "In Progress",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "In Progress"


def test_emergency_maintenance_request_api(client):
    token = get_admin_token(client)

    unit_id = create_test_unit(
        client,
        token,
    )

    response = client.post(
        "/maintenance/requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "category": "Electrical",
            "title": "Electrical emergency",
            "description": "Power failure with exposed wiring.",
            "priority": "Emergency",
            "estimated_cost": 5000,
            "actual_cost": 0,
            "status": "Open",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["priority"] == "Emergency"
    assert data["status"] == "Open"


def test_invalid_maintenance_staff_rejected(client):
    token = get_admin_token(client)

    request_data = create_test_request(
        client,
        token,
    )

    # Create a normal Tenant user.
    unique = uuid.uuid4().hex[:8]

    tenant_response = client.post(
        "/auth/register",
        json={
            "name": f"Normal Tenant {unique}",
            "email": f"pytest.normal.tenant.{unique}@example.com",
            "password": "TenantPassword123!",
            "role": "Tenant",
        },
    )

    assert tenant_response.status_code == 200

    tenant_id = tenant_response.json()["id"]

    response = client.put(
        f"/maintenance/requests/{request_data['id']}/assign",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "staff_id": tenant_id,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "User is not maintenance staff"
    )