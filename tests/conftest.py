import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db


TEST_DATABASE_URL = (
    "postgresql://postgres:AgroPostgres2026@localhost:5432/"
    "smart_property_management_test"
)


test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client):
    email = "pytest.admin@example.com"
    password = "TestAdminPassword123!"

    # Check whether the test admin already exists.
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Pytest Admin",
            "email": email,
            "password": password,
            "role": "Super Admin",
        },
    )

    # The user may already exist because another test used it.
    assert register_response.status_code in (200, 400)

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    client.headers.update(
        {
            "Authorization": f"Bearer {token}",
        }
    )

    return client