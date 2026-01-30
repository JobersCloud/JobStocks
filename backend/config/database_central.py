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
    """
    Conexión a la BD central que contiene la tabla empresa_cliente.

    IMPORTANTE: Las variables de entorno son OBLIGATORIAS:
    - DB_CENTRAL_SERVER: Servidor de BD central (ej: 127.0.0.1,1433)
    - DB_CENTRAL_NAME: Nombre de la BD central
    - DB_CENTRAL_USER: Usuario de BD
    - DB_CENTRAL_PASSWORD: Contraseña de BD
    - DB_DRIVER: Driver ODBC (opcional, default: ODBC Driver 18)
    """

    @staticmethod
    def get_connection():
        """Crea y retorna una conexión a la BD central"""
        # Leer variables de entorno (OBLIGATORIAS, sin valores por defecto)
        server = os.environ.get('DB_CENTRAL_SERVER')
        database = os.environ.get('DB_CENTRAL_NAME')
        username = os.environ.get('DB_CENTRAL_USER')
        password = os.environ.get('DB_CENTRAL_PASSWORD')
        driver = os.environ.get('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')

        # Validar que las variables obligatorias estén definidas
        if not server:
            raise ValueError("DB_CENTRAL_SERVER no está configurado. Defina la variable de entorno.")
        if not database:
            raise ValueError("DB_CENTRAL_NAME no está configurado. Defina la variable de entorno.")
        if not username:
            raise ValueError("DB_CENTRAL_USER no está configurado. Defina la variable de entorno.")
        if not password:
            raise ValueError("DB_CENTRAL_PASSWORD no está configurado. Defina la variable de entorno.")

        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
        return pyodbc.connect(conn_str)
