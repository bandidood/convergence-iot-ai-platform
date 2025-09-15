# =============================================================================
# DOCKERFILE EDGE AI ENGINE - RNCP 39394
# Expert en Systèmes d'Information et Sécurité
# 
# Support CUDA + Optimisations performance 
# Cible: latence <0.28ms, précision 97.6%
# =============================================================================

# Base image avec CUDA support
FROM nvidia/cuda:11.8-runtime-ubuntu20.04

# Métadonnées du projet RNCP 39394
LABEL maintainer="Johann Lebel - Expert SI & Sécurité"
LABEL project="RNCP-39394-IoT-AI-Platform" 
LABEL version="1.0.0"
LABEL description="Explainable Edge AI Engine with CUDA support"
LABEL security="ISA/IEC 62443 SL2+ compliant"

# Configuration non-interactive pour éviter les prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

# Configuration CUDA et optimisations
ENV CUDA_VISIBLE_DEVICES=0
ENV TF_ENABLE_ONEDNN_OPTS=1
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=1

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3-pip \
    build-essential \
    curl \
    git \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    pkg-config \
    libhdf5-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgtk2.0-dev \
    libcanberra-gtk-module \
    libxrandr2 \
    libasound2-dev \
    libpulse-dev \
    libjack-jackd2-dev \
    libasound2-plugins \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Création utilisateur non-privilégié (sécurité)
RUN groupadd -r aiengine && useradd -r -g aiengine -d /app -s /bin/bash -c "AI Engine User" aiengine

# Répertoire de travail
WORKDIR /app

# Copie des requirements et installation optimisée
COPY core/edge-ai-engine/requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt

# Installation TensorFlow avec GPU support
RUN pip3 install --no-cache-dir \
    tensorflow-gpu==2.13.0 \
    tensorrt \
    pycuda

# Installation outils performance et monitoring
RUN pip3 install --no-cache-dir \
    psutil \
    memory-profiler \
    py-spy \
    line-profiler \
    numba \
    prometheus-client

# Copie du code source
COPY core/edge-ai-engine/ .

# Compilation Numba pour optimisation JIT
RUN python3 -c "import numba; numba.jit(lambda x: x+1)(1)"

# Configuration sécurité - permissions restrictives
RUN chown -R aiengine:aiengine /app && \
    chmod -R 750 /app && \
    chmod +x /app/*.py

# Répertoires pour modèles et logs
RUN mkdir -p /app/models /app/logs /app/metrics && \
    chown -R aiengine:aiengine /app/models /app/logs /app/metrics

# Configuration monitoring Prometheus (optionnel)
# COPY monitoring/prometheus.yml /etc/prometheus/
EXPOSE 8080 9090

# Variables d'environnement sécurisées
ENV AI_MODEL_PATH=/app/models
ENV AI_LOG_LEVEL=INFO
ENV AI_METRICS_PORT=8080
ENV AI_PROMETHEUS_PORT=9090
ENV AI_MAX_WORKERS=4
ENV AI_BATCH_SIZE=32
ENV AI_CACHE_SIZE=1000

# Health check pour Kubernetes
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python3 -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Configuration utilisateur non-root
USER aiengine

# Port d'écoute API
EXPOSE 8080

# Script d'entrée avec gestion des signaux
COPY --chown=aiengine:aiengine core/edge-ai-engine/docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Point d'entrée principal
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python3", "explainable_ai_engine.py", "--serve", "--port=8080"]

# =============================================================================
# OPTIMISATIONS RUNTIME
# =============================================================================

# Configuration mémoire optimisée
ENV MALLOC_ARENA_MAX=2
ENV MALLOC_MMAP_THRESHOLD_=1048576
ENV MALLOC_TRIM_THRESHOLD_=1048576
ENV MALLOC_TOP_PAD_=1048576

# Configuration GPU memory growth (évite OOM)
ENV TF_FORCE_GPU_ALLOW_GROWTH=true
ENV TF_GPU_ALLOCATOR=cuda_malloc_async

# Optimisations CPU
ENV OMP_NUM_THREADS=4
ENV MKL_NUM_THREADS=4
ENV OPENBLAS_NUM_THREADS=4
ENV NUMBA_NUM_THREADS=4

# Cache optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# =============================================================================
# SÉCURITÉ RUNTIME
# =============================================================================

# Désactivation des fonctionnalités non nécessaires
ENV PYTHONSTARTUP=""
ENV PYTHONPATH="/app"

# Configuration logs sécurisés
VOLUME ["/app/logs", "/app/models", "/app/metrics"]

# Labels sécurité
LABEL security.scan="enabled"
LABEL security.vulnerability.check="true"
LABEL compliance.standard="ISA/IEC-62443-SL2+"
LABEL compliance.gdpr="true"
LABEL performance.target="latency<0.28ms"
LABEL performance.accuracy=">97.6%"
LABEL build.date="2024-08-17"
LABEL build.version="3.0.0-RNCP39394"
