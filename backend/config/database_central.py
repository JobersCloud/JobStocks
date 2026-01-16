# ============================================================
# ARCHIVO: config/database_central.py
# Conexión a BD Central (jobers_control_usuarios)
# ============================================================

import pyodbc
import os
from pathlib import Path

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class DatabaseCentral:
    """Conexión a la BD central que contiene la tabla empresa_cliente"""

    DB_CONFIG = {
        'server': os.environ.get('DB_CENTRAL_SERVER', '192.168.63.36,1434'),
        'database': os.environ.get('DB_CENTRAL_NAME', 'jobers_control_usuarios'),
        'username': os.environ.get('DB_CENTRAL_USER', 'sa'),
        'password': os.environ.get('DB_CENTRAL_PASSWORD', 'Desa1'),
        'driver': os.environ.get('DB_DRIVER', '{ODBC Driver 18 for SQL Server}'),
    }

    @staticmethod
    def get_connection():
        """Crea y retorna una conexión a la BD central"""
        conn_str = (
            f"DRIVER={DatabaseCentral.DB_CONFIG['driver']};"
            f"SERVER={DatabaseCentral.DB_CONFIG['server']};"
            f"DATABASE={DatabaseCentral.DB_CONFIG['database']};"
            f"UID={DatabaseCentral.DB_CONFIG['username']};"
            f"PWD={DatabaseCentral.DB_CONFIG['password']};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=no;"
        )
        return pyodbc.connect(conn_str)
