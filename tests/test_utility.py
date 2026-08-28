import uuid


def get_admin_token(client):
    unique = uuid.uuid4().hex[:8]
    email = f"pytest.utility.admin.{unique}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Utility Admin {unique}",
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
            "property_name": f"Utility Property {unique}",
            "property_type": "Apartment",
            "address": "Utility Test Road",
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
            "building_name": f"Utility Tower {unique}",
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
            "unit_number": f"UTIL-{unique}",
            "floor_number": 1,
            "unit_type": "2BHK",
            "area": 1200,
            "monthly_rent": 25000,
            "status": "Available",
        },
    )

    assert unit_response.status_code == 200

    return unit_response.json()["id"]


def test_create_utility_reading(client):
    token = get_admin_token(client)
    unit_id = create_test_unit(client, token)

    response = client.post(
        "/utilities/readings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "utility_type": "Electricity",
            "previous_reading": 1000,
            "current_reading": 1250,
            "rate": 8,
            "billing_month": "2026-09",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["unit_id"] == unit_id
    assert data["utility_type"] == "Electricity"
    assert data["previous_reading"] == 1000
    assert data["current_reading"] == 1250

    # 1250 - 1000 = 250
    assert data["units_consumed"] == 250

    # 250 × 8 = 2000
    assert data["total_amount"] == 2000

    assert data["billing_month"] == "2026-09"


def test_get_utility_readings(client):
    token = get_admin_token(client)
    unit_id = create_test_unit(client, token)

    create_response = client.post(
        "/utilities/readings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "utility_type": "Water",
            "previous_reading": 500,
            "current_reading": 650,
            "rate": 5,
            "billing_month": "2026-09",
        },
    )

    assert create_response.status_code == 200

    response = client.get(
        "/utilities/readings",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    readings = response.json()

    assert isinstance(readings, list)
    assert any(
        item["unit_id"] == unit_id
        for item in readings
    )


def test_invalid_current_reading_rejected(client):
    token = get_admin_token(client)
    unit_id = create_test_unit(client, token)

    response = client.post(
        "/utilities/readings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "utility_type": "Electricity",
            "previous_reading": 1000,
            "current_reading": 900,
            "rate": 8,
            "billing_month": "2026-09",
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Current reading cannot be lower than previous reading"
    )


def test_invalid_utility_type_rejected(client):
    token = get_admin_token(client)
    unit_id = create_test_unit(client, token)

    response = client.post(
        "/utilities/readings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "utility_type": "Solar",
            "previous_reading": 100,
            "current_reading": 200,
            "rate": 5,
            "billing_month": "2026-09",
        },
    )

    assert response.status_code == 422


def test_create_utility_invoice(client):
    token = get_admin_token(client)
    unit_id = create_test_unit(client, token)

    response = client.post(
        "/utilities/invoices",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "utility_type": "Gas",
            "billing_month": "2026-09",
            "units_consumed": 100,
            "rate": 12,
            "status": "Pending",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["unit_id"] == unit_id
    assert data["utility_type"] == "Gas"
    assert data["units_consumed"] == 100
    assert data["rate"] == 12

    # 100 × 12 = 1200
    assert data["total_amount"] == 1200

    assert data["status"] == "Pending"


def test_get_utility_invoices(client):
    token = get_admin_token(client)
    unit_id = create_test_unit(client, token)

    create_response = client.post(
        "/utilities/invoices",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "utility_type": "Internet",
            "billing_month": "2026-09",
            "units_consumed": 50,
            "rate": 20,
            "status": "Pending",
        },
    )

    assert create_response.status_code == 200

    response = client.get(
        "/utilities/invoices",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    invoices = response.json()

    assert isinstance(invoices, list)
    assert any(
        item["unit_id"] == unit_id
        for item in invoices
    )


def test_invalid_utility_invoice_status(client):
    token = get_admin_token(client)
    unit_id = create_test_unit(client, token)

    response = client.post(
        "/utilities/invoices",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "unit_id": unit_id,
            "utility_type": "Water",
            "billing_month": "2026-09",
            "units_consumed": 100,
            "rate": 5,
            "status": "InvalidStatus",
        },
    )

    assert response.status_code == 422