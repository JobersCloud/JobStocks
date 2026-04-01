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
# Fecha : 2026-03-27
# ============================================================

# ============================================
# ARCHIVO: utils/backup_scheduler.py
# Scheduler de backups programados
# ============================================

import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class BackupScheduler:
    """Scheduler que comprueba periodicamente si hay backups programados pendientes"""

    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Arrancar el scheduler en un thread daemon"""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name='BackupScheduler')
        self._thread.start()
        logger.info("BackupScheduler iniciado")

    def stop(self):
        """Detener el scheduler"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("BackupScheduler detenido")

    def _run(self):
        """Loop principal: cada 60 segundos comprueba backups pendientes"""
        # Esperar 30 segundos al arrancar para que la app este lista
        self._stop_event.wait(30)

        while not self._stop_event.is_set():
            try:
                self._check_scheduled_backups()
            except Exception as e:
                logger.error(f"Error en BackupScheduler: {e}")

            # Esperar 60 segundos entre comprobaciones
            self._stop_event.wait(60)

    def _check_scheduled_backups(self):
        """Comprobar si hay backups programados que deban ejecutarse ahora"""
        from models.backup_model import BackupModel
        from utils.backup_executor import execute_backup, get_backup_status

        try:
            configs = BackupModel.get_scheduled_configs()
        except Exception as e:
            logger.error(f"Error obteniendo configs programadas: {e}")
            return

        now = datetime.now()

        for config in configs:
            try:
                if not self._should_run(config, now):
                    continue

                empresa_id = config['empresa_id']

                # No ejecutar si ya hay un backup en curso para esta empresa
                status = get_backup_status(empresa_id)
                if status.get('running'):
                    continue

                logger.info(f"Ejecutando backup programado: {config['nombre']} (empresa {empresa_id})")

                # Ejecutar en thread separado
                thread = threading.Thread(
                    target=execute_backup,
                    args=(config, empresa_id, None),
                    daemon=True,
                    name=f'Backup-{config["id"]}'
                )
                thread.start()

            except Exception as e:
                logger.error(f"Error procesando config {config.get('id')}: {e}")

    def _should_run(self, config, now):
        """Determinar si un backup programado debe ejecutarse ahora"""
        frecuencia = config.get('frecuencia', 'manual')
        hora = config.get('hora', 3)
        ultima = config.get('ultima_ejecucion')

        # Solo ejecutar en la hora programada (minuto 0)
        if now.hour != hora or now.minute > 1:
            return False

        if frecuencia == 'daily':
            # Si nunca se ha ejecutado, o fue hace mas de 23 horas
            if not ultima:
                return True
            diff = (now - ultima).total_seconds()
            return diff > 23 * 3600

        elif frecuencia == 'weekly':
            dia_semana = config.get('dia_semana', 1)  # 1=lunes
            # isoweekday(): 1=lunes, 7=domingo
            if now.isoweekday() != dia_semana:
                return False
            if not ultima:
                return True
            diff = (now - ultima).total_seconds()
            return diff > 6 * 24 * 3600

        elif frecuencia == 'monthly':
            dia_mes = config.get('dia_mes', 1)
            if now.day != dia_mes:
                return False
            if not ultima:
                return True
            diff = (now - ultima).total_seconds()
            return diff > 27 * 24 * 3600

        return False
