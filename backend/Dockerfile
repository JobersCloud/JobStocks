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

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo del backend
COPY . .

# Crear directorio para logs
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

# Cambiar a usuario no-root
USER appuser

# Puerto de la aplicacion
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/registro-habilitado || exit 1

# Comando para ejecutar la aplicacion (gunicorn para produccion)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "app:app"]
