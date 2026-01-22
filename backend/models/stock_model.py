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

    # Columnas válidas para ordenación (seguridad contra SQL injection)
    VALID_ORDER_COLUMNS = ['codigo', 'descripcion', 'calidad', 'color', 'tono',
                           'calibre', 'formato', 'serie', 'existencias']

    # Columnas válidas para filtros (seguridad contra SQL injection)
    VALID_FILTER_COLUMNS = ['codigo', 'descripcion', 'calidad', 'color', 'tono',
                            'calibre', 'formato', 'serie', 'existencias']

    # Operadores válidos y su traducción SQL
    VALID_OPERATORS = {
        'eq': '=',           # Igual a
        'neq': '<>',         # Diferente de
        'contains': 'LIKE',  # Contiene
        'starts': 'LIKE',    # Empieza por
        'ends': 'LIKE',      # Termina en
        'gt': '>',           # Mayor que
        'gte': '>=',         # Mayor o igual
        'lt': '<',           # Menor que
        'lte': '<='          # Menor o igual
    }

    @staticmethod
    def _parse_filter_key(key):
        """
        Parsea una clave de filtro que puede tener formato columna__operador.
        Retorna tupla (columna, operador) o None si no es válido.
        """
        if '__' in key:
            parts = key.split('__', 1)
            if len(parts) == 2:
                columna, operador = parts
                if columna in StockModel.VALID_FILTER_COLUMNS and operador in StockModel.VALID_OPERATORS:
                    return (columna, operador)
        return None

    @staticmethod
    def _build_filter_condition(columna, operador, valor):
        """
        Construye la condición SQL y el parámetro para un filtro.
        Retorna tupla (condición_sql, valor_parametro).
        """
        sql_op = StockModel.VALID_OPERATORS.get(operador, '=')

        if operador == 'contains':
            return (f"{columna} LIKE ?", f"%{valor}%")
        elif operador == 'starts':
            return (f"{columna} LIKE ?", f"{valor}%")
        elif operador == 'ends':
            return (f"{columna} LIKE ?", f"%{valor}")
        else:
            # Operadores de comparación directa (eq, neq, gt, gte, lt, lte)
            return (f"{columna} {sql_op} ?", valor)

    @staticmethod
    def search(filtros, page=None, limit=None, order_by='codigo', order_dir='ASC'):
        """
        Busca stocks con filtros opcionales, paginación y ordenación.

        Args:
            filtros: dict con filtros de búsqueda
            page: número de página (1-based), None para sin paginación
            limit: registros por página, None para sin paginación
            order_by: columna para ordenar (default: codigo)
            order_dir: dirección de ordenación ASC o DESC (default: ASC)

        Returns:
            Si hay paginación: dict con 'data', 'total', 'page', 'limit', 'pages'
            Si no hay paginación: lista de stocks (comportamiento original)
        """
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        cursor = conn.cursor()

        # Validar columna de ordenación (prevenir SQL injection)
        if order_by not in StockModel.VALID_ORDER_COLUMNS:
            order_by = 'codigo'

        # Validar dirección de ordenación
        order_dir = 'DESC' if order_dir.upper() == 'DESC' else 'ASC'

        # Construir WHERE clause
        where_conditions = ["empresa = ?"]
        params = [empresa_erp]

        # Procesar filtros - soporta tanto formato simple como con operador
        for key, valor in filtros.items():
            if not valor:  # Ignorar valores vacíos
                continue

            # Intentar parsear como filtro con operador (columna__operador)
            parsed = StockModel._parse_filter_key(key)
            if parsed:
                columna, operador = parsed
                condition, param = StockModel._build_filter_condition(columna, operador, valor)
                where_conditions.append(condition)
                params.append(param)
            # Compatibilidad con filtros simples (sin operador)
            elif key in StockModel.VALID_FILTER_COLUMNS:
                # Por defecto usa LIKE %valor% para texto
                if key == 'existencias':
                    # Para existencias, usar >= si viene como filtro simple
                    where_conditions.append("existencias >= ?")
                    params.append(float(valor))
                else:
                    where_conditions.append(f"{key} LIKE ?")
                    params.append(f"%{valor}%")
            # Filtro especial existencias_min (compatibilidad)
            elif key == 'existencias_min':
                where_conditions.append("existencias >= ?")
                params.append(float(valor))

        where_clause = " AND ".join(where_conditions)

        # Si hay paginación, usar ROW_NUMBER() (compatible con SQL Server 2008)
        if page is not None and limit is not None:
            page = max(1, int(page))
            limit = max(1, min(500, int(limit)))  # Máximo 500 registros por página
            offset = (page - 1) * limit

            # Primero obtener el total de registros
            count_query = f"SELECT COUNT(*) FROM view_externos_stock WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # Query con paginación usando ROW_NUMBER()
            query = f"""
                SELECT * FROM (
                    SELECT
                        empresa, codigo, descripcion, calidad, color, tono, calibre,
                        formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet,
                        existencias, ean13, pesocaja, pesopallet,
                        ROW_NUMBER() OVER (ORDER BY {order_by} {order_dir}) AS row_num
                    FROM view_externos_stock
                    WHERE {where_clause}
                ) AS numbered
                WHERE row_num > ? AND row_num <= ?
            """
            params.extend([offset, offset + limit])
        else:
            # Sin paginación - comportamiento original con ordenación
            query = f"""
                SELECT empresa, codigo, descripcion, calidad, color, tono, calibre,
                       formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet,
                       existencias, ean13, pesocaja, pesopallet
                FROM view_externos_stock
                WHERE {where_clause}
                ORDER BY {order_by} {order_dir}
            """

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

        # Devolver con metadatos de paginación si aplica
        if page is not None and limit is not None:
            total_pages = (total + limit - 1) // limit  # Redondeo hacia arriba
            return {
                'data': stocks,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': total_pages
            }

        return stocks

    @staticmethod
    def get_valores_unicos(columna, limite=100):
        """
        Obtiene los valores únicos de una columna para filtros estilo Excel.

        Args:
            columna: nombre de la columna (debe estar en VALID_FILTER_COLUMNS)
            limite: máximo de valores a devolver (default 100)

        Returns:
            Lista de valores únicos ordenados
        """
        # Validar columna (seguridad contra SQL injection)
        if columna not in StockModel.VALID_FILTER_COLUMNS:
            return []

        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        cursor = conn.cursor()

        # Query para obtener valores únicos
        query = f"""
            SELECT DISTINCT TOP {min(limite, 500)} {columna}
            FROM view_externos_stock
            WHERE empresa = ? AND {columna} IS NOT NULL AND {columna} <> ''
            ORDER BY {columna}
        """
        cursor.execute(query, (empresa_erp,))

        valores = [row[0] for row in cursor.fetchall()]
        conn.close()

        return valores

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
