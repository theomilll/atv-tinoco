"""Health endpoint tests."""


def test_health_endpoint(client):
    """Test health check returns ok."""
    response = client.get('/api/health/')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'
