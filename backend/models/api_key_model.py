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
# ARCHIVO: models/api_key_model.py
# ============================================
import secrets
from config.database import Database

class ApiKeyModel:
    @staticmethod
    def generate_key():
        """Genera una API key única de 64 caracteres"""
        return secrets.token_hex(32)

    @staticmethod
    def create(user_id, nombre):
        """Crea una nueva API key para un usuario"""
        conn = Database.get_connection()
        cursor = conn.cursor()

        api_key = ApiKeyModel.generate_key()

        cursor.execute("""
            INSERT INTO api_keys (user_id, api_key, nombre)
            VALUES (?, ?, ?)
        """, (user_id, api_key, nombre))

        conn.commit()
        cursor.close()
        conn.close()

        return api_key

    @staticmethod
    def validate(api_key):
        """Valida una API key y retorna el usuario asociado"""
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ak.id, ak.user_id, ak.nombre, u.username, u.full_name, u.email
            FROM api_keys ak
            INNER JOIN users u ON ak.user_id = u.id
            WHERE ak.api_key = ? AND ak.activo = 1 AND u.active = 1
        """, (api_key,))

        row = cursor.fetchone()

        if row:
            # Actualizar fecha de último uso
            cursor.execute("""
                UPDATE api_keys SET fecha_ultimo_uso = GETDATE() WHERE api_key = ?
            """, (api_key,))
            conn.commit()

            result = {
                'api_key_id': row[0],
                'user_id': row[1],
                'key_nombre': row[2],
                'username': row[3],
                'full_name': row[4],
                'email': row[5]
            }
        else:
            result = None

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def get_by_user(user_id):
        """Obtiene todas las API keys de un usuario"""
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, api_key, nombre, activo, fecha_creacion, fecha_ultimo_uso
            FROM api_keys
            WHERE user_id = ?
            ORDER BY fecha_creacion DESC
        """, (user_id,))

        keys = []
        for row in cursor.fetchall():
            # Ocultar parte de la API key por seguridad
            api_key_masked = row[1][:8] + '...' + row[1][-8:]
            keys.append({
                'id': row[0],
                'api_key': api_key_masked,
                'nombre': row[2],
                'activo': row[3],
                'fecha_creacion': row[4].isoformat() if row[4] else None,
                'fecha_ultimo_uso': row[5].isoformat() if row[5] else None
            })

        cursor.close()
        conn.close()

        return keys

    @staticmethod
    def deactivate(api_key_id, user_id):
        """Desactiva una API key"""
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE api_keys SET activo = 0
            WHERE id = ? AND user_id = ?
        """, (api_key_id, user_id))

        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        return affected > 0

    @staticmethod
    def delete(api_key_id, user_id):
        """Elimina una API key"""
        conn = Database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM api_keys WHERE id = ? AND user_id = ?
        """, (api_key_id, user_id))

        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        return affected > 0
