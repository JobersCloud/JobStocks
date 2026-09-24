#!/bin/bash
# ============================================================================
# renovar-cert.sh - Renovacion del certificado de stocks.undefasa.com
#
# Sustituye a la linea suelta de certbot que habia en el cron. Aquella
# renovaba, pero si fallaba no se enteraba nadie: el certificado caduco el
# 24/08/2026 y estuvo 23 dias caducado sin que saltara ningun aviso.
#
# Este script ademas comprueba como queda el certificado DESPUES de intentar
# la renovacion y deja constancia en dos sitios:
#   - /home/undefasa/nginx/cert-status.txt  (una linea, facil de mirar)
#   - syslog, con la etiqueta certbot-stocks (journalctl -t certbot-stocks)
# y devuelve codigo != 0 si algo no esta bien, para que el cron lo reporte.
# ============================================================================

LE=/home/undefasa/nginx/letsencrypt
CERT="$LE/live/stocks.undefasa.com/fullchain.pem"
ESTADO=/home/undefasa/nginx/cert-status.txt
AVISAR_DIAS=15

/usr/bin/certbot renew \
    --config-dir "$LE" \
    --work-dir /home/undefasa/nginx/work \
    --logs-dir /home/undefasa/nginx/logs \
    --deploy-hook "docker exec jobiadoc-nginx nginx -s reload" \
    -q
SALIDA=$?

if [ ! -f "$CERT" ]; then
    MSG="ERROR - no existe el certificado $CERT"
    echo "$(date '+%F %T') | $MSG" > "$ESTADO"
    logger -t certbot-stocks "$MSG"
    exit 2
fi

FIN=$(openssl x509 -in "$CERT" -noout -enddate 2>/dev/null | cut -d= -f2)
DIAS=$(( ( $(date -d "$FIN" +%s) - $(date +%s) ) / 86400 ))

if   [ "$DIAS" -lt 0 ];             then NIVEL=CADUCADO
elif [ "$DIAS" -lt "$AVISAR_DIAS" ]; then NIVEL=AVISO
else                                     NIVEL=OK
fi

MSG="$NIVEL - caduca en $DIAS dias ($FIN) - certbot salio con $SALIDA"
echo "$(date '+%F %T') | $MSG" > "$ESTADO"
logger -t certbot-stocks "$MSG"

# Si el certificado no esta sano, salir con error para que cron lo notifique
[ "$NIVEL" = "OK" ] || exit 1
exit 0
