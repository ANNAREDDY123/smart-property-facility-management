def get_admin_token(client):
    client.post(
        "/auth/register",
        json={
            "name": "Lease Test Admin",
            "email": "pytest.lease.admin@example.com",
            "password": "AdminPassword123!",
            "role": "Super Admin",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "pytest.lease.admin@example.com",
            "password": "AdminPassword123!",
        },
    )

    return response.json()["access_token"]


def create_tenant(client, token, suffix):
    response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": f"Lease Tenant {suffix}",
            "email": f"pytest.lease.tenant.{suffix}@example.com",
            "phone": "9876543210",
            "identification_number": f"LEASE-TEN-{suffix}",
            "emergency_contact": "Test Contact",
            "address": "Hyderabad",
        },
    )

    assert response.status_code == 200
    return response.json()["id"]


def create_property(client, token, suffix):
    response = client.post(
        "/properties",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_name": f"Lease Property {suffix}",
            "property_type": "Apartment",
            "address": "Test Road",
            "city": "Hyderabad",
            "state": "Telangana",
            "total_area": 50000,
            "total_units": 100,
            "status": "Active",
        },
    )

    assert response.status_code == 200
    return response.json()["id"]


def create_unit(client, token, suffix, status="Available"):
    property_id = create_property(client, token, suffix)

    building_response = client.post(
        "/buildings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_id": property_id,
            "building_name": f"Lease Tower {suffix}",
            "number_of_floors": 10,
            "total_units": 100,
        },
    )

    assert building_response.status_code == 200
    building_id = building_response.json()["id"]

    response = client.post(
        "/units",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "building_id": building_id,
            "unit_number": f"10{suffix}",
            "floor_number": 1,
            "unit_type": "2BHK",
            "area": 1200,
            "monthly_rent": 25000,
            "status": status,
        },
    )

    assert response.status_code == 200
    return response.json()["id"]


def test_create_active_lease_occupies_unit(client):
    token = get_admin_token(client)

    tenant_id = create_tenant(client, token, "001")
    unit_id = create_unit(client, token, "001")

    response = client.post(
        "/leases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "start_date": "2026-09-01",
            "end_date": "2027-08-31",
            "monthly_rent": 25000,
            "security_deposit": 50000,
            "lease_status": "Active",
        },
    )

    assert response.status_code == 200

    lease = response.json()

    assert lease["tenant_id"] == tenant_id
    assert lease["unit_id"] == unit_id
    assert lease["lease_status"] == "Active"

    unit_response = client.get(
        f"/units/{unit_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert unit_response.status_code == 200
    assert unit_response.json()["status"] == "Occupied"


def test_maintenance_unit_cannot_be_leased(client):
    token = get_admin_token(client)

    tenant_id = create_tenant(client, token, "002")
    unit_id = create_unit(
        client,
        token,
        "002",
        status="Maintenance",
    )

    response = client.post(
        "/leases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "start_date": "2026-09-01",
            "end_date": "2027-08-31",
            "monthly_rent": 25000,
            "security_deposit": 50000,
            "lease_status": "Active",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Maintenance units cannot be leased"
    )


def test_overlapping_active_lease_rejected(client):
    token = get_admin_token(client)

    tenant_one = create_tenant(client, token, "003")
    tenant_two = create_tenant(client, token, "004")
    unit_id = create_unit(client, token, "003")

    first_response = client.post(
        "/leases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tenant_id": tenant_one,
            "unit_id": unit_id,
            "start_date": "2026-09-01",
            "end_date": "2027-08-31",
            "monthly_rent": 25000,
            "security_deposit": 50000,
            "lease_status": "Active",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/leases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tenant_id": tenant_two,
            "unit_id": unit_id,
            "start_date": "2027-01-01",
            "end_date": "2027-12-31",
            "monthly_rent": 26000,
            "security_deposit": 52000,
            "lease_status": "Active",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Unit already has an overlapping active lease"
    )


def test_invalid_lease_dates_rejected(client):
    token = get_admin_token(client)

    tenant_id = create_tenant(client, token, "005")
    unit_id = create_unit(client, token, "005")

    response = client.post(
        "/leases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "start_date": "2027-09-01",
            "end_date": "2027-08-31",
            "monthly_rent": 25000,
            "security_deposit": 50000,
            "lease_status": "Draft",
        },
    )

    assert response.status_code == 422


def test_terminate_lease_makes_unit_available(client):
    token = get_admin_token(client)

    tenant_id = create_tenant(client, token, "006")
    unit_id = create_unit(client, token, "006")

    create_response = client.post(
        "/leases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "start_date": "2026-09-01",
            "end_date": "2027-08-31",
            "monthly_rent": 25000,
            "security_deposit": 50000,
            "lease_status": "Active",
        },
    )

    assert create_response.status_code == 200

    lease_id = create_response.json()["id"]

    response = client.put(
        f"/leases/{lease_id}/terminate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["lease_status"] == "Terminated"

    unit_response = client.get(
        f"/units/{unit_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert unit_response.status_code == 200
    assert unit_response.json()["status"] == "Available"