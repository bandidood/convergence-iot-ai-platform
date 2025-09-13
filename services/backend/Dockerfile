# =============================================================================
# BACKEND DOCKERFILE - Station Traffeyère IoT/AI Platform
# Multi-stage build: Python Builder + Runtime optimisé
# FastAPI + IoT + Edge AI + Monitoring - RNCP 39394
# =============================================================================

# =============================================================================
# Stage 1: BUILDER - Installation dépendances avec cache
# =============================================================================
FROM python:3.11-slim AS builder

# Metadata
LABEL org.opencontainers.image.title="Station Traffeyère Backend API"
LABEL org.opencontainers.image.description="FastAPI Backend IoT/AI Platform"
LABEL org.opencontainers.image.version="1.0.0"
LABEL maintainer="Johann Lebel <johann@johann-lebel.fr>"

# Variables d'environnement build
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation dépendances système pour compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Création environnement virtuel
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Mise à jour pip et outils
RUN pip install --no-cache-dir --upgrade \
    pip==24.2 \
    setuptools==72.1.0 \
    wheel==0.43.0

# Copie requirements et installation dépendances
WORKDIR /app
COPY requirements.txt .

# Installation dépendances Python avec cache pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: RUNTIME - Image production optimisée
# =============================================================================
FROM python:3.11-slim AS production

# Variables d'environnement production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONPATH=/app
ENV TZ=Europe/Paris

# Installation dépendances runtime uniquement
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    libpq5 \
    libffi8 \
    libssl3 \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Utilisateur non-root pour sécurité
RUN groupadd -r -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup -d /app -s /bin/bash appuser

# Copie environnement virtuel du builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Répertoire de travail avec permissions correctes
WORKDIR /app
RUN chown -R appuser:appgroup /app

# Copie du code source avec permissions
COPY --chown=appuser:appgroup . .

# Création dossiers nécessaires
RUN mkdir -p /app/logs /app/models /app/data /app/uploads && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Variables d'environnement application
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000
ENV UVICORN_WORKERS=4
ENV UVICORN_LOG_LEVEL=info
ENV UVICORN_RELOAD=false
ENV UVICORN_ACCESS_LOG=true

# Configuration FastAPI
ENV FASTAPI_ENV=production
ENV FASTAPI_DEBUG=false
ENV FASTAPI_TESTING=false

# Configuration base de données
ENV DATABASE_URL=postgresql://station_user:${POSTGRES_PASSWORD}@postgres:5432/station_traffeyere
ENV REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
ENV INFLUXDB_URL=http://influxdb:8086

# Configuration MinIO/S3
ENV MINIO_ENDPOINT=minio:9000
ENV AWS_ACCESS_KEY_ID=${MINIO_ROOT_USER}
ENV AWS_SECRET_ACCESS_KEY=${MINIO_ROOT_PASSWORD}

# Configuration monitoring
ENV PROMETHEUS_METRICS_ENABLED=true
ENV JAEGER_ENABLED=false
ENV LOG_JSON_FORMAT=true

# Health check optimisé
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget -qO- --spider http://localhost:8000/healthz || exit 1

# Port d'exposition
EXPOSE 8000

# Utilisateur non-root
USER appuser

# Signal handling pour arrêt gracieux
STOPSIGNAL SIGTERM

# Script de démarrage avec gestion gracieuse
COPY --chown=appuser:appgroup docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Point d'entrée
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Commande par défaut - production avec Gunicorn + Uvicorn
CMD ["gunicorn", "main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-tmp-dir", "/dev/shm", \
     "--worker-connections", "1024", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "120", \
     "--keepalive", "2", \
     "--preload", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]