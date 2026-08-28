def get_admin_token(client):
    client.post(
        "/auth/register",
        json={
            "name": "Building Test Admin",
            "email": "pytest.building.admin@example.com",
            "password": "AdminPassword123!",
            "role": "Super Admin",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "pytest.building.admin@example.com",
            "password": "AdminPassword123!",
        },
    )

    return response.json()["access_token"]


def create_property(client, token):
    response = client.post(
        "/properties",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_name": "Pytest Building Property",
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


def test_create_building(client):
    token = get_admin_token(client)
    property_id = create_property(client, token)

    response = client.post(
        "/buildings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_id": property_id,
            "building_name": "Tower A",
            "number_of_floors": 10,
            "total_units": 100,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["building_name"] == "Tower A"
    assert data["property_id"] == property_id


def test_create_unit(client):
    token = get_admin_token(client)
    property_id = create_property(client, token)

    building_response = client.post(
        "/buildings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_id": property_id,
            "building_name": "Tower B",
            "number_of_floors": 10,
            "total_units": 100,
        },
    )

    building_id = building_response.json()["id"]

    response = client.post(
        "/units",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "building_id": building_id,
            "unit_number": "101",
            "floor_number": 1,
            "unit_type": "2BHK",
            "area": 1200,
            "monthly_rent": 25000,
            "status": "Available",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["unit_number"] == "101"
    assert data["building_id"] == building_id
    assert data["status"] == "Available"


def test_duplicate_unit_number_rejected(client):
    token = get_admin_token(client)
    property_id = create_property(client, token)

    building_response = client.post(
        "/buildings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "property_id": property_id,
            "building_name": "Tower C",
            "number_of_floors": 5,
            "total_units": 50,
        },
    )

    building_id = building_response.json()["id"]

    unit_data = {
        "building_id": building_id,
        "unit_number": "101",
        "floor_number": 1,
        "unit_type": "2BHK",
        "area": 1200,
        "monthly_rent": 25000,
        "status": "Available",
    }

    first_response = client.post(
        "/units",
        headers={"Authorization": f"Bearer {token}"},
        json=unit_data,
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/units",
        headers={"Authorization": f"Bearer {token}"},
        json=unit_data,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Unit number already exists in this building"
    )