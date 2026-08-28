import uuid


def get_admin_token(client):
    unique = uuid.uuid4().hex[:8]
    email = f"pytest.rent.api.admin.{unique}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Rent API Admin {unique}",
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


def create_test_lease(client, token):
    unique = uuid.uuid4().hex[:8]

    tenant_response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": f"Rent API Tenant {unique}",
            "email": f"pytest.rent.api.tenant.{unique}@example.com",
            "phone": "9876500003",
            "identification_number": f"PYTEST-RENT-API-{unique}",
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
            "property_name": f"Rent API Property {unique}",
            "property_type": "Apartment",
            "address": "Rent API Road",
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
            "building_name": f"Rent API Tower {unique}",
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
            "unit_number": f"RENT-{unique}",
            "floor_number": 1,
            "unit_type": "2BHK",
            "area": 1200,
            "monthly_rent": 25000,
            "status": "Available",
        },
    )

    assert unit_response.status_code == 200
    unit_id = unit_response.json()["id"]

    lease_response = client.post(
        "/leases",
        headers={"Authorization": f"Bearer {token}"},
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

    assert lease_response.status_code == 200

    return lease_response.json()["id"]


def create_test_invoice(client, token):
    lease_id = create_test_lease(client, token)

    response = client.post(
        "/rent/invoices/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "lease_id": lease_id,
            "billing_month": "2027-01",
            "rent_amount": 25000,
            "late_fee": 500,
            "discount": 500,
            "due_date": "2027-01-10",
            "status": "Pending",
        },
    )

    assert response.status_code == 200

    return response.json()


def test_generate_rent_invoice_api(client):
    token = get_admin_token(client)

    invoice = create_test_invoice(
        client,
        token,
    )

    assert invoice["lease_id"] > 0
    assert invoice["billing_month"] == "2027-01"

    # 25,000 + 500 - 500 = 25,000
    assert invoice["total_amount"] == 25000
    assert invoice["status"] == "Pending"


def test_get_rent_invoices_api(client):
    token = get_admin_token(client)

    invoice = create_test_invoice(
        client,
        token,
    )

    response = client.get(
        "/rent/invoices",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    invoices = response.json()

    assert isinstance(invoices, list)
    assert any(
        item["id"] == invoice["id"]
        for item in invoices
    )


def test_get_rent_invoice_by_id_api(client):
    token = get_admin_token(client)

    invoice = create_test_invoice(
        client,
        token,
    )

    invoice_id = invoice["id"]

    response = client.get(
        f"/rent/invoices/{invoice_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == invoice_id


def test_pay_rent_invoice_api(client):
    token = get_admin_token(client)

    invoice = create_test_invoice(
        client,
        token,
    )

    invoice_id = invoice["id"]

    response = client.post(
        f"/rent/pay/{invoice_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "invoice_id": invoice_id,
            "amount": 25000,
            "payment_method": "UPI",
            "payment_status": "Success",
            "transaction_reference": (
                f"PYTEST-RENT-API-{uuid.uuid4().hex[:8]}"
            ),
        },
    )

    assert response.status_code == 200

    payment = response.json()

    assert payment["invoice_id"] == invoice_id
    assert payment["amount"] == 25000
    assert payment["payment_status"] == "Success"


def test_get_rent_payments_api(client):
    token = get_admin_token(client)

    invoice = create_test_invoice(
        client,
        token,
    )

    invoice_id = invoice["id"]

    payment_response = client.post(
        f"/rent/pay/{invoice_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "invoice_id": invoice_id,
            "amount": 25000,
            "payment_method": "Bank Transfer",
            "payment_status": "Success",
            "transaction_reference": (
                f"PYTEST-RENT-PAY-{uuid.uuid4().hex[:8]}"
            ),
        },
    )

    assert payment_response.status_code == 200

    response = client.get(
        "/rent/payments",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    payments = response.json()

    assert isinstance(payments, list)
    assert any(
        payment["invoice_id"] == invoice_id
        for payment in payments
    )