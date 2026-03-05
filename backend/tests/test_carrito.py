"""Tests de carrito: add, view, remove, clear."""
from unittest.mock import patch, MagicMock


class TestCarritoAuth:
    def test_carrito_requires_auth(self, client):
        """GET /api/carrito sin sesión devuelve 401."""
        response = client.get('/api/carrito')
        assert response.status_code == 401

    def test_carrito_add_requires_auth(self, client):
        """POST /api/carrito/add sin sesión devuelve 401."""
        response = client.post('/api/carrito/add', json={'codigo': 'ABC'})
        assert response.status_code == 401

    def test_carrito_clear_requires_auth(self, client):
        """DELETE /api/carrito/clear sin sesión devuelve 401."""
        response = client.delete('/api/carrito/clear')
        assert response.status_code == 401
