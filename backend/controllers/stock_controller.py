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
# ARCHIVO: controllers/stock_controller.py
# ============================================
from flask import jsonify, request, session
from flask_login import current_user
from models.stock_model import StockModel
from models.precio_model import PrecioModel
from models.parametros_model import ParametrosModel


def _precios_habilitados():
    """Verifica si se deben mostrar precios (global + usuario)"""
    empresa_id = session.get('empresa_id', '1')
    if not ParametrosModel.mostrar_precios(empresa_id):
        return False
    return getattr(current_user, 'mostrar_precios', False)


class StockController:
    @staticmethod
    def get_all():
        """Obtener todos los stocks (filtrados por empresa de sesión)"""
        try:
            stocks = StockModel.get_all()
            # Inyectar precios si está habilitado (global + usuario)
            empresa_id = session.get('empresa_id', '1')
            if _precios_habilitados():
                PrecioModel.inyectar_precios(empresa_id, stocks)
            return jsonify(stocks), 200
        except Exception as e:
            # Incluir info de debug en el error
            db_config = session.get('db_config', {})
            server = db_config.get('dbserver', 'NO DEFINIDO')
            dbname = db_config.get('dbname', 'NO DEFINIDO')
            empresa_id = session.get('empresa_id', 'NO DEFINIDO')
            error_msg = f"{str(e)} [Server: {server}, DB: {dbname}, Empresa: {empresa_id}]"
            print(f"[ERROR] get_all: {error_msg}")
            return jsonify({"error": error_msg}), 500

    @staticmethod
    def get_by_codigo(codigo):
        """Obtener stock por código"""
        try:
            stock = StockModel.get_by_codigo(codigo)
            if stock:
                # Inyectar precio si está habilitado (global + usuario)
                empresa_id = session.get('empresa_id', '1')
                if _precios_habilitados():
                    PrecioModel.inyectar_precios(empresa_id, [stock])
                return jsonify(stock), 200
            else:
                return jsonify({"error": "Stock no encontrado"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def search():
        """Buscar stocks con filtros, paginación y ordenación"""
        try:
            # Obtener parámetros de filtros simples (compatibilidad)
            filtros = {
                'codigo': request.args.get('codigo'),
                'descripcion': request.args.get('descripcion'),
                'calidad': request.args.get('calidad'),
                'color': request.args.get('color'),
                'tono': request.args.get('tono'),
                'calibre': request.args.get('calibre'),
                'formato': request.args.get('formato'),
                'serie': request.args.get('serie'),
                'existencias_min': request.args.get('existencias_min')
            }

            # Eliminar filtros vacíos
            filtros = {k: v for k, v in filtros.items() if v is not None}

            # Capturar filtros con operadores (formato: columna__operador=valor)
            # Excluir parámetros de paginación/ordenación
            params_excluidos = {'page', 'limit', 'order_by', 'order_dir', 'empresa'}
            for key in request.args:
                if '__' in key and key not in params_excluidos:
                    # Es un filtro con operador (ej: codigo__contains=ABC)
                    filtros[key] = request.args.get(key)

            # Parámetros de paginación (opcionales)
            page = request.args.get('page', type=int)
            limit = request.args.get('limit', type=int)

            # Parámetros de ordenación
            order_by = request.args.get('order_by', 'codigo')
            order_dir = request.args.get('order_dir', 'ASC')

            # Llamar al modelo con paginación si se proporciona
            result = StockModel.search(filtros, page=page, limit=limit,
                                       order_by=order_by, order_dir=order_dir)
            # Inyectar precios si está habilitado (global + usuario)
            empresa_id = session.get('empresa_id', '1')
            if _precios_habilitados():
                stocks = result['data'] if isinstance(result, dict) else result
                PrecioModel.inyectar_precios(empresa_id, stocks)
            return jsonify(result), 200
        except Exception as e:
            # Incluir info de debug en el error
            db_config = session.get('db_config', {})
            server = db_config.get('dbserver', 'NO DEFINIDO')
            dbname = db_config.get('dbname', 'NO DEFINIDO')
            empresa_id = session.get('empresa_id', 'NO DEFINIDO')
            error_msg = f"{str(e)} [Server: {server}, DB: {dbname}, Empresa: {empresa_id}]"
            print(f"[ERROR] search: {error_msg}")
            return jsonify({"error": error_msg}), 500

    @staticmethod
    def get_resumen():
        """Obtener resumen estadístico"""
        try:
            resumen = StockModel.get_resumen()
            return jsonify(resumen), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def get_valores_unicos(columna):
        """Obtener valores únicos de una columna para filtros estilo Excel"""
        try:
            # Validar columna
            if columna not in StockModel.VALID_FILTER_COLUMNS:
                return jsonify({
                    'error': f'Columna no válida. Columnas permitidas: {", ".join(StockModel.VALID_FILTER_COLUMNS)}'
                }), 400

            limite = request.args.get('limite', 100, type=int)
            valores = StockModel.get_valores_unicos(columna, limite)

            return jsonify({
                'columna': columna,
                'valores': valores,
                'total': len(valores)
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
