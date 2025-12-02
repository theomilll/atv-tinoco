"""Auth endpoint tests."""


def test_login_missing_credentials(client):
    """Test login fails without credentials."""
    response = client.post('/api/auth/login/', json={})
    assert response.status_code == 400


def test_login_invalid_credentials(client):
    """Test login fails with invalid credentials."""
    response = client.post('/api/auth/login/', json={
        'username': 'invalid',
        'password': 'invalid'
    })
    assert response.status_code == 401


def test_login_success(auth_client):
    """Test login succeeds with valid credentials."""
    response = auth_client.get('/api/auth/me/')
    assert response.status_code == 200
    assert response.json['username'] == 'testuser'


def test_logout(auth_client):
    """Test logout works."""
    response = auth_client.post('/api/auth/logout/')
    assert response.status_code == 200
