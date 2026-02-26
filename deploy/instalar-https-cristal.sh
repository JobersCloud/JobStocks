#!/bin/bash
# ============================================================
# Script para configurar HTTPS en servidor CRISTAL
# Dominio: prolife-area.cristalceramicas.com
# Ejecutar como root o con sudo
# ============================================================

set -e

DOMINIO="prolife-area.cristalceramicas.com"
EMAIL="admin@cristalceramicas.com"  # Cambiar si es necesario

echo "========================================"
echo "  Configurando HTTPS para $DOMINIO"
echo "========================================"
echo ""

# 1. Instalar nginx y certbot
echo "[1/5] Instalando nginx y certbot..."
apt update
apt install -y nginx certbot python3-certbot-nginx

# 2. Detener nginx temporalmente
echo "[2/5] Deteniendo nginx..."
systemctl stop nginx || true

# 3. Obtener certificado Let's Encrypt (modo standalone)
echo "[3/5] Obteniendo certificado SSL..."
certbot certonly --standalone -d $DOMINIO --non-interactive --agree-tos --email $EMAIL

# 4. Copiar configuracion nginx
echo "[4/5] Configurando nginx..."
cp /var/jobstocks/deploy/nginx-cristal.conf /etc/nginx/sites-available/prolife-area
ln -sf /etc/nginx/sites-available/prolife-area /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Verificar configuracion
nginx -t

# 5. Iniciar nginx
echo "[5/5] Iniciando nginx..."
systemctl start nginx
systemctl enable nginx

# Configurar renovacion automatica (cron)
echo ""
echo "Configurando renovacion automatica del certificado..."
(crontab -l 2>/dev/null | grep -v certbot; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -

echo ""
echo "========================================"
echo "  HTTPS configurado correctamente!"
echo "========================================"
echo ""
echo "  URL: https://$DOMINIO"
echo ""
echo "  El certificado se renovara automaticamente."
echo "========================================"
