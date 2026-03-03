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
# Fecha : 2026-02-09
# ============================================================

"""
Motor de migraciones de base de datos reutilizable.

Módulo genérico que no sabe nada del proyecto.
Recibe una conexión pyodbc y una lista de migraciones,
detecta cuáles faltan y las aplica en orden.

Uso:
    from utils.db_migrator import run_pending
    from migrations import MIGRATIONS

    conn = get_my_connection()
    result = run_pending(conn, MIGRATIONS)
    conn.close()
"""

import re
import logging

logger = logging.getLogger(__name__)

# Caché en memoria: empresas ya verificadas en esta ejecución del servidor.
# Se resetea al reiniciar la app. Evita abrir conexión extra en cada login.
# Clave: identificador de empresa, Valor: número total de migraciones verificadas
_verified_companies = {}

# Regex para detectar sentencias DROP destructivas (prohibidas)
# DROP INDEX se permite porque solo elimina un índice de rendimiento, no datos
_DROP_PATTERN = re.compile(
    r'\bDROP\s+(TABLE|DATABASE|VIEW|PROCEDURE|FUNCTION|TRIGGER|SCHEMA)\b',
    re.IGNORECASE
)

# SQL para crear la tabla de control de migraciones (SQL Server)
_CREATE_TABLE_SQL = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'schema_migrations')
BEGIN
    CREATE TABLE schema_migrations (
        id INT IDENTITY(1,1) PRIMARY KEY,
        version INT NOT NULL UNIQUE,
        description VARCHAR(200) NOT NULL,
        app_version VARCHAR(20) NULL,
        applied_at DATETIME DEFAULT GETDATE()
    );
END
"""


def ensure_migrations_table(conn):
    """
    Crea la tabla schema_migrations si no existe.

    Args:
        conn: Conexión pyodbc activa
    """
    cursor = conn.cursor()
    try:
        cursor.execute(_CREATE_TABLE_SQL)
        conn.commit()
        logger.debug("Tabla schema_migrations verificada/creada")
    finally:
        cursor.close()


def get_applied_versions(conn):
    """
    Obtiene el conjunto de versiones ya aplicadas.

    Args:
        conn: Conexión pyodbc activa

    Returns:
        set[int]: Versiones aplicadas
    """
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cursor.fetchall()}
    finally:
        cursor.close()


def _validate_migration(migration):
    """
    Valida que una migración sea correcta y segura.

    Args:
        migration: dict con version, description, sql

    Raises:
        ValueError: Si la migración contiene DROP o tiene formato inválido
    """
    version = migration.get('version')
    if not isinstance(version, int) or version < 1:
        raise ValueError(f"Migración con version inválida: {version}")

    if not migration.get('description'):
        raise ValueError(f"Migración v{version} sin descripción")

    sql_list = migration.get('sql', [])
    if not sql_list:
        raise ValueError(f"Migración v{version} sin sentencias SQL")

    for i, sql in enumerate(sql_list):
        if _DROP_PATTERN.search(sql):
            raise ValueError(
                f"Migración v{version} contiene DROP (sentencia {i+1}). "
                f"Las migraciones destructivas no están permitidas."
            )


def run_pending(conn, migrations):
    """
    Ejecuta las migraciones pendientes en orden.

    Cada migración se ejecuta en su propia transacción.
    Si una falla, se hace rollback de ESA migración y se detiene.

    Args:
        conn: Conexión pyodbc activa (autocommit=False)
        migrations: Lista de dicts con: version, description, app_version, sql

    Returns:
        dict con:
            applied: list[int] - versiones aplicadas en esta ejecución
            already_applied: int - cantidad ya aplicadas previamente
            failed: dict|None - {version, error} si alguna falló
            total: int - total de migraciones definidas
    """
    # Asegurar que la tabla existe
    ensure_migrations_table(conn)

    # Obtener versiones ya aplicadas
    applied = get_applied_versions(conn)

    # Ordenar migraciones por versión
    sorted_migrations = sorted(migrations, key=lambda m: m['version'])

    # Validar TODAS las migraciones antes de ejecutar ninguna
    for m in sorted_migrations:
        _validate_migration(m)

    result = {
        'applied': [],
        'already_applied': len(applied),
        'failed': None,
        'total': len(sorted_migrations)
    }

    # Ejecutar solo las pendientes
    for migration in sorted_migrations:
        version = migration['version']

        if version in applied:
            continue

        description = migration['description']
        app_version = migration.get('app_version', '')

        logger.info(f"Aplicando migración v{version}: {description}")

        try:
            cursor = conn.cursor()

            # Ejecutar cada sentencia SQL de la migración
            for sql in migration['sql']:
                sql_stripped = sql.strip()
                if sql_stripped:
                    cursor.execute(sql_stripped)

            # Registrar la migración como aplicada
            cursor.execute(
                "INSERT INTO schema_migrations (version, description, app_version) "
                "VALUES (?, ?, ?)",
                version, description, app_version
            )

            conn.commit()
            cursor.close()

            result['applied'].append(version)
            logger.info(f"Migración v{version} aplicada correctamente")

        except Exception as e:
            # Rollback de esta migración
            try:
                conn.rollback()
            except Exception:
                pass

            # Detectar conflicto de UNIQUE (otro proceso aplicó la misma migración)
            error_str = str(e)
            if 'unique' in error_str.lower() or '2601' in error_str or '2627' in error_str:
                logger.info(
                    f"Migración v{version} ya aplicada por otro proceso (concurrencia)"
                )
                result['applied'].append(version)
                continue

            error_msg = f"Error en migración v{version} ({description}): {e}"
            logger.error(error_msg)

            result['failed'] = {
                'version': version,
                'description': description,
                'error': error_str
            }

            # Detener: no aplicar las siguientes
            break

    # Log resumen
    if result['applied']:
        logger.info(
            f"Migraciones completadas: {len(result['applied'])} aplicadas "
            f"({result['already_applied']} ya existían)"
        )
    elif not result['failed']:
        logger.debug("Sin migraciones pendientes")

    return result


def needs_check(company_id, migrations):
    """
    Verifica si una empresa necesita chequeo de migraciones.

    Devuelve False si ya fue verificada en esta ejecución del servidor
    Y el número total de migraciones no ha cambiado (no se añadieron nuevas).

    Args:
        company_id: Identificador de la empresa
        migrations: Lista de migraciones definidas

    Returns:
        bool: True si hay que abrir conexión y verificar
    """
    total = len(migrations)
    return _verified_companies.get(str(company_id)) != total


def mark_checked(company_id, migrations):
    """
    Marca una empresa como verificada (todas las migraciones al día).

    Args:
        company_id: Identificador de la empresa
        migrations: Lista de migraciones definidas
    """
    _verified_companies[str(company_id)] = len(migrations)


def get_status(conn, migrations):
    """
    Obtiene el estado actual de las migraciones.

    Args:
        conn: Conexión pyodbc activa
        migrations: Lista de dicts con las migraciones definidas

    Returns:
        dict con:
            applied: list[dict] - migraciones aplicadas con fecha
            pending: list[dict] - migraciones pendientes
            total: int
    """
    ensure_migrations_table(conn)

    # Obtener migraciones aplicadas con fechas
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT version, description, app_version, applied_at "
            "FROM schema_migrations ORDER BY version"
        )
        applied_rows = {
            row[0]: {
                'version': row[0],
                'description': row[1],
                'app_version': row[2],
                'applied_at': row[3].isoformat() if row[3] else None
            }
            for row in cursor.fetchall()
        }
    finally:
        cursor.close()

    applied = []
    pending = []

    for m in sorted(migrations, key=lambda x: x['version']):
        v = m['version']
        if v in applied_rows:
            applied.append(applied_rows[v])
        else:
            pending.append({
                'version': v,
                'description': m['description'],
                'app_version': m.get('app_version', '')
            })

    return {
        'applied': applied,
        'pending': pending,
        'total': len(migrations)
    }
