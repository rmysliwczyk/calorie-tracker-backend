import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, StaticPool, create_engine

from .dependencies import get_password_hash, get_session
from .main import app
from .models import User

load_dotenv()
admin_username = os.getenv("DEFAULT_ADMIN_LOGIN")
admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
access_token = ""

client = TestClient(app)

# session and client fixture for a test only database


@pytest.fixture(name="session", scope="module")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client", scope="module")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Creating an admin accout


def test_creating_admin_account_in_db(session: Session):
    new_user = User.model_validate(
        {
            "username": admin_username,
            "hashed_password": get_password_hash(admin_password),
            "is_admin": True,
        }
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    user_from_db = session.get(User, 1)


# Integration tests


def test_auth_token_returns_405_not_allowed_for_get(client: TestClient):
    # This endpoint doesn't allow GET, we expect 405 Method Not Allowed
    response = client.get("/auth/token")
    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}


def test_auth_token_returns_200_and_valid_token_for_post(client: TestClient):
    global access_token
    response = client.post(
        "/auth/token", data={"username": admin_username, "password": admin_password}
    )
    assert response.status_code == 200
    response_body = response.json()
    assert "access_token" in response_body
    access_token = response_body["access_token"]
    assert response_body["token_type"] == "bearer"


def test_auth_me_returns_200_and_current_user_data(client: TestClient):
    print(access_token)
    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["username"] == admin_username
