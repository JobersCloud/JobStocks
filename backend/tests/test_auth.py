"""Tests de autenticación: login, logout, current-user, CSRF."""
from unittest.mock import patch, MagicMock


class TestLogin:
    def test_login_missing_credentials(self, client):
        """Login sin credenciales devuelve 400."""
        response = client.post('/api/login', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_login_missing_password(self, client):
        """Login sin password devuelve 400."""
        response = client.post('/api/login', json={
            'username': 'admin',
            'connection': '1'
        })
        assert response.status_code == 400

    def test_login_missing_connection(self, client):
        """Login sin connection devuelve 400."""
        response = client.post('/api/login', json={
            'username': 'admin',
            'password': 'test'
        })
        assert response.status_code == 400


class TestCurrentUser:
    def test_current_user_unauthenticated(self, client):
        """current-user sin sesión devuelve 401."""
        response = client.get('/api/current-user')
        assert response.status_code == 401


class TestCsrf:
    def test_csrf_token_unauthenticated(self, client):
        """CSRF token sin sesión devuelve 401."""
        response = client.get('/api/csrf-token')
        assert response.status_code == 401
