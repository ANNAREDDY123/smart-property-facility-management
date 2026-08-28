import uuid


def get_admin_token(client):
    unique = uuid.uuid4().hex[:8]
    email = f"pytest.parking.admin.{unique}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Parking Admin {unique}",
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


def create_test_property(client, token):
    unique = uuid.uuid4().hex[:8]

    response = client.post(
        "/properties",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_name": f"Parking Property {unique}",
            "property_type": "Apartment",
            "address": "Parking Test Road",
            "city": "Hyderabad",
            "state": "Telangana",
            "total_area": 50000,
            "total_units": 100,
            "status": "Active",
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


def create_test_tenant(client, token):
    unique = uuid.uuid4().hex[:8]

    response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": f"Parking Tenant {unique}",
            "email": f"parking.tenant.{unique}@example.com",
            "phone": "9876543210",
            "identification_number": f"PARK-{unique}",
            "emergency_contact": "9876500000",
            "address": "Parking Test Address",
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


def create_parking(client, token, property_id, parking_number):
    response = client.post(
        "/parking",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_id": property_id,
            "parking_number": parking_number,
            "status": "Available",
        },
    )

    assert response.status_code == 200

    return response.json()


def test_create_parking(client):
    token = get_admin_token(client)
    property_id = create_test_property(client, token)

    parking = create_parking(
        client,
        token,
        property_id,
        f"P-{uuid.uuid4().hex[:8]}",
    )

    assert parking["property_id"] == property_id
    assert parking["status"] == "Available"
    assert parking["vehicle_number"] is None
    assert parking["tenant_id"] is None


def test_get_parking(client):
    token = get_admin_token(client)
    property_id = create_test_property(client, token)

    parking = create_parking(
        client,
        token,
        property_id,
        f"P-{uuid.uuid4().hex[:8]}",
    )

    response = client.get(
        "/parking",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    parking_list = response.json()

    assert any(
        item["id"] == parking["id"]
        for item in parking_list
    )


def test_assign_parking(client):
    token = get_admin_token(client)
    property_id = create_test_property(client, token)
    tenant_id = create_test_tenant(client, token)

    parking = create_parking(
        client,
        token,
        property_id,
        f"P-{uuid.uuid4().hex[:8]}",
    )

    response = client.post(
        f"/parking/{parking['id']}/assign",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_number": f"TS09-{uuid.uuid4().hex[:6].upper()}",
            "vehicle_type": "Car",
            "tenant_id": tenant_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Assigned"
    assert data["tenant_id"] == tenant_id
    assert data["vehicle_number"] is not None
    assert data["vehicle_type"] == "Car"


def test_assign_already_assigned_parking_rejected(client):
    token = get_admin_token(client)
    property_id = create_test_property(client, token)
    tenant_id = create_test_tenant(client, token)

    parking = create_parking(
        client,
        token,
        property_id,
        f"P-{uuid.uuid4().hex[:8]}",
    )

    vehicle_number = f"TS10-{uuid.uuid4().hex[:6].upper()}"

    first_response = client.post(
        f"/parking/{parking['id']}/assign",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_number": vehicle_number,
            "vehicle_type": "Car",
            "tenant_id": tenant_id,
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/parking/{parking['id']}/assign",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_number": f"TS11-{uuid.uuid4().hex[:6].upper()}",
            "vehicle_type": "SUV",
            "tenant_id": tenant_id,
        },
    )

    assert second_response.status_code == 400
    assert (
        second_response.json()["detail"]
        == "Parking slot is already assigned"
    )


def test_duplicate_active_vehicle_rejected(client):
    token = get_admin_token(client)
    property_id = create_test_property(client, token)
    tenant_id = create_test_tenant(client, token)

    parking1 = create_parking(
        client,
        token,
        property_id,
        f"P-{uuid.uuid4().hex[:8]}",
    )

    parking2 = create_parking(
        client,
        token,
        property_id,
        f"P-{uuid.uuid4().hex[:8]}",
    )

    vehicle_number = f"TS12-{uuid.uuid4().hex[:6].upper()}"

    first_response = client.post(
        f"/parking/{parking1['id']}/assign",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_number": vehicle_number,
            "vehicle_type": "Car",
            "tenant_id": tenant_id,
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/parking/{parking2['id']}/assign",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_number": vehicle_number,
            "vehicle_type": "Car",
            "tenant_id": tenant_id,
        },
    )

    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "Vehicle is already assigned to another parking slot"
    )


def test_blocked_parking_cannot_be_assigned(client):
    token = get_admin_token(client)
    property_id = create_test_property(client, token)
    tenant_id = create_test_tenant(client, token)

    response = client.post(
        "/parking",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_id": property_id,
            "parking_number": f"P-{uuid.uuid4().hex[:8]}",
            "status": "Blocked",
        },
    )

    assert response.status_code == 200

    parking = response.json()

    assign_response = client.post(
        f"/parking/{parking['id']}/assign",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_number": f"TS13-{uuid.uuid4().hex[:6].upper()}",
            "vehicle_type": "Car",
            "tenant_id": tenant_id,
        },
    )

    assert assign_response.status_code == 400
    assert (
        assign_response.json()["detail"]
        == "Blocked parking slot cannot be assigned"
    )


def test_release_parking(client):
    token = get_admin_token(client)
    property_id = create_test_property(client, token)
    tenant_id = create_test_tenant(client, token)

    parking = create_parking(
        client,
        token,
        property_id,
        f"P-{uuid.uuid4().hex[:8]}",
    )

    assign_response = client.post(
        f"/parking/{parking['id']}/assign",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_number": f"TS14-{uuid.uuid4().hex[:6].upper()}",
            "vehicle_type": "SUV",
            "tenant_id": tenant_id,
        },
    )

    assert assign_response.status_code == 200

    release_response = client.put(
        f"/parking/{parking['id']}/release",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert release_response.status_code == 200

    data = release_response.json()

    assert data["status"] == "Available"
    assert data["vehicle_number"] is None
    assert data["vehicle_type"] is None
    assert data["tenant_id"] is None


def test_release_available_parking_rejected(client):
    token = get_admin_token(client)
    property_id = create_test_property(client, token)

    parking = create_parking(
        client,
        token,
        property_id,
        f"P-{uuid.uuid4().hex[:8]}",
    )

    response = client.put(
        f"/parking/{parking['id']}/release",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Parking slot is not assigned"
    )


def test_invalid_property_rejected(client):
    token = get_admin_token(client)

    response = client.post(
        "/parking",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_id": 999999,
            "parking_number": f"P-{uuid.uuid4().hex[:8]}",
            "status": "Available",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Property not found"


def test_invalid_tenant_rejected(client):
    token = get_admin_token(client)
    property_id = create_test_property(client, token)

    parking = create_parking(
        client,
        token,
        property_id,
        f"P-{uuid.uuid4().hex[:8]}",
    )

    response = client.post(
        f"/parking/{parking['id']}/assign",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_number": f"TS15-{uuid.uuid4().hex[:6].upper()}",
            "vehicle_type": "Car",
            "tenant_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Tenant not found"