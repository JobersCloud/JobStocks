# ============================================
# ARCHIVO: models/factura_pdf_model.py
# Modelo para gestionar PDFs de facturas almacenados en directorio local
# ============================================
import os
from config.database import Database
from models.parametros_model import ParametrosModel


class FacturaPdfModel:
    @staticmethod
    def _get_pdf_dir(empresa_id, connection=None):
        """Obtiene el directorio de PDFs configurado para la empresa"""
        return ParametrosModel.get('FACTURAS_PDF_DIRECTORIO', empresa_id, connection) or ''

    @staticmethod
    def get_pdfs(empresa, anyo, factura, connection_id=None):
        """Lista PDFs vinculados a una factura"""
        conn = Database.get_connection(connection_id)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, empresa, anyo, factura, filename, fecha_registro
                FROM factura_pdf
                WHERE empresa = ? AND anyo = ? AND factura = ?
                ORDER BY fecha_registro DESC
            """, (empresa, anyo, factura))
            return [{
                'id': row[0],
                'empresa': row[1].strip() if row[1] else '',
                'anyo': row[2],
                'factura': row[3],
                'filename': row[4],
                'fecha_registro': row[5].isoformat() if row[5] else None
            } for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def has_pdfs_batch(keys, connection_id=None):
        """
        Check masivo: dada una lista de (empresa, anyo, factura),
        retorna un set de las que tienen PDFs.
        """
        conn = Database.get_connection(connection_id)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT empresa, anyo, factura
                FROM factura_pdf
            """)
            existing = set()
            for row in cursor.fetchall():
                existing.add((row[0].strip() if row[0] else '', row[1], row[2]))
            return existing
        finally:
            conn.close()

    @staticmethod
    def scan_directory(empresa_id, connection_id=None):
        """Escanea el directorio de PDFs y retorna lista de archivos"""
        pdf_dir = FacturaPdfModel._get_pdf_dir(empresa_id)
        if not pdf_dir or not os.path.isdir(pdf_dir):
            return []

        files = []
        for f in sorted(os.listdir(pdf_dir)):
            if f.lower().endswith('.pdf'):
                full_path = os.path.join(pdf_dir, f)
                stat = os.stat(full_path)
                files.append({
                    'filename': f,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': os.path.getmtime(full_path)
                })
        return files

    @staticmethod
    def link_pdf(empresa, anyo, factura, filename, connection_id=None):
        """Vincula un PDF a una factura. Retorna el id del registro."""
        safe_name = os.path.basename(filename)
        if safe_name != filename:
            raise ValueError('Nombre de archivo no válido')

        conn = Database.get_connection(connection_id)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO factura_pdf (empresa, anyo, factura, filename)
                VALUES (?, ?, ?, ?)
            """, (empresa, anyo, factura, safe_name))
            conn.commit()
            cursor.execute("SELECT @@IDENTITY")
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    @staticmethod
    def unlink_pdf(pdf_id, connection_id=None):
        """Elimina la vinculación de un PDF"""
        conn = Database.get_connection(connection_id)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM factura_pdf WHERE id = ?", (pdf_id,))
            affected = cursor.rowcount
            conn.commit()
            return affected > 0
        finally:
            conn.close()

    @staticmethod
    def get_pdf_path(pdf_id, empresa_id, connection_id=None):
        """
        Obtiene la ruta completa de un PDF por su id.
        Valida que el archivo existe y no hay path traversal.
        """
        conn = Database.get_connection(connection_id)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT filename FROM factura_pdf WHERE id = ?
            """, (pdf_id,))
            row = cursor.fetchone()
            if not row:
                return None

            filename = row[0]
            pdf_dir = FacturaPdfModel._get_pdf_dir(empresa_id)
            if not pdf_dir:
                return None

            safe_name = os.path.basename(filename)
            full_path = os.path.join(pdf_dir, safe_name)

            real_path = os.path.realpath(full_path)
            real_dir = os.path.realpath(pdf_dir)
            if not real_path.startswith(real_dir):
                return None

            if not os.path.isfile(full_path):
                return None

            return full_path
        finally:
            conn.close()
