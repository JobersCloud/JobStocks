#!/bin/bash
# ============================================================
# Script para configurar HTTPS en servidor OVH para AZULFER
# Dominio: stocks.azulfer.com
# Ejecutar como root o con sudo
# ============================================================

set -e

DOMINIO="stocks.azulfer.com"
EMAIL="admin@azulfer.com"

echo "========================================"
echo "  Configurando HTTPS para $DOMINIO"
echo "========================================"
echo ""

# 1. Instalar certbot si no esta instalado
echo "[1/4] Verificando certbot..."
apt install -y certbot python3-certbot-nginx 2>/dev/null || true

# 2. Copiar configuracion nginx (solo HTTP)
echo "[2/4] Configurando nginx (HTTP)..."
cp /opt/ApiRestExternos/deploy/nginx-azulfer.conf /etc/nginx/sites-available/stocks-azulfer
ln -sf /etc/nginx/sites-available/stocks-azulfer /etc/nginx/sites-enabled/

# Verificar y recargar nginx
nginx -t
systemctl reload nginx

# 3. Obtener certificado y configurar SSL automaticamente
echo "[3/4] Obteniendo certificado SSL con certbot..."
certbot --nginx -d $DOMINIO --non-interactive --agree-tos --email $EMAIL --redirect

# 4. Verificar
echo "[4/4] Verificando..."
nginx -t
systemctl reload nginx

# Configurar renovacion automatica si no existe
if ! crontab -l 2>/dev/null | grep -q certbot; then
    echo "Configurando renovacion automatica..."
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
fi

echo ""
echo "========================================"
echo "  HTTPS configurado correctamente!"
echo "  URL: https://$DOMINIO"
echo "========================================"
