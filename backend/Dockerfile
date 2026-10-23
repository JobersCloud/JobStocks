# ============================================
# Dockerfile para backend Flask con SQL Server
# ApiRestExternos - Actualizado 2026-01-08
# ============================================
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Instalar dependencias del sistema para ODBC Driver 18
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    apt-transport-https \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get install -y unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configurar OpenSSL para permitir TLS legacy (necesario para SQL Server 2008)
RUN sed -i 's/openssl_conf = openssl_init/openssl_conf = openssl_init\n\n[openssl_init]\nssl_conf = ssl_sect\n\n[ssl_sect]\nsystem_default = system_default_sect\n\n[system_default_sect]\nMinProtocol = TLSv1\nCipherString = DEFAULT@SECLEVEL=0/' /etc/ssl/openssl.cnf || \
    echo -e "\n[openssl_init]\nssl_conf = ssl_sect\n\n[ssl_sect]\nsystem_default = system_default_sect\n\n[system_default_sect]\nMinProtocol = TLSv1\nCipherString = DEFAULT@SECLEVEL=0" >> /etc/ssl/openssl.cnf

# Crear usuario no-root para seguridad
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Directorio de trabajo
WORKDIR /app

# ============================================
# Aviso de seguridad (octubre 2026): pip y certifi
# ============================================
# El pip que trae la imagen base es el que se queda CAPTURADO en la imagen, asi
# que se actualiza ANTES de instalar nada: de ese modo las dependencias se
# resuelven ya con el pip corregido. La comprobacion posterior tumba el build si
# por cualquier via se cuela una version vulnerable, para que no haya que fiarse
# de revisarlo a mano despues.
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.2.2" \
    && python -c "import sys; from importlib.metadata import version; v=version('pip'); n=tuple(int(p) for p in v.split('.')[:3] if p.isdigit()); print('pip instalado:', v); sys.exit(0 if n>=(26,2,2) else 'ERROR: pip '+v+' es vulnerable, se requiere >=26.2.2')"

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -c "import sys; from importlib.metadata import version; v=version('certifi'); n=tuple(int(p) for p in v.split('.')[:3] if p.isdigit()); print('certifi instalado:', v); sys.exit(0 if n>=(2026,10,19) else 'ERROR: certifi '+v+' es vulnerable, se requiere >=2026.10.19')"

# Copiar codigo del backend
COPY . .

# Crear directorio para logs
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

# Cambiar a usuario no-root
USER appuser

# Puerto de la aplicacion
EXPOSE 5000

# Healthcheck (usa /api/version que no requiere connection)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/version || exit 1

# Comando para ejecutar la aplicacion (gunicorn para produccion)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "--max-requests", "1000", "--max-requests-jitter", "50", "app:app"]
