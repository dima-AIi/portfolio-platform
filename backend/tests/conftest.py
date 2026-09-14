import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-pytest-only-32b!"
os.environ["ENV"] = "development"
os.environ["UPLOAD_DIR"] = os.path.join(os.path.dirname(__file__), "test_uploads")

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.utils.seed import seed_technologies


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_technologies(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_technologies(db)
    db.close()
    from app.utils.rate_limit import reset_rate_limits

    reset_rate_limits()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "owner@example.com", "username": "owner", "password": "strongpass123"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "username": "other", "password": "strongpass123"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(client, headers, title="Telegram CRM", **kwargs):
    payload = {"title": title, "short_description": "CRM system.", **kwargs}
    response = client.post("/api/v1/projects", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()
