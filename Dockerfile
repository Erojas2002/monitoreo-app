# Dockerfile
FROM python:3.12-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Crear directorio para archivos estáticos
RUN mkdir -p /app/staticfiles

# Crear entrypoint.sh directamente con formato Unix
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'echo "Esperando a que la base de datos esté lista..."' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'until pg_isready -h db -U postgres -d monitoreo_db; do' >> /entrypoint.sh && \
    echo '    echo "PostgreSQL no está listo - esperando..."' >> /entrypoint.sh && \
    echo '    sleep 2' >> /entrypoint.sh && \
    echo 'done' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'echo "PostgreSQL está listo!"' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'echo "Ejecutando migraciones..."' >> /entrypoint.sh && \
    echo 'python manage.py migrate' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'echo "Recolectando archivos estáticos..."' >> /entrypoint.sh && \
    echo 'python manage.py collectstatic --noinput' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'echo "Ejecutando: $@"' >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Exponer puerto
EXPOSE 8000

# Usar entrypoint
ENTRYPOINT ["/entrypoint.sh"]