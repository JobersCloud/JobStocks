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
# Fecha : 2026-02-08
# ============================================================

# ============================================
# ARCHIVO: routes/db_info_routes.py
# ============================================
from flask import Blueprint, jsonify, session
from flask_login import login_required
from utils.auth import administrador_required
from config.database import Database

db_info_bp = Blueprint('db_info', __name__)


@db_info_bp.route('/api/db-info', methods=['GET'])
@login_required
@administrador_required
def get_db_info():
    """
    Obtener información de la base de datos
    ---
    tags:
      - Sistema
    responses:
      200:
        description: Información de la BD
    """
    try:
        conn = Database.get_connection()
        cursor = conn.cursor()
        info = {}

        # Versión de SQL Server
        try:
            cursor.execute("SELECT @@VERSION")
            row = cursor.fetchone()
            if row:
                info['version'] = row[0]
        except Exception:
            info['version'] = None

        # Nombre de la BD
        try:
            cursor.execute("SELECT DB_NAME()")
            row = cursor.fetchone()
            if row:
                info['database_name'] = row[0]
        except Exception:
            info['database_name'] = None

        # Nombre del servidor
        try:
            cursor.execute("SELECT @@SERVERNAME")
            row = cursor.fetchone()
            if row:
                info['server_name'] = row[0]
        except Exception:
            info['server_name'] = None

        # Collation
        try:
            cursor.execute("SELECT DATABASEPROPERTYEX(DB_NAME(), 'Collation')")
            row = cursor.fetchone()
            if row:
                info['collation'] = row[0]
        except Exception:
            info['collation'] = None

        # Recovery model
        try:
            cursor.execute("SELECT DATABASEPROPERTYEX(DB_NAME(), 'Recovery')")
            row = cursor.fetchone()
            if row:
                info['recovery_model'] = row[0]
        except Exception:
            info['recovery_model'] = None

        # Tamaño de la BD con sp_spaceused
        try:
            cursor.execute("EXEC sp_spaceused")
            row = cursor.fetchone()
            if row:
                info['space'] = {
                    'database_size': row[1].strip() if row[1] else None,
                    'unallocated_space': row[2].strip() if row[2] else None
                }
            # Segundo resultado de sp_spaceused
            if cursor.nextset():
                row = cursor.fetchone()
                if row:
                    info['space']['reserved'] = row[0].strip() if row[0] else None
                    info['space']['data'] = row[1].strip() if row[1] else None
                    info['space']['index_size'] = row[2].strip() if row[2] else None
                    info['space']['unused'] = row[3].strip() if row[3] else None
        except Exception:
            info['space'] = None

        # Archivos de la BD
        try:
            cursor.execute("""
                SELECT
                    name,
                    type_desc,
                    physical_name,
                    size * 8 / 1024 AS size_mb,
                    CASE max_size
                        WHEN -1 THEN -1
                        WHEN 0 THEN 0
                        ELSE max_size * 8 / 1024
                    END AS max_size_mb,
                    growth,
                    is_percent_growth
                FROM sys.database_files
            """)
            files = []
            for row in cursor.fetchall():
                growth_str = f"{row[5]}%" if row[6] else f"{row[5] * 8 / 1024:.0f} MB"
                files.append({
                    'name': row[0],
                    'type': row[1],
                    'physical_name': row[2],
                    'size_mb': row[3],
                    'max_size_mb': row[4],
                    'growth': growth_str
                })
            info['files'] = files
        except Exception:
            info['files'] = []

        # Información del servidor (CPU, memoria)
        try:
            cursor.execute("""
                SELECT
                    cpu_count,
                    physical_memory_in_bytes / 1024 / 1024 AS physical_memory_mb,
                    sqlserver_start_time
                FROM sys.dm_os_sys_info
            """)
            row = cursor.fetchone()
            if row:
                info['server'] = {
                    'cpu_count': row[0],
                    'physical_memory_mb': row[1],
                    'start_time': str(row[2]) if row[2] else None
                }
        except Exception:
            # SQL Server 2008 puede no tener physical_memory_in_bytes
            try:
                cursor.execute("""
                    SELECT
                        cpu_count,
                        physical_memory_kb / 1024 AS physical_memory_mb,
                        sqlserver_start_time
                    FROM sys.dm_os_sys_info
                """)
                row = cursor.fetchone()
                if row:
                    info['server'] = {
                        'cpu_count': row[0],
                        'physical_memory_mb': row[1],
                        'start_time': str(row[2]) if row[2] else None
                    }
            except Exception:
                info['server'] = None

        # Número de tablas y vistas
        try:
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM sys.tables) AS table_count,
                    (SELECT COUNT(*) FROM sys.views) AS view_count
            """)
            row = cursor.fetchone()
            if row:
                info['objects'] = {
                    'tables': row[0],
                    'views': row[1]
                }
        except Exception:
            info['objects'] = None

        # Top 10 tablas más grandes
        try:
            cursor.execute("""
                SELECT TOP 10
                    t.name AS table_name,
                    SUM(p.rows) AS row_count,
                    SUM(a.total_pages) * 8 / 1024 AS total_size_mb
                FROM sys.tables t
                INNER JOIN sys.indexes i ON t.object_id = i.object_id
                INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE i.index_id <= 1
                GROUP BY t.name
                ORDER BY total_size_mb DESC
            """)
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    'name': row[0],
                    'rows': row[1],
                    'size_mb': row[2]
                })
            info['top_tables'] = tables
        except Exception:
            info['top_tables'] = []

        cursor.close()
        conn.close()

        return jsonify(info), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
