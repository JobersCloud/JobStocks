"""Tests de endpoints de consultas sobre productos."""
from unittest.mock import patch, MagicMock


class TestConsultasAuth:
    def test_listar_requires_auth(self, client):
        """GET /api/consultas sin sesión devuelve 401."""
        response = client.get('/api/consultas')
        assert response.status_code == 401

    def test_crear_requires_auth(self, client):
        """POST /api/consultas sin sesión devuelve 401 (before_request)."""
        response = client.post('/api/consultas', json={
            'codigo_producto': 'ABC',
            'nombre_cliente': 'Test',
            'email_cliente': 'test@test.com',
            'mensaje': 'test'
        })
        assert response.status_code == 401


class TestConsultasRol:
    @patch('app.get_user_by_id')
    def test_listar_requires_admin(self, mock_get_user, auth_client):
        """GET /api/consultas con rol usuario devuelve 403."""
        mock_get_user.return_value = {
            'id': 1, 'username': 'user', 'email': 'u@t.com',
            'full_name': 'User', 'rol': 'usuario', 'empresa_id': '1',
            'cliente_id': None, 'debe_cambiar_password': False,
            'company_name': 'Test', 'mostrar_precios': False,
            'administrador_clientes': False
        }
        response = auth_client['client'].get('/api/consultas')
        assert response.status_code == 403


class TestConsultasEndpoints:
    @patch('models.consulta_model.ConsultaModel.get_all_by_empresa')
    def test_listar_consultas(self, mock_get, admin_client):
        """GET /api/consultas con admin devuelve lista."""
        mock_get.return_value = [
            {'id': 1, 'codigo_producto': 'ABC', 'estado': 'pendiente'}
        ]
        response = admin_client['client'].get('/api/consultas')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['total'] == 1

    @patch('models.consulta_model.ConsultaModel.crear')
    def test_crear_consulta(self, mock_crear, admin_client):
        """POST /api/consultas crea consulta (requiere auth por before_request)."""
        mock_crear.return_value = 1
        response = admin_client['client'].post('/api/consultas', json={
            'codigo_producto': 'ABC123',
            'nombre_cliente': 'Juan',
            'email_cliente': 'juan@test.com',
            'mensaje': 'Consulta de test'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['consulta_id'] == 1

    def test_crear_consulta_sin_campos(self, admin_client):
        """POST /api/consultas sin campos requeridos devuelve 400."""
        response = admin_client['client'].post('/api/consultas', json={
            'codigo_producto': 'ABC123'
        })
        assert response.status_code == 400

    @patch('models.consulta_model.ConsultaModel.crear')
    def test_crear_consulta_error_bd(self, mock_crear, admin_client):
        """POST /api/consultas con error de BD devuelve 500."""
        mock_crear.return_value = None
        response = admin_client['client'].post('/api/consultas', json={
            'codigo_producto': 'ABC123',
            'nombre_cliente': 'Juan',
            'email_cliente': 'juan@test.com',
            'mensaje': 'Test'
        })
        assert response.status_code == 500


class TestWhatsappConfig:
    @patch('models.parametros_model.ParametrosModel.get')
    def test_whatsapp_config(self, mock_get, admin_client):
        """GET /api/consultas/whatsapp-config devuelve número."""
        mock_get.return_value = '+34612345678'
        response = admin_client['client'].get('/api/consultas/whatsapp-config')
        assert response.status_code == 200
        data = response.get_json()
        assert 'numero' in data
