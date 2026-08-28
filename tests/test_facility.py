import uuid

import pytest
from sqlalchemy import delete

from app.models.facility import Facility
from app.models.facility_booking import FacilityBooking


FACILITY_NAMES = [
    "Gym",
    "Swimming Pool",
    "Conference Room",
    "Club House",
    "Sports Area",
]


@pytest.fixture(autouse=True)
def clean_facility_data():
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()

    try:
        db.execute(delete(FacilityBooking))
        db.execute(delete(Facility))
        db.commit()
    finally:
        db.close()

    yield


def get_admin_token(client):
    unique = uuid.uuid4().hex[:8]
    email = f"facility.admin.{unique}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "name": f"Facility Admin {unique}",
            "email": email,
            "password": "AdminPassword123!",
            "role": "Super Admin",
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "AdminPassword123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_tenant(client, token):
    unique = uuid.uuid4().hex[:8]

    response = client.post(
        "/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": f"Facility Tenant {unique}",
            "email": f"facility.tenant.{unique}@example.com",
            "phone": "9876543210",
            "identification_number": f"FAC-{unique}",
            "emergency_contact": "9876500000",
            "address": "Facility Test Address",
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


def get_facilities(client, token):
    response = client.get(
        "/facilities",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    return response.json()


def create_facility(
    client,
    token,
    capacity=2,
    status="Active",
):
    facilities = get_facilities(client, token)

    for facility in facilities:
        if facility["status"] == status:
            return facility

    existing_names = {
        facility["name"]
        for facility in facilities
    }

    available_name = next(
        (
            name
            for name in FACILITY_NAMES
            if name not in existing_names
        ),
        None,
    )

    if available_name is None:
        raise AssertionError(
            "No unused facility type is available"
        )

    response = client.post(
        "/facilities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": available_name,
            "capacity": capacity,
            "status": status,
        },
    )

    assert response.status_code == 200

    return response.json()


def create_specific_facility(
    client,
    token,
    capacity=2,
    status="Active",
):
    facilities = get_facilities(client, token)

    existing_names = {
        facility["name"]
        for facility in facilities
    }

    available_name = next(
        (
            name
            for name in FACILITY_NAMES
            if name not in existing_names
        ),
        None,
    )

    if available_name is None:
        raise AssertionError(
            "All facility types already exist"
        )

    response = client.post(
        "/facilities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": available_name,
            "capacity": capacity,
            "status": status,
        },
    )

    assert response.status_code == 200

    return response.json()


def book(
    client,
    token,
    facility_id,
    tenant_id,
    booking_date,
    start_time="10:00:00",
    end_time="11:00:00",
    status="Confirmed",
):
    return client.post(
        f"/facilities/{facility_id}/book",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tenant_id": tenant_id,
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time,
            "status": status,
        },
    )


def test_create_facility(client):
    token = get_admin_token(client)

    facility = create_specific_facility(
        client,
        token,
        capacity=5,
    )

    assert facility["name"] in FACILITY_NAMES
    assert facility["capacity"] == 5
    assert facility["status"] == "Active"


def test_duplicate_facility_rejected(client):
    token = get_admin_token(client)

    facility = create_specific_facility(
        client,
        token,
        capacity=5,
    )

    response = client.post(
        "/facilities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": facility["name"],
            "capacity": 5,
            "status": "Active",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Facility already exists"


def test_get_facilities(client):
    token = get_admin_token(client)

    response = client.get(
        "/facilities",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_book_facility(client):
    token = get_admin_token(client)
    tenant_id = create_tenant(client, token)

    facility = create_facility(
        client,
        token,
        capacity=2,
    )

    response = book(
        client,
        token,
        facility["id"],
        tenant_id,
        "2030-09-01",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["facility_id"] == facility["id"]
    assert data["tenant_id"] == tenant_id
    assert data["status"] == "Confirmed"


def test_get_facility_bookings(client):
    token = get_admin_token(client)

    response = client.get(
        "/facilities/bookings",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_overlapping_booking_allowed_until_capacity(client):
    token = get_admin_token(client)

    tenant1 = create_tenant(client, token)
    tenant2 = create_tenant(client, token)

    facility = create_specific_facility(
        client,
        token,
        capacity=2,
    )

    response1 = book(
        client,
        token,
        facility["id"],
        tenant1,
        "2030-09-02",
        "10:00:00",
        "11:00:00",
    )

    assert response1.status_code == 200

    response2 = book(
        client,
        token,
        facility["id"],
        tenant2,
        "2030-09-02",
        "10:30:00",
        "11:30:00",
    )

    assert response2.status_code == 200


def test_facility_capacity_exceeded(client):
    token = get_admin_token(client)

    tenant1 = create_tenant(client, token)
    tenant2 = create_tenant(client, token)
    tenant3 = create_tenant(client, token)

    facility = create_specific_facility(
        client,
        token,
        capacity=2,
    )

    response1 = book(
        client,
        token,
        facility["id"],
        tenant1,
        "2030-09-03",
        "10:00:00",
        "11:00:00",
    )

    assert response1.status_code == 200

    response2 = book(
        client,
        token,
        facility["id"],
        tenant2,
        "2030-09-03",
        "10:30:00",
        "11:30:00",
    )

    assert response2.status_code == 200

    response3 = book(
        client,
        token,
        facility["id"],
        tenant3,
        "2030-09-03",
        "10:15:00",
        "11:15:00",
    )

    assert response3.status_code == 409

    assert (
        response3.json()["detail"]
        == "Facility capacity exceeded for this time slot"
    )


def test_cancelled_booking_does_not_consume_capacity(client):
    token = get_admin_token(client)

    tenant1 = create_tenant(client, token)
    tenant2 = create_tenant(client, token)

    facility = create_specific_facility(
        client,
        token,
        capacity=1,
    )

    cancelled = book(
        client,
        token,
        facility["id"],
        tenant1,
        "2030-09-04",
        "10:00:00",
        "11:00:00",
        "Cancelled",
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "Cancelled"

    confirmed = book(
        client,
        token,
        facility["id"],
        tenant2,
        "2030-09-04",
        "10:30:00",
        "11:30:00",
        "Confirmed",
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "Confirmed"


def test_invalid_tenant_rejected(client):
    token = get_admin_token(client)

    facility = create_facility(
        client,
        token,
        capacity=2,
    )

    response = book(
        client,
        token,
        facility["id"],
        999999,
        "2030-09-05",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Tenant not found"


def test_invalid_time_range_rejected(client):
    token = get_admin_token(client)
    tenant_id = create_tenant(client, token)

    facility = create_facility(
        client,
        token,
        capacity=2,
    )

    response = book(
        client,
        token,
        facility["id"],
        tenant_id,
        "2030-09-06",
        "12:00:00",
        "11:00:00",
    )

    assert response.status_code == 422


def test_inactive_facility_rejected(client):
    token = get_admin_token(client)
    tenant_id = create_tenant(client, token)

    facility = create_specific_facility(
        client,
        token,
        capacity=5,
        status="Inactive",
    )

    response = book(
        client,
        token,
        facility["id"],
        tenant_id,
        "2030-09-07",
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Facility is not active"
    )