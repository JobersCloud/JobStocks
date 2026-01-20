#!/bin/bash
# ============================================================
# Script de despliegue para servidor Linux (51.68.44.136)
# Ejecutar desde el servidor después de subir archivos con scp
# ============================================================

# Mover archivos de config a la carpeta correcta (si están en /backend/)
if [ -f /opt/ApiRestExternos/backend/database.py ]; then
    mv /opt/ApiRestExternos/backend/database.py /opt/ApiRestExternos/backend/config/
fi

if [ -f /opt/ApiRestExternos/backend/database_central.py ]; then
    mv /opt/ApiRestExternos/backend/database_central.py /opt/ApiRestExternos/backend/config/
fi

# Ir al directorio del proyecto
cd /opt/ApiRestExternos

# Parar contenedores actuales
sudo docker-compose down

# Reconstruir y arrancar
sudo docker-compose up -d --build

# Esperar a que arranque
sleep 5

# Verificar versión
echo "Verificando API..."
curl -s http://localhost:5000/api/version

echo ""
echo "Despliegue completado!"
