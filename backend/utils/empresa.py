# ============================================================
# ARCHIVO: utils/empresa.py
# Utilidades centralizadas para gestión de empresa
# ============================================================

from flask import session, request, g
from config.database import Database


def get_connection():
    """
    Obtiene el connection (empresa_cli_id) del contexto actual.

    Orden de búsqueda:
    1. Variable global g (si ya se resolvió en esta request)
    2. Sesión del usuario
    3. Parámetro URL (?empresa=X o ?connection=X)

    Returns:
        int o str: connection o None
    """
    # 1. Verificar si ya está en g (caché de request)
    if hasattr(g, 'connection') and g.connection:
        return g.connection

    connection = None

    # 2. Buscar en sesión
    if 'connection' in session:
        connection = session['connection']

    # 3. Buscar en parámetros URL
    if not connection:
        connection = request.args.get('empresa') or request.args.get('connection')

    # Guardar en g para caché de request
    if connection:
        g.connection = connection

    return connection


# Alias para compatibilidad
def get_empresa_cli_id():
    """Alias para get_connection() - mantener compatibilidad."""
    return get_connection()


def get_empresa_id():
    """
    Obtiene el código empresa_id (empresa_erp) para filtrar datos.

    Returns:
        str: código empresa_id o None
    """
    # 1. Verificar caché en g
    if hasattr(g, 'empresa_id') and g.empresa_id:
        return g.empresa_id

    # 2. Verificar sesión
    if 'empresa_id' in session:
        g.empresa_id = session['empresa_id']
        return g.empresa_id

    # 3. Obtener de BD central
    connection = get_connection()
    if connection:
        empresa_id = Database.get_empresa_erp(connection)
        if empresa_id:
            g.empresa_id = empresa_id
            return empresa_id

    return None


# Alias para compatibilidad
def get_empresa_erp():
    """Alias para get_empresa_id() - mantener compatibilidad."""
    return get_empresa_id()


def get_empresa_info():
    """
    Obtiene toda la información de la empresa actual.

    Returns:
        dict: información completa de la empresa o None
    """
    connection = get_connection()
    if connection:
        return Database.get_empresa_info(connection)
    return None


def init_empresa_session(connection_id):
    """
    Inicializa la sesión con los datos de empresa.
    Llamar cuando el usuario accede con ?empresa=X

    Args:
        connection_id: ID de la conexión (empresa_cli_id)

    Returns:
        dict: información de la empresa o None si no existe
    """
    from models.empresa_cliente_model import EmpresaClienteModel

    empresa = EmpresaClienteModel.get_by_id(connection_id)

    if empresa:
        # Guardar en sesión
        session['connection'] = connection_id
        session['empresa_id'] = empresa.get('empresa_erp')
        session['empresa_nombre'] = empresa.get('nombre')

        # Guardar en g para esta request
        g.connection = connection_id
        g.empresa_id = empresa.get('empresa_erp')

        return empresa

    return None


def validar_empresa():
    """
    Valida que haya una empresa configurada en el contexto.

    Returns:
        tuple: (connection, empresa_id) o (None, None)

    Raises:
        ValueError: Si no hay empresa configurada
    """
    connection = get_connection()
    empresa_id = get_empresa_id()

    if not connection:
        raise ValueError("No se ha especificado empresa")

    if not empresa_id:
        raise ValueError(f"Empresa {connection} no encontrada o sin empresa_id configurado")

    return connection, empresa_id


def get_db_connection():
    """
    Obtiene una conexión a la BD de la empresa actual.

    Returns:
        pyodbc.Connection

    Raises:
        ValueError: Si no hay empresa configurada
    """
    connection = get_connection()
    if not connection:
        raise ValueError("No se ha especificado empresa para la conexión")

    return Database.get_connection(connection)
