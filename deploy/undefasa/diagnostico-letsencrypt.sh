#!/bin/bash
# =============================================================================
#  DIAGNOSTICO DE LA RENOVACION DEL CERTIFICADO stocks.undefasa.com
# =============================================================================
#
#  QUE HACE ESTE SCRIPT
#  --------------------
#  1. Pone una captura de red escuchando el puerto 80 de este servidor.
#  2. Lanza una peticion real de validacion a Let's Encrypt.
#  3. Ensena que ha llegado (o no) al servidor durante esa validacion.
#
#  QUE NO HACE
#  -----------
#  No cambia ninguna configuracion, no reinicia servicios y no corta
#  el servicio. Solo escucha y pide el certificado, que es exactamente
#  lo que ya hace la tarea programada dos veces al dia.
#
#  COMO SE EJECUTA
#  ---------------
#      bash /home/undefasa/nginx/diagnostico-letsencrypt.sh
#
#  Hay que lanzarlo con el usuario 'undefasa', NO con root: si certbot
#  se ejecuta como root deja los ficheros con otro propietario y luego
#  la tarea programada deja de funcionar. Pedira la contrasena de sudo
#  una vez, que es para poder capturar el trafico de red.
#
#  QUE MIRAR MIENTRAS TANTO
#  ------------------------
#  El script imprime la hora exacta de inicio y fin. Con esa ventana,
#  buscar en el firewall conexiones ENTRANTES con destino el puerto 80
#  de este servidor (192.168.60.50) y origen cualquiera.
#
#  Importante: la conexion que interesa es la de ENTRADA. Let's Encrypt
#  tiene que venir el a leer un fichero nuestro. El trafico de SALIDA
#  hacia Let's Encrypt es otra conversacion distinta, y esa ya funciona.
# =============================================================================

set -u

LE=/home/undefasa/nginx/letsencrypt
CERT="$LE/live/stocks.undefasa.com/fullchain.pem"
CAPTURA=$(mktemp /tmp/captura-le.XXXXXX)
IFAZ=$(ip route | awk '/default/ {print $5; exit}')
IP=$(ip -4 -o addr show "$IFAZ" | awk '{print $4}' | cut -d/ -f1)

echo
echo "============================================================"
echo "  DIAGNOSTICO RENOVACION stocks.undefasa.com"
echo "============================================================"
echo "  Servidor  : $(hostname)  ($IP, interfaz $IFAZ)"
echo "  Certificado actual caduca: $(openssl x509 -in "$CERT" -noout -enddate 2>/dev/null | cut -d= -f2)"
echo "============================================================"
echo

echo ">> Se va a capturar el trafico entrante al puerto 80."
echo "   Hace falta sudo solo para eso."
sudo -v || { echo "ERROR: no se pudo obtener sudo"; exit 1; }
echo

INICIO=$(date '+%F %T %Z')
echo "############################################################"
echo "#  VENTANA DE LA PRUEBA - INICIO: $INICIO"
echo "############################################################"
echo

# Captura en segundo plano (120 s como maximo)
sudo timeout 120 tcpdump -i "$IFAZ" -nn tcp and dst port 80 > "$CAPTURA" 2>/dev/null &
PID_CAPTURA=$!
sleep 4

echo ">> Lanzando la validacion de Let's Encrypt..."
echo

certbot renew \
    --config-dir "$LE" \
    --work-dir /home/undefasa/nginx/work \
    --logs-dir /home/undefasa/nginx/logs \
    --no-random-sleep-on-renew \
    --deploy-hook "docker exec jobiadoc-nginx nginx -s reload" 2>&1 \
  | grep -E "Detail:|Congratulations|Successfully|new certificate|not yet due|Failed" \
  | sed 's/^/   /'

echo
echo ">> Esperando a que termine la captura..."
wait $PID_CAPTURA 2>/dev/null

FIN=$(date '+%F %T %Z')
echo
echo "############################################################"
echo "#  VENTANA DE LA PRUEBA - FIN: $FIN"
echo "############################################################"
echo

PAQUETES=$(grep -c . "$CAPTURA" 2>/dev/null || echo 0)

echo "=== TRAFICO QUE HA LLEGADO AL PUERTO 80 DE $IP ==="
if [ "$PAQUETES" -eq 0 ]; then
    echo "   (ninguno)"
else
    head -25 "$CAPTURA"
fi
echo
echo "   Total de paquetes: $PAQUETES"
echo

echo "============================================================"
echo "  CONCLUSION"
echo "============================================================"
if openssl x509 -in "$CERT" -noout -checkend 0 > /dev/null 2>&1; then
    echo "  El certificado esta VIGENTE. La renovacion ha funcionado."
elif [ "$PAQUETES" -eq 0 ]; then
    echo "  No ha llegado NI UN SOLO paquete al puerto 80 de este"
    echo "  servidor durante toda la validacion."
    echo
    echo "  Es decir: Let's Encrypt lo intenta, pero sus peticiones no"
    echo "  llegan hasta aqui. Se estan descartando antes."
    echo
    echo "  Que revisar, por orden:"
    echo "   1. A que IP apunta la redireccion (NAT) del puerto 80."
    echo "      Este servidor es ahora $IP. Si la regla sigue puesta"
    echo "      a 192.168.0.50, ahi esta el fallo."
    echo "   2. Si hay filtrado por pais. Let's Encrypt valida a la vez"
    echo "      desde varios puntos del mundo, tambien de fuera de"
    echo "      Europa, y si uno no llega falla la renovacion entera."
    echo "   3. Si la proteccion anti-flood o el IPS esta descartando"
    echo "      esas conexiones simultaneas de IPs desconocidas."
    echo
    echo "  Ojo: un descarte silencioso (drop) no aparece en el log"
    echo "  como denegacion. Que no haya denegaciones no significa que"
    echo "  el trafico se este entregando."
else
    echo "  Han llegado $PAQUETES paquetes al puerto 80, asi que el"
    echo "  trafico si entra. El fallo esta en otro sitio: revisar"
    echo "  arriba el mensaje de certbot."
fi
echo "============================================================"
echo
echo "  Ventana para buscar en el log del firewall:"
echo "    desde  $INICIO"
echo "    hasta  $FIN"
echo "  Buscar: conexiones ENTRANTES, destino $IP puerto 80."
echo "============================================================"
echo

rm -f "$CAPTURA"
