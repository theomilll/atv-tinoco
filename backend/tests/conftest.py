"""Pytest fixtures."""
import pytest

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def app():
    """Create test application."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Create authenticated test client."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@test.com',
            is_active=True
        )
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

    client.post('/api/auth/login/', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    return client
