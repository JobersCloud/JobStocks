"""Tests de endpoints de propuestas: listar, detalle, cambiar estado."""
from unittest.mock import patch, MagicMock


class TestPropuestasAuth:
    def test_mis_propuestas_requires_auth(self, client):
        """GET /api/propuestas/mis-propuestas sin sesión devuelve 401."""
        response = client.get('/api/propuestas/mis-propuestas')
        assert response.status_code == 401

    def test_todas_propuestas_requires_auth(self, client):
        """GET /api/propuestas sin sesión devuelve 401."""
        response = client.get('/api/propuestas')
        assert response.status_code == 401

    def test_pendientes_requires_auth(self, client):
        """GET /api/propuestas/pendientes sin sesión devuelve 401."""
        response = client.get('/api/propuestas/pendientes')
        assert response.status_code == 401

    def test_detalle_requires_auth(self, client):
        """GET /api/propuestas/1 sin sesión devuelve 401."""
        response = client.get('/api/propuestas/1')
        assert response.status_code == 401

    def test_cambiar_estado_requires_auth(self, client):
        """PUT /api/propuestas/1/estado sin sesión devuelve 401."""
        response = client.put('/api/propuestas/1/estado',
                              json={'estado': 'Procesada'})
        assert response.status_code == 401


class TestPropuestasRol:
    @patch('app.get_user_by_id')
    def test_todas_propuestas_requires_admin(self, mock_get_user, auth_client):
        """GET /api/propuestas con rol usuario devuelve 403."""
        mock_get_user.return_value = {
            'id': 1, 'username': 'user', 'email': 'u@t.com',
            'full_name': 'User', 'rol': 'usuario', 'empresa_id': '1',
            'cliente_id': None, 'debe_cambiar_password': False,
            'company_name': 'Test', 'mostrar_precios': False,
            'administrador_clientes': False
        }
        response = auth_client['client'].get('/api/propuestas')
        assert response.status_code == 403


class TestPropuestasEndpoints:
    @patch('models.propuesta_model.PropuestaModel.get_by_user')
    def test_mis_propuestas(self, mock_get, admin_client):
        """GET /api/propuestas/mis-propuestas devuelve lista."""
        mock_get.return_value = [
            {'id': 1, 'estado': 'Enviada', 'total_items': 3}
        ]
        response = admin_client['client'].get('/api/propuestas/mis-propuestas')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    @patch('models.propuesta_model.PropuestaModel.get_all')
    def test_todas_propuestas(self, mock_get, admin_client):
        """GET /api/propuestas con admin devuelve lista."""
        mock_get.return_value = [
            {'id': 1, 'estado': 'Enviada'},
            {'id': 2, 'estado': 'Procesada'}
        ]
        response = admin_client['client'].get('/api/propuestas')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 2

    @patch('models.propuesta_model.PropuestaModel.get_pendientes')
    def test_pendientes(self, mock_get, admin_client):
        """GET /api/propuestas/pendientes devuelve propuestas pendientes."""
        mock_get.return_value = [
            {'id': 1, 'estado': 'Enviada'}
        ]
        response = admin_client['client'].get('/api/propuestas/pendientes')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    @patch('models.propuesta_model.PropuestaModel.get_by_id')
    def test_detalle_propuesta(self, mock_get, admin_client):
        """GET /api/propuestas/1 devuelve detalle."""
        mock_get.return_value = {
            'id': 1, 'estado': 'Enviada', 'lineas': []
        }
        response = admin_client['client'].get('/api/propuestas/1')
        assert response.status_code == 200

    @patch('models.propuesta_model.PropuestaModel.get_by_id')
    def test_detalle_propuesta_no_encontrada(self, mock_get, admin_client):
        """GET /api/propuestas/999 no encontrada devuelve 404."""
        mock_get.return_value = None
        response = admin_client['client'].get('/api/propuestas/999')
        assert response.status_code == 404

    @patch('models.propuesta_model.PropuestaModel.actualizar_estado')
    @patch('models.propuesta_model.PropuestaModel.get_by_id')
    def test_cambiar_estado(self, mock_get, mock_update, admin_client):
        """PUT /api/propuestas/1/estado con admin funciona."""
        mock_get.return_value = {'id': 1, 'estado': 'Enviada'}
        mock_update.return_value = True
        response = admin_client['client'].put(
            '/api/propuestas/1/estado',
            json={'estado': 'Procesada'},
            headers={'X-CSRF-Token': admin_client['csrf_token']}
        )
        assert response.status_code == 200

    def test_cambiar_estado_sin_body(self, admin_client):
        """PUT /api/propuestas/1/estado sin estado devuelve 400."""
        response = admin_client['client'].put(
            '/api/propuestas/1/estado',
            json={},
            headers={'X-CSRF-Token': admin_client['csrf_token']}
        )
        assert response.status_code == 400
