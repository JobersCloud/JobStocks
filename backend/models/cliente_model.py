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
# ARCHIVO: models/cliente_model.py
# ============================================
from config.database import Database


class ClienteModel:
    COLUMNS_FULL = 'empresa, codigo, razon, domicilio, codpos, poblacion, provincia, pais'
    COLUMNS_BASIC = 'empresa, codigo, razon'

    @staticmethod
    def _get_columns(cursor):
        """Detecta si la vista tiene columnas de dirección (script 32 ejecutado)."""
        try:
            cursor.execute("SELECT COL_LENGTH('view_externos_clientes', 'domicilio')")
            result = cursor.fetchone()
            return ClienteModel.COLUMNS_FULL if result and result[0] is not None else ClienteModel.COLUMNS_BASIC
        except Exception:
            return ClienteModel.COLUMNS_BASIC

    @staticmethod
    def _row_to_dict(row):
        return {
            'empresa': row[0],
            'codigo': row[1],
            'razon': row[2],
            'domicilio': row[3] if len(row) > 3 else None,
            'codpos': row[4] if len(row) > 4 else None,
            'poblacion': row[5] if len(row) > 5 else None,
            'provincia': row[6] if len(row) > 6 else None,
            'pais': row[7] if len(row) > 7 else None
        }

    @staticmethod
    def get_all(empresa_id=None):
        """
        Obtiene todos los clientes (con filtro opcional por empresa)

        Args:
            empresa_id: Filtrar por empresa (opcional)

        Returns:
            list: Lista de clientes
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = f"SELECT {ClienteModel._get_columns(cursor)} FROM view_externos_clientes"
        params = []

        if empresa_id:
            query += " WHERE empresa LIKE ?"
            params.append(f"%{empresa_id}%")

        query += " ORDER BY razon"

        cursor.execute(query, params)
        clientes = [ClienteModel._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        return clientes

    @staticmethod
    def get_by_codigo(codigo, empresa_id=None):
        """
        Obtiene un cliente por código

        Args:
            codigo: Código del cliente
            empresa_id: Filtrar por empresa (opcional)

        Returns:
            dict: Cliente o None si no existe
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = f"SELECT {ClienteModel._get_columns(cursor)} FROM view_externos_clientes WHERE codigo = ?"
        params = [codigo]

        if empresa_id:
            query += " AND empresa LIKE ?"
            params.append(f"%{empresa_id}%")

        cursor.execute(query, params)
        row = cursor.fetchone()
        cliente = ClienteModel._row_to_dict(row) if row else None
        conn.close()
        return cliente

    @staticmethod
    def search(filtros):
        """
        Busca clientes con filtros opcionales

        Args:
            filtros: Dict con filtros (empresa, razon)

        Returns:
            list: Lista de clientes filtrados
        """
        conn = Database.get_connection()
        cursor = conn.cursor()

        query = f"SELECT {ClienteModel._get_columns(cursor)} FROM view_externos_clientes WHERE 1=1"
        params = []

        if filtros.get('empresa'):
            query += " AND empresa LIKE ?"
            params.append(f"%{filtros['empresa']}%")

        if filtros.get('razon'):
            query += " AND razon LIKE ?"
            params.append(f"%{filtros['razon']}%")

        query += " ORDER BY razon"

        cursor.execute(query, params)
        clientes = [ClienteModel._row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        return clientes

    # Dominios de email genéricos que no sirven para matching
    DOMINIOS_GENERICOS = {
        'gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'yahoo.es',
        'live.com', 'msn.com', 'icloud.com', 'aol.com', 'protonmail.com',
        'mail.com', 'zoho.com', 'gmx.com', 'yandex.com',
        'hotmail.es', 'outlook.es', 'gmail.es', 'telefonica.net', 'terra.es',
        'ono.com', 'wanadoo.es', 'orange.es', 'movistar.es', 'vodafone.es'
    }

    @staticmethod
    def buscar_coincidencia(empresa_id, cif_nif=None, company_name=None, email=None, connection_id=None):
        """
        Intenta encontrar un cliente en genter que coincida con los datos del usuario.
        Prioridad: 1) CIF/NIF exacto, 2) dominio email, 3) nombre empresa.
        Solo retorna si hay exactamente 1 coincidencia.

        Returns: codigo del cliente o None
        """
        import unicodedata
        import re

        conn = Database.get_connection(connection_id)
        cursor = conn.cursor()

        try:
            # --- Prioridad 1: CIF/NIF exacto ---
            if cif_nif and cif_nif.strip():
                cif_normalizado = cif_nif.strip().upper()
                cursor.execute("""
                    SELECT RTRIM(codigo) FROM cristal.dbo.genter
                    WHERE tipoter = 'C' AND RTRIM(empresa) = ?
                    AND UPPER(RTRIM(cif)) = ?
                """, (empresa_id, cif_normalizado))
                rows = cursor.fetchall()
                if len(rows) == 1:
                    return rows[0][0].strip()

            # --- Prioridad 2: Dominio email ---
            if email and '@' in email:
                dominio = email.split('@')[1].strip().lower()
                if dominio not in ClienteModel.DOMINIOS_GENERICOS:
                    cursor.execute("""
                        SELECT RTRIM(codigo) FROM cristal.dbo.genter
                        WHERE tipoter = 'C' AND RTRIM(empresa) = ?
                        AND RTRIM(e_mail) LIKE ?
                    """, (empresa_id, f'%@{dominio}'))
                    rows = cursor.fetchall()
                    if len(rows) == 1:
                        return rows[0][0].strip()

            # --- Prioridad 3: Nombre de empresa ---
            if company_name and company_name.strip():
                # Normalizar: quitar acentos, mayúsculas, sufijos legales
                def normalizar(texto):
                    texto = texto.strip().upper()
                    # Quitar acentos
                    texto = ''.join(
                        c for c in unicodedata.normalize('NFD', texto)
                        if unicodedata.category(c) != 'Mn'
                    )
                    # Quitar sufijos legales comunes
                    texto = re.sub(r'\b(S\.?L\.?U?\.?|S\.?A\.?|S\.?C\.?|C\.?B\.?|S\.?COOP\.?)\b', '', texto)
                    texto = texto.strip().rstrip(',').strip()
                    return texto

                nombre_norm = normalizar(company_name)
                if len(nombre_norm) >= 3:
                    cursor.execute("""
                        SELECT RTRIM(codigo) FROM cristal.dbo.genter
                        WHERE tipoter = 'C' AND RTRIM(empresa) = ?
                        AND (UPPER(RTRIM(razon)) LIKE ? OR UPPER(RTRIM(nombre_comercial)) LIKE ?)
                    """, (empresa_id, f'%{nombre_norm}%', f'%{nombre_norm}%'))
                    rows = cursor.fetchall()
                    if len(rows) == 1:
                        return rows[0][0].strip()

            return None

        except Exception as e:
            print(f"⚠️ Error en buscar_coincidencia: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
