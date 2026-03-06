"""Tests de endpoints de parámetros: públicos y protegidos."""
from unittest.mock import patch, MagicMock


class TestParametrosPublicos:
    @patch('models.parametros_model.ParametrosModel.permitir_propuestas')
    def test_propuestas_habilitadas(self, mock_param, client):
        """GET /api/parametros/propuestas-habilitadas es público."""
        mock_param.return_value = True
        response = client.get('/api/parametros/propuestas-habilitadas?connection=1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'habilitado' in data


class TestParametrosAuth:
    def test_listar_requires_auth(self, client):
        """GET /api/parametros sin sesión devuelve 401."""
        response = client.get('/api/parametros')
        assert response.status_code == 401

    def test_actualizar_requires_auth(self, client):
        """PUT /api/parametros/TEST sin sesión devuelve 401."""
        response = client.put('/api/parametros/TEST', json={'valor': '1'})
        assert response.status_code == 401

    def test_firma_habilitada_requires_auth(self, client):
        """GET /api/parametros/firma-habilitada sin sesión devuelve 401."""
        response = client.get('/api/parametros/firma-habilitada')
        assert response.status_code == 401

    def test_grid_con_imagenes_requires_auth(self, client):
        """GET /api/parametros/grid-con-imagenes sin sesión devuelve 401."""
        response = client.get('/api/parametros/grid-con-imagenes')
        assert response.status_code == 401


class TestParametrosRol:
    @patch('app.get_user_by_id')
    def test_listar_requires_superusuario(self, mock_get_user, auth_client):
        """GET /api/parametros con rol usuario devuelve 403."""
        mock_get_user.return_value = {
            'id': 1, 'username': 'user', 'email': 'u@t.com',
            'full_name': 'User', 'rol': 'usuario', 'empresa_id': '1',
            'cliente_id': None, 'debe_cambiar_password': False,
            'company_name': 'Test', 'mostrar_precios': False,
            'administrador_clientes': False
        }
        response = auth_client['client'].get('/api/parametros')
        assert response.status_code == 403

    @patch('app.get_user_by_id')
    def test_listar_admin_not_sufficient(self, mock_get_user, auth_client):
        """GET /api/parametros con rol admin devuelve 403 (necesita superusuario)."""
        mock_get_user.return_value = {
            'id': 1, 'username': 'admin', 'email': 'a@t.com',
            'full_name': 'Admin', 'rol': 'administrador', 'empresa_id': '1',
            'cliente_id': None, 'debe_cambiar_password': False,
            'company_name': 'Test', 'mostrar_precios': False,
            'administrador_clientes': False
        }
        response = auth_client['client'].get('/api/parametros')
        assert response.status_code == 403


class TestParametrosEndpoints:
    @patch('models.parametros_model.ParametrosModel.get_all')
    def test_listar_parametros(self, mock_get, superuser_client):
        """GET /api/parametros con superusuario devuelve lista."""
        mock_get.return_value = [
            {'clave': 'PERMITIR_REGISTRO', 'valor': '1', 'descripcion': 'Test'}
        ]
        response = superuser_client['client'].get('/api/parametros')
        assert response.status_code == 200
