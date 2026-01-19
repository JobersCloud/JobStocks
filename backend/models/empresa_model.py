# ============================================================
# ARCHIVO: models/empresa_model.py
# Modelo para consultar la vista view_externos_empresas
# ============================================================
from config.database import Database

class EmpresaModel:
    """Modelo para obtener datos de la empresa desde la BD del cliente"""

    @staticmethod
    def get_by_id(empresa_id, connection=None):
        """
        Obtiene los datos de una empresa desde view_externos_empresas
        
        Args:
            empresa_id: Código de la empresa (campo empresa_id en la vista)
            connection: ID de conexión para conectar a la BD correcta
        """
        conn = Database.get_connection(connection)
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            
            # 1. Intento exacto/limpio
            cursor.execute("""
                SELECT empresa, nombre 
                FROM view_externos_empresas 
                WHERE LTRIM(RTRIM(empresa)) = LTRIM(RTRIM(?))
            """, (str(empresa_id),))
            
            row = cursor.fetchone()
            
            if row:
                print(f"[DEBUG] Encontrado registro exacto/trim: {row[0]} - {row[1]}")
                return {'empresa_id': row[0], 'nombre': row[1]}
                
            # 2. Si falla, recuperar TODO para ver qué hay (solo dbg)
            print("[DEBUG] No encontrado exacto. Listando contenido de vista...")
            cursor.execute("SELECT empresa, nombre FROM view_externos_empresas")
            all_rows = cursor.fetchall()
            for r in all_rows:
                print(f"[DEBUG] VISTA ROW: ID='{r[0]}' Val='{r[1]}'")
                # Intento de match manual en python
                if str(r[0]).strip() == str(empresa_id).strip():
                     print(f"[DEBUG] Match encontrado en Python loop!")
                     return {'empresa_id': r[0], 'nombre': r[1]}
            
            return None
            
        except Exception as e:
            print(f"[ERROR] EmpresaModel.get_by_id: {e}")
            return None
        finally:
            if conn:
                conn.close()
