"""Health endpoint tests."""
import pytest

from app import create_app


@pytest.fixture
def app():
    """Create test app."""
    app = create_app("testing")
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_health_endpoint(client):
    """Test health check returns 200."""
    response = client.get("/api/health/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
