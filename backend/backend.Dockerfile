# Dockerfile optimized for DEVELOPMENT

FROM python:3.11-slim

# Set environment variables for development
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONFAULTHANDLER=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for development
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

# Create working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies including development dependencies
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

# Create necessary directories for data
RUN mkdir -p /app/data/raw \
    && mkdir -p /app/data/processed \
    && mkdir -p /app/logs

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY evaluation/ ./evaluation/
COPY tests/ ./tests/
COPY pytest.ini .
COPY run_tests.py .
COPY run_tests.sh .

# Expose port
EXPOSE 8000

# Command to run the application in development mode with hot-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

