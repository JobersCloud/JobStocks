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
# Actualizado: 2026-01-16 - Conexión dinámica multi-empresa
# ============================================================

# ============================================
# ARCHIVO: models/stock_model.py
# ============================================
from config.database import Database


class StockModel:
    @staticmethod
    def get_all():
        """Obtiene todos los stocks de la empresa actual (de sesión)"""
        conn = Database.get_connection()  # Obtiene empresa_cli_id de sesión
        empresa_erp = Database.get_empresa_erp()  # Obtiene de sesión
        cursor = conn.cursor()
        cursor.execute("""
            SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                   formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet, existencias, ean13, pesocaja, pesopallet
            FROM view_externos_stock
            WHERE empresa = ?
        """, (empresa_erp,))

        stocks = []
        for row in cursor.fetchall():
            stocks.append({
                'empresa': row[0],
                'codigo': row[1],
                'descripcion': row[2],
                'calidad': row[3],
                'color': row[4],
                'tono': row[5],
                'calibre': row[6],
                'formato': row[7],
                'serie': row[8],
                'unidad': row[9],
                'pallet': row[10],
                'caja': row[11],
                'unidadescaja': float(row[12]) if row[12] else 0,
                'cajaspallet': float(row[13]) if row[13] else 0,
                'existencias': float(row[14]) if row[14] else 0.0,
                'ean13': row[15],
                'pesocaja': float(row[16]) if row[16] else 0,
                'pesopallet': float(row[17]) if row[17] else 0
            })

        conn.close()
        return stocks

    @staticmethod
    def get_by_codigo(codigo):
        """Obtiene un stock por código"""
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                   formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet, existencias, ean13, pesocaja, pesopallet
            FROM view_externos_stock
            WHERE codigo = ? AND empresa = ?
        """, (codigo, empresa_erp))
        row = cursor.fetchone()

        stock = None
        if row:
            stock = {
                'empresa': row[0],
                'codigo': row[1],
                'descripcion': row[2],
                'calidad': row[3],
                'color': row[4],
                'tono': row[5],
                'calibre': row[6],
                'formato': row[7],
                'serie': row[8],
                'unidad': row[9],
                'pallet': row[10],
                'caja': row[11],
                'unidadescaja': float(row[12]) if row[12] else 0,
                'cajaspallet': float(row[13]) if row[13] else 0,
                'existencias': float(row[14]) if row[14] else 0.0,
                'ean13': row[15],
                'pesocaja': float(row[16]) if row[16] else 0,
                'pesopallet': float(row[17]) if row[17] else 0
            }

        conn.close()
        return stock

    @staticmethod
    def get_by_codigo_and_empresa(codigo, empresa):
        """Obtiene un stock por código y empresa (compatibilidad)"""
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                   formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet, existencias, ean13, pesocaja, pesopallet
            FROM view_externos_stock
            WHERE codigo = ? AND empresa LIKE ?
        """, (codigo, f"%{empresa}%"))
        row = cursor.fetchone()

        stock = None
        if row:
            stock = {
                'empresa': row[0],
                'codigo': row[1],
                'descripcion': row[2],
                'calidad': row[3],
                'color': row[4],
                'tono': row[5],
                'calibre': row[6],
                'formato': row[7],
                'serie': row[8],
                'unidad': row[9],
                'pallet': row[10],
                'caja': row[11],
                'unidadescaja': float(row[12]) if row[12] else 0,
                'cajaspallet': float(row[13]) if row[13] else 0,
                'existencias': float(row[14]) if row[14] else 0.0,
                'ean13': row[15],
                'pesocaja': float(row[16]) if row[16] else 0,
                'pesopallet': float(row[17]) if row[17] else 0
            }

        conn.close()
        return stock

    @staticmethod
    def search(filtros):
        """Busca stocks con filtros opcionales"""
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        cursor = conn.cursor()

        # Construir query dinámica - siempre filtrar por empresa_erp
        query = """
            SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                   formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet, existencias, ean13, pesocaja, pesopallet
            FROM view_externos_stock
            WHERE empresa = ?
        """
        params = [empresa_erp]

        if filtros.get('descripcion'):
            query += " AND descripcion LIKE ?"
            params.append(f"%{filtros['descripcion']}%")

        if filtros.get('calidad'):
            query += " AND calidad = ?"
            params.append(filtros['calidad'])

        if filtros.get('color'):
            query += " AND color LIKE ?"
            params.append(f"%{filtros['color']}%")

        if filtros.get('tono'):
            query += " AND tono = ?"
            params.append(filtros['tono'])

        if filtros.get('calibre'):
            query += " AND calibre = ?"
            params.append(filtros['calibre'])

        if filtros.get('formato'):
            query += " AND formato = ?"
            params.append(filtros['formato'])

        if filtros.get('serie'):
            query += " AND serie = ?"
            params.append(filtros['serie'])

        if filtros.get('existencias_min'):
            query += " AND existencias >= ?"
            params.append(float(filtros['existencias_min']))

        cursor.execute(query, params)

        stocks = []
        for row in cursor.fetchall():
            stocks.append({
                'empresa': row[0],
                'codigo': row[1],
                'descripcion': row[2],
                'calidad': row[3],
                'color': row[4],
                'tono': row[5],
                'calibre': row[6],
                'formato': row[7],
                'serie': row[8],
                'unidad': row[9],
                'pallet': row[10],
                'caja': row[11],
                'unidadescaja': float(row[12]) if row[12] else 0,
                'cajaspallet': float(row[13]) if row[13] else 0,
                'existencias': float(row[14]) if row[14] else 0.0,
                'ean13': row[15],
                'pesocaja': float(row[16]) if row[16] else 0,
                'pesopallet': float(row[17]) if row[17] else 0
            })

        conn.close()
        return stocks

    @staticmethod
    def get_resumen():
        """Obtiene un resumen de estadísticas del stock"""
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_productos,
                SUM(existencias) as total_existencias,
                AVG(existencias) as promedio_existencias,
                MIN(existencias) as minimo_existencias,
                MAX(existencias) as maximo_existencias
            FROM view_externos_stock
            WHERE empresa = ?
        """, (empresa_erp,))
        row = cursor.fetchone()

        resumen = {
            'total_productos': row[0],
            'total_existencias': float(row[1]) if row[1] else 0.0,
            'promedio_existencias': float(row[2]) if row[2] else 0.0,
            'minimo_existencias': float(row[3]) if row[3] else 0.0,
            'maximo_existencias': float(row[4]) if row[4] else 0.0
        }

        conn.close()
        return resumen
