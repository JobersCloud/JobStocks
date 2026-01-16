#!/bin/bash
# ============================================
# Script de instalación en Linux (Ubuntu/Debian)
# Ejecutar como root: sudo bash install-linux.sh
# ============================================

set -e

echo "=========================================="
echo "Instalando ApiRestExternos en Linux"
echo "=========================================="

# Variables
APP_DIR="/opt/ApiRestExternos"
VENV_DIR="$APP_DIR/venv"

# 1. Instalar dependencias del sistema
echo "[1/7] Instalando dependencias del sistema..."
apt-get update
apt-get install -y python3 python3-pip python3-venv apache2 curl gnupg2

# 2. Instalar ODBC Driver 18 para SQL Server
echo "[2/7] Instalando ODBC Driver 18..."
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev

# 3. Crear entorno virtual Python
echo "[3/7] Creando entorno virtual..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/backend/requirements.txt

# 4. Configurar permisos
echo "[4/7] Configurando permisos..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

# 5. Instalar servicio systemd
echo "[5/7] Instalando servicio systemd..."
cp $APP_DIR/deploy/gunicorn.service /etc/systemd/system/apirest.service
systemctl daemon-reload
systemctl enable apirest
systemctl start apirest

# 6. Configurar Apache
echo "[6/7] Configurando Apache..."
a2enmod proxy proxy_http headers
cp $APP_DIR/deploy/apache-flask.conf /etc/apache2/sites-available/apirest.conf
a2ensite apirest
systemctl reload apache2

# 7. Verificar
echo "[7/7] Verificando instalación..."
sleep 3
if curl -s http://127.0.0.1:5000/api/registro-habilitado > /dev/null; then
    echo "=========================================="
    echo "✅ Instalación completada exitosamente!"
    echo "=========================================="
    echo "La aplicación está corriendo en:"
    echo "  - Local: http://127.0.0.1:5000"
    echo "  - Apache: http://tu-dominio.com"
    echo ""
    echo "Comandos útiles:"
    echo "  - Ver logs: journalctl -u apirest -f"
    echo "  - Reiniciar: systemctl restart apirest"
    echo "  - Estado: systemctl status apirest"
else
    echo "❌ Error: La aplicación no responde"
    echo "Revisar logs: journalctl -u apirest -f"
    exit 1
fi
