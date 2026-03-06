"""Tests de endpoints de usuarios: listar, crear, activar, desactivar, cambiar rol."""
from unittest.mock import patch, MagicMock


class TestUsuariosAuth:
    def test_listar_requires_auth(self, client):
        """GET /api/usuarios sin sesión devuelve 401."""
        response = client.get('/api/usuarios')
        assert response.status_code == 401

    def test_crear_requires_auth(self, client):
        """POST /api/usuarios sin sesión devuelve 401."""
        response = client.post('/api/usuarios', json={'username': 'test'})
        assert response.status_code == 401

    def test_activar_requires_auth(self, client):
        """POST /api/usuarios/1/activar sin sesión devuelve 401."""
        response = client.post('/api/usuarios/1/activar')
        assert response.status_code == 401

    def test_desactivar_requires_auth(self, client):
        """POST /api/usuarios/1/desactivar sin sesión devuelve 401."""
        response = client.post('/api/usuarios/1/desactivar')
        assert response.status_code == 401

    def test_cambiar_rol_requires_auth(self, client):
        """PUT /api/usuarios/1/rol sin sesión devuelve 401."""
        response = client.put('/api/usuarios/1/rol', json={'rol': 'administrador'})
        assert response.status_code == 401


class TestUsuariosRol:
    @patch('app.get_user_by_id')
    def test_listar_requires_admin(self, mock_get_user, auth_client):
        """GET /api/usuarios con rol usuario devuelve 403."""
        mock_get_user.return_value = {
            'id': 1, 'username': 'user', 'email': 'u@t.com',
            'full_name': 'User', 'rol': 'usuario', 'empresa_id': '1',
            'cliente_id': None, 'debe_cambiar_password': False,
            'company_name': 'Test', 'mostrar_precios': False,
            'administrador_clientes': False
        }
        response = auth_client['client'].get('/api/usuarios')
        assert response.status_code == 403


class TestUsuariosEndpoints:
    @patch('database.users_db.get_all_users_by_empresa')
    def test_listar_usuarios(self, mock_list, admin_client):
        """GET /api/usuarios con admin devuelve lista."""
        mock_list.return_value = [
            {'id': 1, 'username': 'user1', 'full_name': 'User One', 'rol': 'usuario'}
        ]
        response = admin_client['client'].get('/api/usuarios')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_crear_usuario_sin_datos(self, admin_client):
        """POST /api/usuarios sin datos devuelve 400."""
        response = admin_client['client'].post(
            '/api/usuarios',
            json={},
            headers={'X-CSRF-Token': admin_client['csrf_token']}
        )
        assert response.status_code == 400

    def test_crear_usuario_sin_username(self, admin_client):
        """POST /api/usuarios sin username devuelve 400."""
        response = admin_client['client'].post(
            '/api/usuarios',
            json={'password': 'Test1234!', 'empresa_id': '1'},
            headers={'X-CSRF-Token': admin_client['csrf_token']}
        )
        assert response.status_code == 400

    @patch('routes.usuario_routes.activate_user')
    def test_activar_usuario(self, mock_activate, admin_client):
        """POST /api/usuarios/2/activar con admin funciona."""
        mock_activate.return_value = True
        response = admin_client['client'].post(
            '/api/usuarios/2/activar',
            headers={'X-CSRF-Token': admin_client['csrf_token']}
        )
        assert response.status_code == 200

    @patch('routes.usuario_routes.deactivate_user')
    def test_desactivar_usuario(self, mock_deactivate, admin_client):
        """POST /api/usuarios/2/desactivar con admin funciona."""
        mock_deactivate.return_value = True
        response = admin_client['client'].post(
            '/api/usuarios/2/desactivar',
            headers={'X-CSRF-Token': admin_client['csrf_token']}
        )
        assert response.status_code == 200

    @patch('routes.usuario_routes.update_user_rol')
    def test_cambiar_rol(self, mock_update, superuser_client):
        """PUT /api/usuarios/2/rol con superusuario funciona."""
        mock_update.return_value = True
        response = superuser_client['client'].put(
            '/api/usuarios/2/rol',
            json={'rol': 'administrador'},
            headers={'X-CSRF-Token': superuser_client['csrf_token']}
        )
        assert response.status_code == 200

    def test_cambiar_rol_requires_superuser(self, admin_client):
        """PUT /api/usuarios/2/rol con admin devuelve 403 (requiere superusuario)."""
        response = admin_client['client'].put(
            '/api/usuarios/2/rol',
            json={'rol': 'administrador'},
            headers={'X-CSRF-Token': admin_client['csrf_token']}
        )
        assert response.status_code == 403


class TestCambiarPassword:
    def test_cambiar_password_requires_auth(self, client):
        """POST /api/usuarios/cambiar-password sin sesión devuelve 401."""
        response = client.post('/api/usuarios/cambiar-password',
                               json={'new_password': 'Test1234!'})
        assert response.status_code == 401
