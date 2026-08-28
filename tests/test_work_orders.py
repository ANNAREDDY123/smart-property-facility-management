import uuid


def unique_id():
    return uuid.uuid4().hex[:8]


def get_admin_token(client):
    unique = unique_id()
    email = f"pytest.workorder.admin.{unique}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Work Order Test Admin {unique}",
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


def create_test_maintenance_request(client, token):
    unique = unique_id()

    tenant_response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": f"Work Order Tenant {unique}",
            "email": f"pytest.workorder.tenant.{unique}@example.com",
            "phone": f"98765{unique[:5]}",
            "identification_number": f"PYTEST-WO-TEN-{unique}",
            "emergency_contact": "Test Contact",
            "address": "Hyderabad",
        },
    )

    assert tenant_response.status_code == 200
    tenant_id = tenant_response.json()["id"]

    property_response = client.post(
        "/properties",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_name": f"Work Order Property {unique}",
            "property_type": "Apartment",
            "address": f"Work Order Road {unique}",
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
            "building_name": f"Work Order Tower {unique}",
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
            "unit_number": f"WO-{unique}",
            "floor_number": 1,
            "unit_type": "2BHK",
            "area": 1200,
            "monthly_rent": 25000,
            "status": "Available",
        },
    )

    assert unit_response.status_code == 200
    unit_id = unit_response.json()["id"]

    maintenance_response = client.post(
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

    assert maintenance_response.status_code == 200

    return maintenance_response.json()["id"]


def create_test_work_order(client, token):
    maintenance_request_id = create_test_maintenance_request(
        client,
        token,
    )

    response = client.post(
        "/work-orders",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "maintenance_request_id": maintenance_request_id,
            "assigned_to": None,
            "title": "Repair bathroom leakage",
            "description": "Replace damaged bathroom pipe.",
            "priority": "High",
            "status": "Pending",
            "scheduled_date": "2026-09-05T10:00:00",
        },
    )

    assert response.status_code == 200, (
        f"Work order creation failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    return response.json()


def test_create_work_order(client):
    token = get_admin_token(client)

    work_order = create_test_work_order(
        client,
        token,
    )

    assert work_order["id"] > 0
    assert work_order["maintenance_request_id"] > 0
    assert work_order["assigned_to"] is None
    assert work_order["title"] == "Repair bathroom leakage"
    assert work_order["priority"] == "High"
    assert work_order["status"] == "Pending"


def test_get_work_orders(client):
    token = get_admin_token(client)

    work_order = create_test_work_order(
        client,
        token,
    )

    response = client.get(
        "/work-orders",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    work_orders = response.json()

    assert isinstance(work_orders, list)
    assert any(
        item["id"] == work_order["id"]
        for item in work_orders
    )


def test_get_work_order_by_id(client):
    token = get_admin_token(client)

    work_order = create_test_work_order(
        client,
        token,
    )

    work_order_id = work_order["id"]

    response = client.get(
        f"/work-orders/{work_order_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == work_order_id
    assert data["title"] == "Repair bathroom leakage"


def test_update_work_order(client):
    token = get_admin_token(client)

    work_order = create_test_work_order(
        client,
        token,
    )

    work_order_id = work_order["id"]

    response = client.put(
        f"/work-orders/{work_order_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated bathroom repair",
            "description": "Pipe replacement is required.",
            "priority": "Critical",
            "status": "In Progress",
        },
    )

    assert response.status_code == 200, (
        f"Work order update failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    data = response.json()

    assert data["id"] == work_order_id
    assert data["title"] == "Updated bathroom repair"
    assert data["priority"] == "Critical"
    assert data["status"] == "In Progress"


def test_complete_work_order_sets_completed_at(client):
    token = get_admin_token(client)

    work_order = create_test_work_order(
        client,
        token,
    )

    work_order_id = work_order["id"]

    response = client.put(
        f"/work-orders/{work_order_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "status": "Completed",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Completed"
    assert data["completed_at"] is not None


def test_create_work_order_invalid_maintenance_request(client):
    token = get_admin_token(client)

    response = client.post(
        "/work-orders",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "maintenance_request_id": 999999,
            "assigned_to": None,
            "title": "Invalid request test",
            "description": "Testing invalid maintenance request.",
            "priority": "Medium",
            "status": "Pending",
        },
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Maintenance request not found"
    )


def test_create_work_order_invalid_priority(client):
    token = get_admin_token(client)

    maintenance_request_id = create_test_maintenance_request(
        client,
        token,
    )

    response = client.post(
        "/work-orders",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "maintenance_request_id": maintenance_request_id,
            "assigned_to": None,
            "title": "Invalid priority test",
            "description": "Testing invalid priority.",
            "priority": "Urgent",
            "status": "Pending",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid work order priority"
    )


def test_create_work_order_invalid_status(client):
    token = get_admin_token(client)

    maintenance_request_id = create_test_maintenance_request(
        client,
        token,
    )

    response = client.post(
        "/work-orders",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "maintenance_request_id": maintenance_request_id,
            "assigned_to": None,
            "title": "Invalid status test",
            "description": "Testing invalid status.",
            "priority": "Medium",
            "status": "InvalidStatus",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid work order status"
    )


def test_delete_work_order(client):
    token = get_admin_token(client)

    work_order = create_test_work_order(
        client,
        token,
    )

    work_order_id = work_order["id"]

    response = client.delete(
        f"/work-orders/{work_order_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "Work order deleted successfully"
    )

    get_response = client.get(
        f"/work-orders/{work_order_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 404
    assert (
        get_response.json()["detail"]
        == "Work order not found"
    )