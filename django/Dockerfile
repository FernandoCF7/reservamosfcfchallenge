# Imagen base ligera
FROM python:3.10-slim

# Variables de entorno recomendadas
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Dependencias del sistema (necesarias para psycopg2 y compilación)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejor cache de Docker)
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear usuario no-root (seguridad)
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Exponer puerto
EXPOSE 8000

# Recolectar archivos estáticos (opcional pero recomendado)
RUN python manage.py collectstatic --noinput || true

# Usar Gunicorn en producción
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3"]