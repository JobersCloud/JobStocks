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
# ARCHIVO: controllers/cliente_controller.py
# ============================================
from flask import jsonify, request
from models.cliente_model import ClienteModel


class ClienteController:
    @staticmethod
    def get_all():
        """
        Obtener todos los clientes (con filtro opcional por empresa)
        """
        try:
            empresa_id = request.args.get('empresa')

            if empresa_id:
                clientes = ClienteModel.get_all(empresa_id=empresa_id)
            else:
                clientes = ClienteModel.get_all()

            return jsonify(clientes), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def get_by_codigo(codigo):
        """
        Obtener cliente por código (con filtro opcional por empresa)
        """
        try:
            empresa_id = request.args.get('empresa')

            if empresa_id:
                cliente = ClienteModel.get_by_codigo(codigo, empresa_id=empresa_id)
            else:
                cliente = ClienteModel.get_by_codigo(codigo)

            if cliente:
                return jsonify(cliente), 200
            else:
                return jsonify({"error": "Cliente no encontrado"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def search():
        """
        Buscar clientes con filtros
        """
        try:
            filtros = {
                'empresa': request.args.get('empresa'),
                'razon': request.args.get('razon')
            }

            # Eliminar filtros vacíos
            filtros = {k: v for k, v in filtros.items() if v is not None}

            clientes = ClienteModel.search(filtros)
            return jsonify(clientes), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
