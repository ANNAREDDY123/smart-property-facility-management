import uuid
from datetime import datetime, timezone


def get_admin_token(client):
    unique = uuid.uuid4().hex[:8]
    email = f"pytest.visitor.admin.{unique}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Visitor Admin {unique}",
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


def create_test_tenant(client, token):
    unique = uuid.uuid4().hex[:8]

    response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": f"Visitor Test Tenant {unique}",
            "email": f"visitor.tenant.{unique}@example.com",
            "phone": "9876543210",
            "identification_number": f"VIS-{unique}",
            "emergency_contact": "9876500000",
            "address": "Visitor Test Address",
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


def create_test_unit(client, token):
    unique = uuid.uuid4().hex[:8]

    property_response = client.post(
        "/properties",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_name": f"Visitor Property {unique}",
            "property_type": "Apartment",
            "address": "Visitor Test Road",
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
            "building_name": f"Visitor Tower {unique}",
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
            "unit_number": f"VIS-{unique}",
            "floor_number": 1,
            "unit_type": "2BHK",
            "area": 1200,
            "monthly_rent": 25000,
            "status": "Available",
        },
    )

    assert unit_response.status_code == 200

    return unit_response.json()["id"]


def create_test_visitor(client, token):
    tenant_id = create_test_tenant(client, token)
    unit_id = create_test_unit(client, token)

    response = client.post(
        "/visitors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "visitor_name": "Ravi Kumar",
            "phone": "9988776655",
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "purpose": "Meeting tenant",
            "visitor_status": "Expected",
        },
    )

    assert response.status_code == 200

    return response.json()


def test_create_visitor(client):
    token = get_admin_token(client)

    visitor = create_test_visitor(
        client,
        token,
    )

    assert visitor["visitor_name"] == "Ravi Kumar"
    assert visitor["phone"] == "9988776655"
    assert visitor["purpose"] == "Meeting tenant"
    assert visitor["visitor_status"] == "Expected"
    assert visitor["exit_time"] is None


def test_create_checked_in_visitor(client):
    token = get_admin_token(client)

    tenant_id = create_test_tenant(client, token)
    unit_id = create_test_unit(client, token)

    entry_time = datetime.now(timezone.utc).isoformat()

    response = client.post(
        "/visitors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "visitor_name": "Suresh Kumar",
            "phone": "9988771122",
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "purpose": "Delivery",
            "entry_time": entry_time,
            "visitor_status": "Checked In",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["visitor_status"] == "Checked In"
    assert data["entry_time"] is not None


def test_get_visitors(client):
    token = get_admin_token(client)

    visitor = create_test_visitor(
        client,
        token,
    )

    response = client.get(
        "/visitors",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    visitors = response.json()

    assert isinstance(visitors, list)
    assert any(
        item["id"] == visitor["id"]
        for item in visitors
    )


def test_filter_visitors_by_status(client):
    token = get_admin_token(client)

    visitor = create_test_visitor(
        client,
        token,
    )

    response = client.get(
        "/visitors",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "visitor_status": "Expected",
        },
    )

    assert response.status_code == 200

    visitors = response.json()

    assert any(
        item["id"] == visitor["id"]
        and item["visitor_status"] == "Expected"
        for item in visitors
    )


def test_checkout_visitor(client):
    token = get_admin_token(client)

    visitor = create_test_visitor(
        client,
        token,
    )

    response = client.put(
        f"/visitors/{visitor['id']}/checkout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["visitor_status"] == "Checked Out"
    assert data["exit_time"] is not None


def test_checkout_already_checked_out_visitor(client):
    token = get_admin_token(client)

    visitor = create_test_visitor(
        client,
        token,
    )

    first_response = client.put(
        f"/visitors/{visitor['id']}/checkout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first_response.status_code == 200

    second_response = client.put(
        f"/visitors/{visitor['id']}/checkout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert second_response.status_code == 400

    assert (
        second_response.json()["detail"]
        == "Visitor is already checked out"
    )


def test_invalid_visitor_status(client):
    token = get_admin_token(client)

    tenant_id = create_test_tenant(client, token)
    unit_id = create_test_unit(client, token)

    response = client.post(
        "/visitors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "visitor_name": "Invalid Status Visitor",
            "phone": "9999999999",
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "purpose": "Testing",
            "visitor_status": "InvalidStatus",
        },
    )

    assert response.status_code == 422