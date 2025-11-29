# Dockerfile optimizado para DESARROLLO

FROM python:3.11-slim

# Establecer variables de entorno para desarrollo
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONFAULTHANDLER=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para desarrollo
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        gdb \
        curl \
        vim \
        git \
        procps \
        htop \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python incluyendo las de desarrollo
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        pytest \
        pytest-asyncio \
        pytest-cov \
        black \
        flake8 \
        mypy \
        ipython \
        ipdb

# Crear directorios necesarios para datos
RUN mkdir -p /app/data/raw \
    && mkdir -p /app/data/processed \
    && mkdir -p /app/logs

# Copiar código de la aplicación
COPY app/ ./app/
COPY scripts/build_vector_db.py .
COPY scripts/build_sqlite_db.py .
COPY scripts/ingest.py .

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la aplicación en modo desarrollo con hot-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

