#!/bin/bash
# ============================================================
# Publicacion con canary: probar la imagen nueva en un contenedor
# aparte ANTES de tocar el que esta sirviendo.
#
# Lo lanzan los publica_*.bat; no esta pensado para uso directo.
# Parametros, por variables de entorno:
#   APP_DIR      ruta del proyecto en el servidor      (obligatorio)
#   CONTAINER    nombre del contenedor del backend     (obligatorio)
#   APP_PORT     puerto donde sirve la app             (por defecto 5000)
#   CANARY_PORT  puerto libre para la prueba           (por defecto 15007)
#   SUDO_PASS    contrasena de sudo, si hace falta     (opcional)
#   USE_SUDO     1 para sudo sin contrasena            (opcional)
#   SOLO_CANARY  1 para quedarse en la prueba y NO cambiar el contenedor
# ============================================================

APP_DIR="${APP_DIR:?falta APP_DIR}"
CONTAINER="${CONTAINER:?falta CONTAINER}"
APP_PORT="${APP_PORT:-5000}"
CANARY_PORT="${CANARY_PORT:-15007}"
CANARY_NAME="${CONTAINER}-canary"

cd "$APP_DIR" || exit 1

# --- Como se llama a docker en este servidor ---
if [ -n "$SUDO_PASS" ]; then
    d() { echo "$SUDO_PASS" | sudo -S "$@" 2>/dev/null; }
elif [ "$USE_SUDO" = "1" ]; then
    d() { sudo "$@"; }
else
    d() { "$@"; }
fi

# --- Compose v2 o v1 ---
if d docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif d docker-compose version >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "!! No se encuentra docker compose ni docker-compose"
    exit 1
fi
dc() { d $COMPOSE "$@"; }
echo ">> Usando: $COMPOSE"

version_servida() {
    curl -sf --max-time 5 "http://127.0.0.1:${APP_PORT}/api/version" 2>/dev/null
}

# ============================================================
echo ""
echo "[1/4] Construyendo la imagen (la app sigue sirviendo)..."
if ! dc build; then
    echo ""
    echo "!! FALLO EL BUILD. No se ha tocado la aplicacion en uso."
    echo -n ">> Sigue sirviendo: "; version_servida || echo "(no responde, revisar)"
    exit 1
fi

# ============================================================
echo ""
echo "[2/4] Probando la imagen nueva en el puerto ${CANARY_PORT}..."

IMG=$(d docker inspect -f '{{.Config.Image}}' "$CONTAINER" 2>/dev/null | tr -d '\r')
if [ -z "$IMG" ]; then IMG=$(dc config --images 2>/dev/null | head -1 | tr -d '\r'); fi
if [ -z "$IMG" ]; then
    echo "!! No se ha podido determinar la imagen. No se toca nada."
    exit 1
fi
echo ">> Imagen: $IMG"

# El canary tiene que ser un clon fiel del contenedor en uso, o la prueba no
# vale: mismo entorno (las variables van en el compose o en el .env segun el
# servidor), misma red y mismos extra_hosts (host.docker.internal).
ENVFILE=$(mktemp)
d docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$CONTAINER" 2>/dev/null \
    | tr -d '\r' | grep -v '^$' > "$ENVFILE"

NET=$(d docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$CONTAINER" 2>/dev/null | tr -d '\r' | awk '{print $1}')
EXTRA=""
for h in $(d docker inspect -f '{{range .HostConfig.ExtraHosts}}{{println .}}{{end}}' "$CONTAINER" 2>/dev/null | tr -d '\r'); do
    [ -n "$h" ] && EXTRA="$EXTRA --add-host $h"
done
[ -n "$NET" ] && echo ">> Red: $NET"

d docker rm -f "$CANARY_NAME" >/dev/null 2>&1
# El puerto de dentro no se toca (manda el CMD de la imagen); solo se publica
# fuera en otro puerto, y solo en loopback.
d docker run -d --name "$CANARY_NAME" \
    --env-file "$ENVFILE" \
    ${NET:+--network "$NET"} \
    $EXTRA \
    -p "127.0.0.1:${CANARY_PORT}:${APP_PORT}" \
    "$IMG" >/dev/null 2>&1
RUN_RC=$?
rm -f "$ENVFILE"

if [ "$RUN_RC" != "0" ]; then
    echo "!! No se ha podido arrancar el contenedor de prueba. No se toca nada."
    d docker logs --tail 30 "$CANARY_NAME" 2>&1 | sed 's/^/     /'
    d docker rm -f "$CANARY_NAME" >/dev/null 2>&1
    exit 1
fi

CANARY_OK=0
for i in $(seq 1 30); do
    sleep 1
    VER=$(curl -sf --max-time 3 "http://127.0.0.1:${CANARY_PORT}/api/version" 2>/dev/null)
    if [ -n "$VER" ]; then
        echo ">> La imagen nueva arranca y responde: $VER"
        CANARY_OK=1
        break
    fi
    if [ -z "$(d docker ps -q -f name="^${CANARY_NAME}$")" ]; then break; fi
done

if [ "$CANARY_OK" != "1" ]; then
    echo ""
    echo "!! LA IMAGEN NUEVA NO ARRANCA. No se ha tocado la aplicacion en uso."
    echo "!! Ultimas lineas del error:"
    d docker logs --tail 30 "$CANARY_NAME" 2>&1 | sed 's/^/     /'
    d docker rm -f "$CANARY_NAME" >/dev/null 2>&1
    echo ""
    echo -n ">> Sigue sirviendo la version anterior: "
    version_servida || echo "(no responde, revisar)"
    exit 1
fi

d docker rm -f "$CANARY_NAME" >/dev/null 2>&1

if [ "$SOLO_CANARY" = "1" ]; then
    echo ""
    echo ">> MODO PRUEBA: la imagen nueva arranca, pero NO se cambia el"
    echo ">> contenedor en uso. Sigue sirviendo: $(version_servida)"
    exit 0
fi

# ============================================================
echo ""
echo "[3/4] Cambiando al contenedor nuevo (imagen ya probada)..."
INICIO=$(date +%s)
# Recrear solo lo que cambia: redis y la red se quedan como estan. Si el
# compose es viejo y no sabe recrear en sitio (KeyError: ContainerConfig),
# se cae al down + up de siempre.
# Ojo: con tuberia el $? seria el del sed, no el del compose.
OUT=$(dc up -d --no-deps 2>&1); RC=$?
echo "$OUT" | sed 's/^/     /'
if [ "$RC" != "0" ]; then
    echo ">> El 'up' no ha podido recrear en sitio; probando con down + up..."
    dc down 2>&1 | sed 's/^/     /'
    dc up -d 2>&1 | sed 's/^/     /'
fi

for i in $(seq 1 40); do
    VER=$(version_servida)
    [ -n "$VER" ] && break
    sleep 1
done
FIN=$(date +%s)

# ============================================================
echo ""
echo "[4/4] Comprobando el resultado..."
d docker ps --format '     {{.Names}} :: {{.Status}}'
echo -n ">> Version sirviendo: "
version_servida || echo "NO RESPONDE"
echo ""
echo ">> Corte: $((FIN-INICIO)) segundos"

d docker image prune -f >/dev/null 2>&1

if [ -z "$(version_servida)" ]; then
    echo "!! La aplicacion no responde despues del cambio. Revisar:"
    d docker logs --tail 40 "$CONTAINER" 2>&1 | sed 's/^/     /'
    exit 1
fi
exit 0
