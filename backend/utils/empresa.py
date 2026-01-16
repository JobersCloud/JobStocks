# ============================================================
# ARCHIVO: utils/empresa.py
# Utilidades centralizadas para gestión de empresa
# ============================================================

from flask import session, request, g
from config.database import Database


def get_empresa_cli_id():
    """
    Obtiene el empresa_cli_id del contexto actual.

    Orden de búsqueda:
    1. Variable global g (si ya se resolvió en esta request)
    2. Sesión del usuario
    3. Parámetro URL (?empresa=X o ?empresa_id=X)

    Returns:
        int o str: empresa_cli_id o None
    """
    # 1. Verificar si ya está en g (caché de request)
    if hasattr(g, 'empresa_cli_id') and g.empresa_cli_id:
        return g.empresa_cli_id

    empresa_cli_id = None

    # 2. Buscar en sesión
    if 'empresa_cli_id' in session:
        empresa_cli_id = session['empresa_cli_id']

    # 3. Buscar en parámetros URL
    if not empresa_cli_id:
        empresa_cli_id = request.args.get('empresa') or request.args.get('empresa_id')

    # Guardar en g para caché de request
    if empresa_cli_id:
        g.empresa_cli_id = empresa_cli_id

    return empresa_cli_id


def get_empresa_erp():
    """
    Obtiene el código empresa_erp para filtrar datos.

    Returns:
        str: código empresa_erp o None
    """
    # 1. Verificar caché en g
    if hasattr(g, 'empresa_erp') and g.empresa_erp:
        return g.empresa_erp

    # 2. Verificar sesión
    if 'empresa_erp' in session:
        g.empresa_erp = session['empresa_erp']
        return g.empresa_erp

    # 3. Obtener de BD central
    empresa_cli_id = get_empresa_cli_id()
    if empresa_cli_id:
        empresa_erp = Database.get_empresa_erp(empresa_cli_id)
        if empresa_erp:
            g.empresa_erp = empresa_erp
            return empresa_erp

    return None


def get_empresa_info():
    """
    Obtiene toda la información de la empresa actual.

    Returns:
        dict: información completa de la empresa o None
    """
    empresa_cli_id = get_empresa_cli_id()
    if empresa_cli_id:
        return Database.get_empresa_info(empresa_cli_id)
    return None


def init_empresa_session(empresa_cli_id):
    """
    Inicializa la sesión con los datos de empresa.
    Llamar cuando el usuario accede con ?empresa=X

    Args:
        empresa_cli_id: ID de la empresa

    Returns:
        dict: información de la empresa o None si no existe
    """
    from models.empresa_cliente_model import EmpresaClienteModel

    empresa = EmpresaClienteModel.get_by_id(empresa_cli_id)

    if empresa:
        # Guardar en sesión
        session['empresa_cli_id'] = empresa_cli_id
        session['empresa_erp'] = empresa.get('empresa_erp')
        session['empresa_nombre'] = empresa.get('nombre')

        # Guardar en g para esta request
        g.empresa_cli_id = empresa_cli_id
        g.empresa_erp = empresa.get('empresa_erp')

        return empresa

    return None


def validar_empresa():
    """
    Valida que haya una empresa configurada en el contexto.

    Returns:
        tuple: (empresa_cli_id, empresa_erp) o (None, None)

    Raises:
        ValueError: Si no hay empresa configurada
    """
    empresa_cli_id = get_empresa_cli_id()
    empresa_erp = get_empresa_erp()

    if not empresa_cli_id:
        raise ValueError("No se ha especificado empresa")

    if not empresa_erp:
        raise ValueError(f"Empresa {empresa_cli_id} no encontrada o sin empresa_erp configurado")

    return empresa_cli_id, empresa_erp


def get_db_connection():
    """
    Obtiene una conexión a la BD de la empresa actual.

    Returns:
        pyodbc.Connection

    Raises:
        ValueError: Si no hay empresa configurada
    """
    empresa_cli_id = get_empresa_cli_id()
    if not empresa_cli_id:
        raise ValueError("No se ha especificado empresa para la conexión")

    return Database.get_connection(empresa_cli_id)
