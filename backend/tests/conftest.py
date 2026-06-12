import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.api.routes import auth


@pytest.fixture()
def client():
    auth.settings.researcher_access_code = "test-researcher-code"
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def register(client, email="learner@example.com", consent=True, researcher_access_code=""):
    response = client.post("/auth/register", json={
        "name": "Test Learner",
        "email": email,
        "password": "SecurePass123!",
        "proficiency": "beginner",
        "learning_goal": "Everyday conversation",
        "research_consent": consent,
        "researcher_access_code": researcher_access_code,
    })
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def learner(client):
    data = register(client)
    return data, {"Authorization": f"Bearer {data['access_token']}"}
