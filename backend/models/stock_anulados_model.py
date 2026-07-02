# ============================================
# ARCHIVO: models/stock_anulados_model.py
# Stocks anulados - misma lógica que stock_model.py
# pero contra view_externos_stock_anulados
# ============================================
from config.database import Database
from models.stock_model import _s, _row_to_stock

VIEW_NAME = 'view_externos_stock_anulados'

SELECT_COLS = """empresa, codigo, descripcion, calidad, color, tono, calibre,
                 formato, serie, unidad, pallet, caja, unidadescaja, cajaspallet,
                 existencias, ean13, pesocaja, pesopallet, tipo_producto, piezascaja"""


class StockAnuladosModel:
    VALID_ORDER_COLUMNS = ['codigo', 'descripcion', 'calidad', 'color', 'tono',
                           'calibre', 'formato', 'serie', 'existencias', 'tipo_producto']

    VALID_FILTER_COLUMNS = ['codigo', 'descripcion', 'calidad', 'color', 'tono',
                            'calibre', 'formato', 'serie', 'existencias', 'tipo_producto']

    VALID_OPERATORS = {
        'eq': '=', 'neq': '<>', 'contains': 'LIKE', 'not_contains': 'NOT LIKE',
        'starts': 'LIKE', 'not_starts': 'NOT LIKE', 'ends': 'LIKE', 'not_ends': 'NOT LIKE',
        'gt': '>', 'gte': '>=', 'lt': '<', 'lte': '<=',
        'between': 'BETWEEN', 'not_between': 'NOT BETWEEN'
    }

    @staticmethod
    def get_all():
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT {SELECT_COLS}
                FROM {VIEW_NAME}
                WHERE empresa = ?
            """, (empresa_erp,))
            return [_row_to_stock(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_by_codigo(codigo):
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT {SELECT_COLS}
                FROM {VIEW_NAME}
                WHERE codigo = ? AND empresa = ?
            """, (codigo, empresa_erp))
            row = cursor.fetchone()
            return _row_to_stock(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def _parse_filter_key(key):
        if '__' in key:
            parts = key.split('__', 1)
            if len(parts) == 2:
                columna, operador = parts
                if columna in StockAnuladosModel.VALID_FILTER_COLUMNS and operador in StockAnuladosModel.VALID_OPERATORS:
                    return (columna, operador)
        return None

    @staticmethod
    def _build_filter_condition(columna, operador, valor):
        sql_op = StockAnuladosModel.VALID_OPERATORS.get(operador, '=')
        if operador == 'contains':
            return (f"{columna} LIKE ?", f"%{valor}%")
        elif operador == 'not_contains':
            return (f"{columna} NOT LIKE ?", f"%{valor}%")
        elif operador == 'starts':
            return (f"{columna} LIKE ?", f"{valor}%")
        elif operador == 'not_starts':
            return (f"{columna} NOT LIKE ?", f"{valor}%")
        elif operador == 'ends':
            return (f"{columna} LIKE ?", f"%{valor}")
        elif operador == 'not_ends':
            return (f"{columna} NOT LIKE ?", f"%{valor}")
        elif operador in ('between', 'not_between'):
            partes = valor.split(',') if ',' in valor else [valor, valor]
            desde = partes[0] if partes[0] else None
            hasta = partes[1] if len(partes) > 1 and partes[1] else None
            if desde and hasta:
                if operador == 'between':
                    return (f"{columna} BETWEEN ? AND ?", [desde, hasta])
                else:
                    return (f"({columna} < ? OR {columna} > ?)", [desde, hasta])
            elif desde:
                op = '>=' if operador == 'between' else '<'
                return (f"{columna} {op} ?", desde)
            elif hasta:
                op = '<=' if operador == 'between' else '>'
                return (f"{columna} {op} ?", hasta)
            else:
                return (None, None)
        else:
            return (f"{columna} {sql_op} ?", valor)

    @staticmethod
    def search(filtros, page=None, limit=None, order_by='codigo', order_dir='ASC'):
        conn = Database.get_connection()
        empresa_erp = Database.get_empresa_erp()
        try:
            cursor = conn.cursor()

            if order_by not in StockAnuladosModel.VALID_ORDER_COLUMNS:
                order_by = 'codigo'
            order_dir = 'DESC' if order_dir.upper() == 'DESC' else 'ASC'

            where_conditions = ["empresa = ?"]
            params = [empresa_erp]

            for key, valor in filtros.items():
                if not valor:
                    continue

                parsed = StockAnuladosModel._parse_filter_key(key)
                if parsed:
                    columna, operador = parsed
                    condition, param = StockAnuladosModel._build_filter_condition(columna, operador, valor)
                    if condition:
                        where_conditions.append(condition)
                        if isinstance(param, list):
                            params.extend(param)
                        else:
                            params.append(param)
                elif key in StockAnuladosModel.VALID_FILTER_COLUMNS:
                    if key == 'existencias':
                        where_conditions.append("existencias >= ?")
                        params.append(float(valor))
                    elif key == 'descripcion':
                        palabras = [p.strip() for p in valor.split() if p.strip()]
                        for palabra in palabras:
                            where_conditions.append("(descripcion LIKE ? OR formato LIKE ?)")
                            params.append(f"%{palabra}%")
                            params.append(f"%{palabra}%")
                    else:
                        where_conditions.append(f"{key} LIKE ?")
                        params.append(f"%{valor}%")
                elif key == 'existencias_min':
                    where_conditions.append("existencias >= ?")
                    params.append(float(valor))

            where_clause = " AND ".join(where_conditions)

            if page is not None and limit is not None:
                page = max(1, int(page))
                limit = max(1, min(500, int(limit)))
                offset = (page - 1) * limit

                count_query = f"SELECT COUNT(*) FROM {VIEW_NAME} WHERE {where_clause}"
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]

                query = f"""
                    SELECT * FROM (
                        SELECT
                            {SELECT_COLS},
                            ROW_NUMBER() OVER (ORDER BY {order_by} {order_dir}) AS row_num
                        FROM {VIEW_NAME}
                        WHERE {where_clause}
                    ) AS numbered
                    WHERE row_num > ? AND row_num <= ?
                """
                params.extend([offset, offset + limit])
            else:
                query = f"""
                    SELECT {SELECT_COLS}
                    FROM {VIEW_NAME}
                    WHERE {where_clause}
                    ORDER BY {order_by} {order_dir}
                """

            cursor.execute(query, params)
            stocks = [_row_to_stock(row) for row in cursor.fetchall()]

            if page is not None and limit is not None:
                total_pages = (total + limit - 1) // limit
                return {
                    'data': stocks,
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': total_pages
                }
            return stocks
        finally:
            conn.close()
