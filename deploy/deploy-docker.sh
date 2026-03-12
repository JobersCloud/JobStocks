#!/bin/bash
# ============================================================
# Script de despliegue para servidor Linux
# Ejecutar desde el servidor despues de subir archivos con scp
# ============================================================

set -e

APP_DIR="/opt/ApiRestExternos"
DEPLOY_DIR="$APP_DIR/deploy"

echo "========================================="
echo "  Despliegue ApiRestExternos"
echo "========================================="

# Mover archivos de config a la carpeta correcta (si estan en /backend/)
if [ -f "$APP_DIR/backend/database.py" ]; then
    mv "$APP_DIR/backend/database.py" "$APP_DIR/backend/config/"
fi

if [ -f "$APP_DIR/backend/database_central.py" ]; then
    mv "$APP_DIR/backend/database_central.py" "$APP_DIR/backend/config/"
fi

# Ir al directorio del proyecto
cd "$APP_DIR"

# Asegurar que nginx sirve la pagina de mantenimiento
# (Copiar config actualizada si existe nginx instalado)
if command -v nginx &> /dev/null; then
    echo "[1/4] Verificando configuracion nginx..."
    # Recargar nginx para asegurar que error_page esta activo
    sudo nginx -t 2>/dev/null && sudo nginx -s reload 2>/dev/null || true
    echo "       Nginx listo - pagina de mantenimiento activa"
else
    echo "[1/4] Nginx no detectado, saltando..."
fi

# Parar contenedores actuales (los usuarios veran la pagina de mantenimiento)
echo "[2/4] Parando contenedores..."
sudo docker-compose down

echo "       Backend detenido - mostrando pagina de mantenimiento"

# Reconstruir y arrancar
echo "[3/4] Reconstruyendo y arrancando..."
sudo docker-compose up -d --build

# Esperar a que arranque
echo "[4/4] Esperando arranque del backend..."
MAX_RETRIES=15
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    RETRY=$((RETRY + 1))
    sleep 2
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/version 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo ""
        VERSION=$(curl -s http://localhost:5000/api/version 2>/dev/null)
        echo "========================================="
        echo "  Despliegue completado!"
        echo "  $VERSION"
        echo "========================================="
        exit 0
    fi
    printf "       Intento %d/%d (HTTP %s)...\r" "$RETRY" "$MAX_RETRIES" "$HTTP_CODE"
done

echo ""
echo "ADVERTENCIA: El backend no respondio tras $MAX_RETRIES intentos."
echo "Revisa los logs con: sudo docker logs apirest-backend -f"
exit 1
