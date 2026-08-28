import uuid


def unique_id():
    return uuid.uuid4().hex[:8]


def get_admin_token(client):
    unique = unique_id()

    email = f"pytest.rentinvoice.admin.{unique}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Rent Invoice Test Admin {unique}",
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
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "full_name": f"Rent Invoice Test Tenant {unique}",
            "email": f"pytest.rentinvoice.tenant.{unique}@example.com",
            "phone": f"98765{unique[:5]}",
            "identification_number": f"PYTEST-RI-{unique}",
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
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "property_name": f"Rent Invoice Test Property {unique}",
            "property_type": "Apartment",
            "address": f"Test Road {unique}",
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
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "property_id": property_id,
            "building_name": f"Rent Invoice Test Tower {unique}",
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
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "building_id": building_id,
            "unit_number": f"RI-{unique}",
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


def create_test_lease(client, token):
    tenant_id = create_test_tenant(client, token)
    unit_id = create_test_unit(client, token)

    response = client.post(
        "/leases",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "start_date": "2026-09-01",
            "end_date": "2027-08-31",
            "monthly_rent": 25000,
            "security_deposit": 50000,
            "lease_status": "Draft",
        },
    )

    assert response.status_code == 200, (
        f"Lease creation failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    return response.json()["id"]


def create_test_invoice(client, token, billing_month="2026-09"):
    lease_id = create_test_lease(client, token)

    response = client.post(
        "/rent-invoices",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "lease_id": lease_id,
            "billing_month": billing_month,
            "rent_amount": 25000,
            "late_fee": 0,
            "discount": 0,
            "total_amount": 25000,
            "due_date": f"{billing_month}-10",
            "status": "Pending",
        },
    )

    assert response.status_code == 200, (
        f"Rent invoice creation failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    return response.json()


def test_create_rent_invoice(client):
    token = get_admin_token(client)

    invoice = create_test_invoice(
        client,
        token,
        "2026-09",
    )

    assert invoice["billing_month"] == "2026-09"
    assert invoice["rent_amount"] == 25000
    assert invoice["late_fee"] == 0
    assert invoice["discount"] == 0
    assert invoice["total_amount"] == 25000
    assert invoice["status"] == "Pending"
    assert invoice["lease_id"] > 0
    assert invoice["id"] > 0


def test_get_rent_invoices(client):
    token = get_admin_token(client)

    invoice = create_test_invoice(
        client,
        token,
        "2026-10",
    )

    response = client.get(
        "/rent-invoices",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    invoices = response.json()

    assert isinstance(invoices, list)
    assert any(
        item["id"] == invoice["id"]
        for item in invoices
    )


def test_get_rent_invoice_by_id(client):
    token = get_admin_token(client)

    invoice = create_test_invoice(
        client,
        token,
        "2026-11",
    )

    invoice_id = invoice["id"]

    response = client.get(
        f"/rent-invoices/{invoice_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == invoice_id
    assert data["lease_id"] == invoice["lease_id"]
    assert data["billing_month"] == "2026-11"


def test_create_rent_invoice_invalid_lease(client):
    token = get_admin_token(client)

    response = client.post(
        "/rent-invoices",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "lease_id": 999999,
            "billing_month": "2026-09",
            "rent_amount": 25000,
            "late_fee": 0,
            "discount": 0,
            "total_amount": 25000,
            "due_date": "2026-09-10",
            "status": "Pending",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Lease not found"


def test_create_rent_invoice_invalid_status(client):
    token = get_admin_token(client)

    lease_id = create_test_lease(
        client,
        token,
    )

    response = client.post(
        "/rent-invoices",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "lease_id": lease_id,
            "billing_month": "2026-12",
            "rent_amount": 25000,
            "late_fee": 0,
            "discount": 0,
            "total_amount": 25000,
            "due_date": "2026-12-10",
            "status": "InvalidStatus",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid invoice status"

def test_rent_invoice_total_calculated_by_server(client):
    token = get_admin_token(client)
    lease_id = create_test_lease(client, token)

    response = client.post(
        "/rent-invoices",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "lease_id": lease_id,
            "billing_month": "2026-12",
            "rent_amount": 25000,
            "late_fee": 1000,
            "discount": 500,
            "due_date": "2026-12-10",
            "status": "Pending",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["rent_amount"] == 25000
    assert data["late_fee"] == 1000
    assert data["discount"] == 500

    # 25,000 + 1,000 - 500 = 25,500
    assert data["total_amount"] == 25500