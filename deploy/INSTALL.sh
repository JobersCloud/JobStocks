#!/bin/bash
# ============================================
# INSTALADOR AUTOMÁTICO - ApiRestExternos
# ============================================
# Ejecutar: sudo bash INSTALL.sh
# ============================================

set -e

APP_NAME="apirest"
APP_DIR="/opt/ApiRestExternos"
VENV_DIR="$APP_DIR/venv"
CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "============================================"
echo "  INSTALADOR ApiRestExternos"
echo "============================================"
echo ""

# Verificar root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Detectar OS
if [ -f /etc/debian_version ]; then
    OS="debian"
    PKG_MANAGER="apt-get"
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
    PKG_MANAGER="yum"
else
    echo "❌ Sistema operativo no soportado"
    exit 1
fi

echo "[1/8] Sistema detectado: $OS"

# Instalar dependencias base
echo "[2/8] Instalando dependencias del sistema..."
if [ "$OS" = "debian" ]; then
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv apache2 curl gnupg2 unixodbc-dev > /dev/null
else
    yum install -y python3 python3-pip httpd curl gnupg2 unixODBC-devel > /dev/null
fi

# Instalar ODBC Driver 18
echo "[3/8] Instalando Microsoft ODBC Driver 18..."
if ! odbcinst -q -d -n "ODBC Driver 18 for SQL Server" > /dev/null 2>&1; then
    if [ "$OS" = "debian" ]; then
        curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg 2>/dev/null

        # Detectar versión de Ubuntu/Debian
        if [ -f /etc/lsb-release ]; then
            VERSION=$(lsb_release -rs)
            curl -s https://packages.microsoft.com/config/ubuntu/$VERSION/prod.list > /etc/apt/sources.list.d/mssql-release.list
        else
            curl -s https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list
        fi

        apt-get update -qq
        ACCEPT_EULA=Y apt-get install -y -qq msodbcsql18 > /dev/null
    else
        curl -s https://packages.microsoft.com/config/rhel/8/prod.repo > /etc/yum.repos.d/mssql-release.repo
        ACCEPT_EULA=Y yum install -y msodbcsql18 > /dev/null
    fi
    echo "   ✓ ODBC Driver 18 instalado"
else
    echo "   ✓ ODBC Driver 18 ya instalado"
fi

# Copiar aplicación
echo "[4/8] Copiando aplicación a $APP_DIR..."
mkdir -p $APP_DIR
cp -r "$CURRENT_DIR"/* $APP_DIR/
rm -f $APP_DIR/INSTALL.sh  # No copiar el instalador

# Crear entorno virtual
echo "[5/8] Creando entorno virtual Python..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install --upgrade pip -q
pip install -r $APP_DIR/backend/requirements.txt -q
deactivate

# Configurar permisos
echo "[6/8] Configurando permisos..."
chown -R www-data:www-data $APP_DIR 2>/dev/null || chown -R apache:apache $APP_DIR
chmod -R 755 $APP_DIR

# Crear servicio systemd
echo "[7/8] Configurando servicio systemd..."
cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=ApiRestExternos Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn --workers 4 --threads 2 --bind 127.0.0.1:5000 --timeout 120 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Ajustar usuario para RedHat
if [ "$OS" = "redhat" ]; then
    sed -i 's/www-data/apache/g' /etc/systemd/system/$APP_NAME.service
fi

systemctl daemon-reload
systemctl enable $APP_NAME > /dev/null 2>&1
systemctl start $APP_NAME

# Configurar Apache
echo "[8/8] Configurando Apache..."
if [ "$OS" = "debian" ]; then
    a2enmod proxy proxy_http headers > /dev/null 2>&1

    cat > /etc/apache2/sites-available/$APP_NAME.conf << EOF
<VirtualHost *:80>
    ServerName localhost

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/

    ErrorLog \${APACHE_LOG_DIR}/$APP_NAME-error.log
    CustomLog \${APACHE_LOG_DIR}/$APP_NAME-access.log combined
</VirtualHost>
EOF

    a2ensite $APP_NAME > /dev/null 2>&1
    a2dissite 000-default > /dev/null 2>&1
    systemctl reload apache2
else
    cat > /etc/httpd/conf.d/$APP_NAME.conf << EOF
<VirtualHost *:80>
    ServerName localhost

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
</VirtualHost>
EOF

    systemctl restart httpd
fi

# Verificar instalación
sleep 3
echo ""
echo "============================================"
if curl -s http://127.0.0.1:5000/api/registro-habilitado > /dev/null 2>&1; then
    IP=$(hostname -I | awk '{print $1}')
    echo "  ✅ INSTALACIÓN COMPLETADA"
    echo "============================================"
    echo ""
    echo "  La aplicación está disponible en:"
    echo "    → http://$IP"
    echo "    → http://localhost"
    echo ""
    echo "  Comandos útiles:"
    echo "    Ver logs:    journalctl -u $APP_NAME -f"
    echo "    Reiniciar:   systemctl restart $APP_NAME"
    echo "    Estado:      systemctl status $APP_NAME"
    echo ""
else
    echo "  ⚠️  INSTALACIÓN CON ADVERTENCIAS"
    echo "============================================"
    echo ""
    echo "  El servicio puede tardar en iniciar."
    echo "  Verificar con: systemctl status $APP_NAME"
    echo ""
fi
