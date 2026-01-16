# ============================================================
#      ██╗ ██████╗ ██████╗ ███████╗██████╗ ███████╗
#      ██║██╔═══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝
#      ██║██║   ██║██████╔╝█████╗  ██████╔╝███████╗
# ██   ██║██║   ██║██╔══██╗██╔══╝  ██╔══██╗╚════██║
# ╚█████╔╝╚██████╔╝██████╔╝███████╗██║  ██║███████║
#  ╚════╝  ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝
#
#                ──  Jobers - Iaucejo  ──
#
# Autor : iaucejo
# Fecha : 2026-01-08
# ============================================================


# ============================================
# ARCHIVO: config/database.py
# Conexión dinámica según empresa_cli_id
# ============================================

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


class Database:
    """
    Conexión dinámica a BD según empresa.

    Flujo:
    1. Se recibe empresa_cli_id por parámetro
    2. Se consulta empresa_cliente en BD central
    3. Se conecta a la BD de esa empresa
    """

    # Driver ODBC por defecto
    DEFAULT_DRIVER = os.environ.get('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')

    @staticmethod
    def get_connection(empresa_cli_id=None):
        """
        Crea y retorna una conexión a la BD de la empresa.

        Args:
            empresa_cli_id: ID de empresa (opcional, se obtiene de sesión si no se pasa)

        Returns:
            pyodbc.Connection a la BD de la empresa

        Raises:
            ValueError: Si no hay empresa en contexto o no existe
        """
        # Si no se pasa, obtener de la sesión de Flask
        if empresa_cli_id is None:
            from flask import session, has_request_context
            if has_request_context():
                empresa_cli_id = session.get('empresa_cli_id')

        if empresa_cli_id is None:
            raise ValueError("No hay empresa en contexto. Accede con ?empresa=X primero.")

        # Importar aquí para evitar imports circulares
        from models.empresa_cliente_model import EmpresaClienteModel

        # Obtener datos de conexión de la empresa (con caché)
        empresa = EmpresaClienteModel.get_by_id(empresa_cli_id)

        if not empresa:
            raise ValueError(f"Empresa con ID {empresa_cli_id} no encontrada")

        # Construir string de conexión
        server = empresa['dbserver']
        if empresa['dbport'] and empresa['dbport'] != 1433:
            server = f"{server},{empresa['dbport']}"

        conn_str = (
            f"DRIVER={Database.DEFAULT_DRIVER};"
            f"SERVER={server};"
            f"DATABASE={empresa['dbname']};"
            f"UID={empresa['dblogin']};"
            f"PWD={empresa['dbpass']};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=no;"
        )

        return pyodbc.connect(conn_str)

    @staticmethod
    def get_empresa_erp(empresa_cli_id=None):
        """
        Obtiene el código empresa_erp para usar en filtros.

        Args:
            empresa_cli_id: ID de empresa (opcional, se obtiene de sesión)

        Returns:
            str: código empresa_erp o None
        """
        # Primero intentar de la sesión (más rápido, ya está cacheado)
        from flask import session, has_request_context
        if has_request_context():
            empresa_erp = session.get('empresa_erp')
            if empresa_erp:
                return empresa_erp

        # Si no está en sesión, obtener de BD central
        if empresa_cli_id is None:
            if has_request_context():
                empresa_cli_id = session.get('empresa_cli_id')

        if empresa_cli_id:
            from models.empresa_cliente_model import EmpresaClienteModel
            empresa = EmpresaClienteModel.get_by_id(empresa_cli_id)
            if empresa:
                return empresa.get('empresa_erp')

        return None

    @staticmethod
    def get_empresa_info(empresa_cli_id):
        """
        Obtiene toda la información de la empresa.

        Args:
            empresa_cli_id: ID de empresa (de tabla empresa_cliente)

        Returns:
            dict con datos de la empresa o None
        """
        from models.empresa_cliente_model import EmpresaClienteModel
        return EmpresaClienteModel.get_by_id(empresa_cli_id)

    @staticmethod
    def get_central_connection():
        """
        Retorna conexión a la BD central (jobers_control_usuarios).
        Útil para grabar logs, auditorías, estadísticas, etc.

        Returns:
            pyodbc.Connection a la BD central
        """
        from config.database_central import DatabaseCentral
        return DatabaseCentral.get_connection()
