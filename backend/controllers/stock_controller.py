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
from flask import jsonify, request
from models.stock_model import StockModel


class StockController:
    @staticmethod
    def get_all():
        """Obtener todos los stocks (filtrados por empresa de sesión)"""
        try:
            stocks = StockModel.get_all()
            return jsonify(stocks), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def get_by_codigo(codigo):
        """Obtener stock por código"""
        try:
            stock = StockModel.get_by_codigo(codigo)
            if stock:
                return jsonify(stock), 200
            else:
                return jsonify({"error": "Stock no encontrado"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def search():
        """Buscar stocks con filtros"""
        try:
            # Obtener parámetros de query string
            filtros = {
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

            stocks = StockModel.search(filtros)
            return jsonify(stocks), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def get_resumen():
        """Obtener resumen estadístico"""
        try:
            resumen = StockModel.get_resumen()
            return jsonify(resumen), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
