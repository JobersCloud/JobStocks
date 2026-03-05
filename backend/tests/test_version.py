"""Smoke tests: endpoint /api/version y health check básico."""


class TestVersion:
    def test_version_returns_200(self, client):
        """El endpoint /api/version debe responder con 200."""
        response = client.get('/api/version')
        assert response.status_code == 200

    def test_version_returns_json(self, client):
        """El endpoint /api/version debe devolver JSON con clave 'version'."""
        response = client.get('/api/version')
        data = response.get_json()
        assert 'version' in data

    def test_version_format(self, client):
        """La versión debe empezar con 'v' y tener formato semántico."""
        response = client.get('/api/version')
        data = response.get_json()
        version = data['version']
        assert version.startswith('v')
        parts = version[1:].split('.')
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)
