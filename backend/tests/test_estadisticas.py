"""Tests de endpoints de estadísticas del dashboard."""
from unittest.mock import patch, MagicMock


class TestEstadisticasAuth:
    def test_resumen_requires_auth(self, client):
        """GET /api/estadisticas/resumen sin sesión devuelve 401."""
        response = client.get('/api/estadisticas/resumen')
        assert response.status_code == 401

    def test_productos_requires_auth(self, client):
        """GET /api/estadisticas/productos-mas-solicitados sin sesión devuelve 401."""
        response = client.get('/api/estadisticas/productos-mas-solicitados')
        assert response.status_code == 401

    def test_propuestas_por_dia_requires_auth(self, client):
        """GET /api/estadisticas/propuestas-por-dia sin sesión devuelve 401."""
        response = client.get('/api/estadisticas/propuestas-por-dia')
        assert response.status_code == 401

    def test_propuestas_por_estado_requires_auth(self, client):
        """GET /api/estadisticas/propuestas-por-estado sin sesión devuelve 401."""
        response = client.get('/api/estadisticas/propuestas-por-estado')
        assert response.status_code == 401

    def test_propuestas_por_mes_requires_auth(self, client):
        """GET /api/estadisticas/propuestas-por-mes sin sesión devuelve 401."""
        response = client.get('/api/estadisticas/propuestas-por-mes')
        assert response.status_code == 401

    def test_usuarios_activos_requires_auth(self, client):
        """GET /api/estadisticas/usuarios-mas-activos sin sesión devuelve 401."""
        response = client.get('/api/estadisticas/usuarios-mas-activos')
        assert response.status_code == 401


class TestEstadisticasRol:
    @patch('app.get_user_by_id')
    def test_resumen_requires_admin(self, mock_get_user, auth_client):
        """GET /api/estadisticas/resumen con rol usuario devuelve 403."""
        mock_get_user.return_value = {
            'id': 1, 'username': 'user', 'email': 'u@t.com',
            'full_name': 'User', 'rol': 'usuario', 'empresa_id': '1',
            'cliente_id': None, 'debe_cambiar_password': False,
            'company_name': 'Test', 'mostrar_precios': False,
            'administrador_clientes': False
        }
        response = auth_client['client'].get('/api/estadisticas/resumen')
        assert response.status_code == 403


class TestEstadisticasEndpoints:
    @patch('models.estadisticas_model.EstadisticasModel.get_resumen')
    def test_resumen(self, mock_get, admin_client):
        """GET /api/estadisticas/resumen con admin devuelve datos."""
        mock_get.return_value = {
            'total_propuestas': 10,
            'propuestas_pendientes': 3,
            'usuarios_activos': 5,
            'consultas_pendientes': 2,
            'total_items_solicitados': 50
        }
        response = admin_client['client'].get('/api/estadisticas/resumen')
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_propuestas' in data

    @patch('models.estadisticas_model.EstadisticasModel.get_productos_mas_solicitados')
    def test_productos_mas_solicitados(self, mock_get, admin_client):
        """GET /api/estadisticas/productos-mas-solicitados devuelve lista."""
        mock_get.return_value = [
            {'codigo': 'ABC', 'descripcion': 'Test', 'total_solicitado': 100}
        ]
        response = admin_client['client'].get('/api/estadisticas/productos-mas-solicitados')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1

    @patch('models.estadisticas_model.EstadisticasModel.get_propuestas_por_periodo')
    def test_propuestas_por_dia(self, mock_get, admin_client):
        """GET /api/estadisticas/propuestas-por-dia devuelve datos."""
        mock_get.return_value = [
            {'fecha': '2026-03-01', 'cantidad': 5}
        ]
        response = admin_client['client'].get('/api/estadisticas/propuestas-por-dia')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    @patch('models.estadisticas_model.EstadisticasModel.get_propuestas_por_periodo')
    def test_propuestas_por_dia_con_parametro(self, mock_get, admin_client):
        """GET /api/estadisticas/propuestas-por-dia?dias=7 respeta parámetro."""
        mock_get.return_value = []
        response = admin_client['client'].get('/api/estadisticas/propuestas-por-dia?dias=7')
        assert response.status_code == 200
        mock_get.assert_called_once()
