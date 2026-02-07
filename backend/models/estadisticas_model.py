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
# ARCHIVO: models/estadisticas_model.py
# Descripcion: Modelo para estadisticas del dashboard de administracion
# ============================================
from config.database import Database
from datetime import datetime, timedelta


class EstadisticasModel:
    @staticmethod
    def get_resumen(empresa_id='1'):
        """
        Obtiene un resumen general de estadisticas.

        Returns:
            dict: Resumen con totales
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        # Total propuestas
        cursor.execute("""
            SELECT COUNT(*) FROM propuestas WHERE empresa_id = ?
        """, (empresa_id,))
        total_propuestas = cursor.fetchone()[0]

        # Propuestas pendientes (estado = 'Enviada')
        cursor.execute("""
            SELECT COUNT(*) FROM propuestas WHERE empresa_id = ? AND estado = 'Enviada'
        """, (empresa_id,))
        propuestas_pendientes = cursor.fetchone()[0]

        # Total usuarios activos de esta empresa
        cursor.execute("""
            SELECT COUNT(*) FROM users WHERE empresa_id = ? AND active = 1
        """, (empresa_id,))
        usuarios_activos = cursor.fetchone()[0]

        # Total consultas pendientes
        cursor.execute("""
            SELECT COUNT(*) FROM consultas WHERE empresa_id = ? AND estado = 'pendiente'
        """, (empresa_id,))
        consultas_pendientes = cursor.fetchone()[0]

        # Total items solicitados (suma de cantidad_solicitada)
        cursor.execute("""
            SELECT ISNULL(SUM(pl.cantidad_solicitada), 0)
            FROM propuestas_lineas pl
            INNER JOIN propuestas p ON pl.propuesta_id = p.id
            WHERE p.empresa_id = ?
        """, (empresa_id,))
        total_items_solicitados = cursor.fetchone()[0]

        conn.close()

        return {
            'total_propuestas': total_propuestas,
            'propuestas_pendientes': propuestas_pendientes,
            'usuarios_activos': usuarios_activos,
            'consultas_pendientes': consultas_pendientes,
            'total_items_solicitados': float(total_items_solicitados) if total_items_solicitados else 0
        }

    @staticmethod
    def get_productos_mas_solicitados(empresa_id='1', limit=10):
        """
        Obtiene los productos mas solicitados.

        Args:
            empresa_id: ID de la empresa
            limit: Cantidad de productos a retornar

        Returns:
            list: Lista de productos con cantidad total solicitada
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP (?)
                pl.codigo,
                pl.descripcion,
                pl.formato,
                SUM(pl.cantidad_solicitada) as total_solicitado,
                COUNT(*) as veces_solicitado
            FROM propuestas_lineas pl
            INNER JOIN propuestas p ON pl.propuesta_id = p.id
            WHERE p.empresa_id = ?
            GROUP BY pl.codigo, pl.descripcion, pl.formato
            ORDER BY total_solicitado DESC
        """, (limit, empresa_id))

        productos = []
        for row in cursor.fetchall():
            productos.append({
                'codigo': row[0],
                'descripcion': row[1],
                'formato': row[2],
                'total_solicitado': float(row[3]) if row[3] else 0,
                'veces_solicitado': row[4]
            })

        conn.close()
        return productos

    @staticmethod
    def get_propuestas_por_periodo(empresa_id='1', dias=30):
        """
        Obtiene las propuestas agrupadas por dia.

        Args:
            empresa_id: ID de la empresa
            dias: Cantidad de dias hacia atras

        Returns:
            list: Lista de fechas con cantidad de propuestas
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        fecha_inicio = datetime.now() - timedelta(days=dias)

        cursor.execute("""
            SELECT
                CAST(fecha AS DATE) as dia,
                COUNT(*) as cantidad,
                SUM(total_items) as total_items
            FROM propuestas
            WHERE empresa_id = ? AND fecha >= ?
            GROUP BY CAST(fecha AS DATE)
            ORDER BY dia ASC
        """, (empresa_id, fecha_inicio))

        propuestas = []
        for row in cursor.fetchall():
            propuestas.append({
                'fecha': row[0].isoformat() if row[0] else None,
                'cantidad': row[1],
                'total_items': row[2]
            })

        conn.close()
        return propuestas

    @staticmethod
    def get_propuestas_por_estado(empresa_id='1'):
        """
        Obtiene el conteo de propuestas por estado.

        Args:
            empresa_id: ID de la empresa

        Returns:
            dict: Conteo por estado
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM propuestas
            WHERE empresa_id = ?
            GROUP BY estado
        """, (empresa_id,))

        estados = {}
        for row in cursor.fetchall():
            estados[row[0]] = row[1]

        conn.close()
        return estados

    @staticmethod
    def get_usuarios_mas_activos(empresa_id='1', limit=10):
        """
        Obtiene los usuarios con mas propuestas.

        Args:
            empresa_id: ID de la empresa
            limit: Cantidad de usuarios a retornar

        Returns:
            list: Lista de usuarios con cantidad de propuestas
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP (?)
                u.id,
                u.username,
                u.full_name,
                COUNT(p.id) as total_propuestas,
                MAX(p.fecha) as ultima_propuesta
            FROM users u
            INNER JOIN propuestas p ON u.id = p.user_id
            WHERE p.empresa_id = ?
            GROUP BY u.id, u.username, u.full_name
            ORDER BY total_propuestas DESC
        """, (limit, empresa_id))

        usuarios = []
        for row in cursor.fetchall():
            usuarios.append({
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'total_propuestas': row[3],
                'ultima_propuesta': row[4].isoformat() if row[4] else None
            })

        conn.close()
        return usuarios

    @staticmethod
    def get_propuestas_por_mes(empresa_id='1', meses=12):
        """
        Obtiene las propuestas agrupadas por mes.

        Args:
            empresa_id: ID de la empresa
            meses: Cantidad de meses hacia atras

        Returns:
            list: Lista de meses con cantidad de propuestas
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                YEAR(fecha) as anio,
                MONTH(fecha) as mes,
                COUNT(*) as cantidad,
                SUM(total_items) as total_items
            FROM propuestas
            WHERE empresa_id = ?
                AND fecha >= DATEADD(MONTH, -?, GETDATE())
            GROUP BY YEAR(fecha), MONTH(fecha)
            ORDER BY anio ASC, mes ASC
        """, (empresa_id, meses))

        propuestas = []
        for row in cursor.fetchall():
            propuestas.append({
                'anio': row[0],
                'mes': row[1],
                'cantidad': row[2],
                'total_items': row[3]
            })

        conn.close()
        return propuestas

    @staticmethod
    def get_articulos_mas_vistos(empresa_id='1', limit=10, dias=30):
        """
        Obtiene los articulos mas vistos (desde audit_log ARTICLE_VIEW).

        Args:
            empresa_id: ID de la empresa
            limit: Cantidad de articulos a retornar
            dias: Periodo en dias hacia atras

        Returns:
            list: Lista de articulos con cantidad de vistas
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP (?)
                a.recurso_id as codigo,
                COUNT(*) as vistas,
                COUNT(DISTINCT a.user_id) as usuarios_unicos,
                MAX(a.fecha) as ultima_vista,
                s.descripcion
            FROM audit_log a
            LEFT JOIN view_externos_stock s ON s.codigo = a.recurso_id AND s.empresa = ?
            WHERE a.accion = 'ARTICLE_VIEW'
                AND a.empresa_id = ?
                AND a.fecha >= DATEADD(DAY, ?, GETDATE())
            GROUP BY a.recurso_id, s.descripcion
            ORDER BY vistas DESC
        """, (limit, empresa_id, empresa_id, -dias))

        articulos = []
        for row in cursor.fetchall():
            articulos.append({
                'codigo': row[0],
                'vistas': row[1],
                'usuarios_unicos': row[2],
                'ultima_vista': row[3].isoformat() if row[3] else None,
                'descripcion': row[4] or row[0]
            })

        conn.close()
        return articulos

    @staticmethod
    def get_consultas_por_estado(empresa_id='1'):
        """
        Obtiene el conteo de consultas por estado.

        Args:
            empresa_id: ID de la empresa

        Returns:
            dict: Conteo por estado
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM consultas
            WHERE empresa_id = ?
            GROUP BY estado
        """, (empresa_id,))

        estados = {}
        for row in cursor.fetchall():
            estados[row[0]] = row[1]

        conn.close()
        return estados
