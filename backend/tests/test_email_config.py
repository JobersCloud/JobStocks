"""Tests de endpoints de configuración de email."""
from unittest.mock import patch, MagicMock


class TestEmailConfigAuth:
    def test_listar_requires_auth(self, client):
        """GET /api/email-config sin sesión devuelve 401."""
        response = client.get('/api/email-config')
        assert response.status_code == 401

    def test_active_requires_auth(self, client):
        """GET /api/email-config/active sin sesión devuelve 401."""
        response = client.get('/api/email-config/active')
        assert response.status_code == 401

    def test_update_requires_auth(self, client):
        """PUT /api/email-config/1 sin sesión devuelve 401."""
        response = client.put('/api/email-config/1', json={'smtp_server': 'smtp.test.com'})
        assert response.status_code == 401


class TestEmailConfigEndpoints:
    @patch('models.email_config_model.EmailConfigModel.get_all_configs')
    def test_listar_configs(self, mock_get, admin_client):
        """GET /api/email-config con admin devuelve lista."""
        mock_get.return_value = [
            {
                'id': 1,
                'nombre_configuracion': 'SMTP Principal',
                'smtp_server': 'smtp.test.com',
                'smtp_port': 587,
                'email_from': 'test@test.com',
                'email_password': 'secret123',
                'email_to': 'dest@test.com',
                'activo': True
            }
        ]
        response = admin_client['client'].get('/api/email-config')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        # Verificar que la contraseña está oculta
        assert data[0]['email_password'] == '********'

    @patch('models.email_config_model.EmailConfigModel.get_active_config')
    def test_active_config(self, mock_get, admin_client):
        """GET /api/email-config/active devuelve config activa."""
        mock_get.return_value = {
            'id': 1,
            'nombre_configuracion': 'SMTP Principal',
            'smtp_server': 'smtp.test.com',
            'email_password': 'secret',
            'activo': True
        }
        response = admin_client['client'].get('/api/email-config/active')
        assert response.status_code == 200
        data = response.get_json()
        assert data['email_password'] == '********'

    @patch('models.email_config_model.EmailConfigModel.get_active_config')
    def test_active_config_not_found(self, mock_get, admin_client):
        """GET /api/email-config/active sin config activa devuelve 404."""
        mock_get.return_value = None
        response = admin_client['client'].get('/api/email-config/active')
        assert response.status_code == 404

    @patch('models.email_config_model.EmailConfigModel.update_config')
    def test_update_config(self, mock_update, admin_client):
        """PUT /api/email-config/1 actualiza configuración."""
        mock_update.return_value = True
        response = admin_client['client'].put(
            '/api/email-config/1',
            json={
                'nombre_configuracion': 'Actualizada',
                'smtp_server': 'smtp.new.com',
                'smtp_port': 465,
                'email_from': 'new@test.com',
                'email_to': 'dest@test.com'
            },
            headers={'X-CSRF-Token': admin_client['csrf_token']}
        )
        assert response.status_code == 200
