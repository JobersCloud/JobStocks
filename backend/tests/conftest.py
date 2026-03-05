"""
Fixtures compartidas para tests de ApiRestExternos.

Estrategia de mocking:
- Se mockea Database.get_connection() para evitar conexiones reales a SQL Server
- Se mockea verify_user() para simular login
- La sesión Flask se pre-popula con connection, empresa_id, csrf_token
"""
import sys
import os
import secrets
from unittest.mock import MagicMock, patch

import pytest

# Asegurar que el backend está en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(autouse=True)
def mock_database():
    """Mock global de Database.get_connection para todos los tests."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []

    with patch('config.database.Database.get_connection', return_value=mock_conn):
        yield {'connection': mock_conn, 'cursor': mock_cursor}


@pytest.fixture(autouse=True)
def mock_database_central():
    """Mock global de DatabaseCentral.get_connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []

    with patch('config.database_central.DatabaseCentral.get_connection', return_value=mock_conn):
        yield {'connection': mock_conn, 'cursor': mock_cursor}


@pytest.fixture
def app():
    """Crea la aplicación Flask para testing."""
    # Mock de EmpresaClienteModel antes de importar app
    with patch('models.empresa_cliente_model.EmpresaClienteModel.get_by_id') as mock_empresa:
        mock_empresa.return_value = {
            'empresa_cli_id': 1,
            'nombre': 'Test Corp',
            'dbserver': 'localhost',
            'dbport': 1433,
            'dblogin': 'sa',
            'dbpass': 'test',
            'dbname': 'TestDB',
            'correo_id': None,
            'key_ws': None,
            'cif': 'B12345678',
            'traductor': None,
            'tipo': 1,
            'empresa_erp': '1'
        }

        from app import app as flask_app

        flask_app.config['TESTING'] = True
        flask_app.config['WTF_CSRF_ENABLED'] = False
        yield flask_app


@pytest.fixture
def client(app):
    """Cliente de test para hacer peticiones HTTP."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Cliente autenticado con sesión pre-populada."""
    csrf_token = secrets.token_hex(16)

    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['connection'] = '1'
        sess['empresa_id'] = '1'
        sess['csrf_token'] = csrf_token
        sess['db_config'] = {
            'dbserver': 'localhost',
            'dbport': 1433,
            'dblogin': 'sa',
            'dbpass': 'test',
            'dbname': 'TestDB'
        }

    return {'client': client, 'csrf_token': csrf_token}
