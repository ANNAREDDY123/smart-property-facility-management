import uuid


def unique_id():
    return uuid.uuid4().hex[:8]


def get_admin_token(client):
    unique = unique_id()

    email = f"pytest.payment.admin.{unique}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Payment Test Admin {unique}",
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


def create_test_invoice(client, token):
    unique = unique_id()

    tenant_response = client.post(
        "/tenants",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "full_name": f"Payment Test Tenant {unique}",
            "email": f"pytest.payment.tenant.{unique}@example.com",
            "phone": f"98765{unique[:5]}",
            "identification_number": f"PYTEST-PAY-{unique}",
            "emergency_contact": "Test Contact",
            "address": "Hyderabad",
        },
    )

    assert tenant_response.status_code == 200, (
        f"Tenant creation failed: "
        f"{tenant_response.status_code} "
        f"{tenant_response.text}"
    )

    tenant_id = tenant_response.json()["id"]

    property_response = client.post(
        "/properties",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "property_name": f"Payment Test Property {unique}",
            "property_type": "Apartment",
            "address": f"Payment Test Road {unique}",
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
            "building_name": f"Payment Test Tower {unique}",
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
            "unit_number": f"PAY-{unique}",
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

    unit_id = unit_response.json()["id"]

    lease_response = client.post(
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

    assert lease_response.status_code == 200, (
        f"Lease creation failed: "
        f"{lease_response.status_code} "
        f"{lease_response.text}"
    )

    lease_id = lease_response.json()["id"]

    invoice_response = client.post(
        "/rent-invoices",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "lease_id": lease_id,
            "billing_month": "2026-09",
            "rent_amount": 25000,
            "late_fee": 0,
            "discount": 0,
            "total_amount": 25000,
            "due_date": "2026-09-10",
            "status": "Pending",
        },
    )

    assert invoice_response.status_code == 200, (
        f"Rent invoice creation failed: "
        f"{invoice_response.status_code} "
        f"{invoice_response.text}"
    )

    return invoice_response.json()["id"]


def create_payment(
    client,
    token,
    invoice_id,
    transaction_reference,
    amount=25000,
    payment_method="UPI",
    payment_status="Success",
):
    response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "invoice_id": invoice_id,
            "amount": amount,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "transaction_reference": transaction_reference,
        },
    )

    return response


def test_create_payment(client):
    token = get_admin_token(client)

    invoice_id = create_test_invoice(
        client,
        token,
    )

    transaction_reference = (
        f"PYTEST-PAY-{unique_id()}"
    )

    response = create_payment(
        client,
        token,
        invoice_id,
        transaction_reference,
    )

    assert response.status_code == 200, (
        f"Payment creation failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    data = response.json()

    assert data["invoice_id"] == invoice_id
    assert data["amount"] == 25000
    assert data["payment_method"] == "UPI"
    assert data["payment_status"] == "Success"
    assert data["transaction_reference"] == transaction_reference
    assert data["id"] > 0


def test_get_payments(client):
    token = get_admin_token(client)

    invoice_id = create_test_invoice(
        client,
        token,
    )

    transaction_reference = (
        f"PYTEST-PAY-{unique_id()}"
    )

    create_response = create_payment(
        client,
        token,
        invoice_id,
        transaction_reference,
        payment_method="Cash",
    )

    assert create_response.status_code == 200, (
        f"Payment creation failed: "
        f"{create_response.status_code} "
        f"{create_response.text}"
    )

    payment_id = create_response.json()["id"]

    response = client.get(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    payments = response.json()

    assert isinstance(payments, list)
    assert any(
        payment["id"] == payment_id
        for payment in payments
    )


def test_get_payment_by_id(client):
    token = get_admin_token(client)

    invoice_id = create_test_invoice(
        client,
        token,
    )

    transaction_reference = (
        f"PYTEST-PAY-{unique_id()}"
    )

    create_response = create_payment(
        client,
        token,
        invoice_id,
        transaction_reference,
        payment_method="Bank Transfer",
    )

    assert create_response.status_code == 200

    payment_id = create_response.json()["id"]

    response = client.get(
        f"/payments/{payment_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["invoice_id"] == invoice_id
    assert data["transaction_reference"] == transaction_reference


def test_create_payment_invalid_invoice(client):
    token = get_admin_token(client)

    transaction_reference = (
        f"PYTEST-PAY-{unique_id()}"
    )

    response = create_payment(
        client,
        token,
        999999,
        transaction_reference,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Rent invoice not found"


def test_create_payment_invalid_status(client):
    token = get_admin_token(client)

    invoice_id = create_test_invoice(
        client,
        token,
    )

    transaction_reference = (
        f"PYTEST-PAY-{unique_id()}"
    )

    response = create_payment(
        client,
        token,
        invoice_id,
        transaction_reference,
        payment_status="InvalidStatus",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid payment status"


def test_duplicate_transaction_reference(client):
    token = get_admin_token(client)

    invoice_id = create_test_invoice(
        client,
        token,
    )

    transaction_reference = (
        f"PYTEST-PAY-DUP-{unique_id()}"
    )

    first_response = create_payment(
        client,
        token,
        invoice_id,
        transaction_reference,
    )

    assert first_response.status_code == 200, (
        f"First payment failed: "
        f"{first_response.status_code} "
        f"{first_response.text}"
    )

    second_response = create_payment(
        client,
        token,
        invoice_id,
        transaction_reference,
    )

    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "Transaction reference already exists"
    )

def test_payment_cannot_exceed_invoice_balance(client):
    token = get_admin_token(client)
    invoice_id = create_test_invoice(client, token)

    response = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "invoice_id": invoice_id,
            "amount": 30000,
            "payment_method": "UPI",
            "payment_status": "Success",
            "transaction_reference": "PYTEST-PAY-EXCEED-001",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Payment exceeds invoice balance"
    )


def test_successful_full_payment_marks_invoice_paid(client):
    token = get_admin_token(client)
    invoice_id = create_test_invoice(client, token)

    payment_response = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "invoice_id": invoice_id,
            "amount": 25000,
            "payment_method": "UPI",
            "payment_status": "Success",
            "transaction_reference": "PYTEST-PAY-FULL-001",
        },
    )

    assert payment_response.status_code == 200

    invoice_response = client.get(
        f"/rent-invoices/{invoice_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert invoice_response.status_code == 200
    assert invoice_response.json()["status"] == "Paid"