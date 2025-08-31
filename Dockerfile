# =============================================================================
# SECURE MULTI-STAGE DOCKERFILE - RNCP 39394 IoT/AI Platform
# Expert en Systèmes d'Information et Sécurité
# =============================================================================

# Build stage - Minimal Alpine Linux with Python 3.11
FROM python:3.11-alpine AS builder

# Build arguments for security
ARG BUILD_DATE
ARG VERSION=1.0.0
ARG VCS_REF

# Metadata following best practices
LABEL org.opencontainers.image.title="Station Traffeyère IoT/AI Platform"
LABEL org.opencontainers.image.description="Secure IoT/AI Edge Computing Platform - RNCP 39394"
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.source="https://github.com/bandidood/convergence-iot-ai-platform"
LABEL org.opencontainers.image.revision=$VCS_REF
LABEL security.compliance="ISA/IEC-62443-SL2+"
LABEL maintainer="Johann Lebel - Expert SI & Sécurité"

# Install build dependencies (removed after build)
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    linux-headers \
    postgresql-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

# Create virtual environment for better dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install security-focused packages
RUN pip install --no-cache-dir --upgrade \
    pip==24.2 \
    setuptools==72.1.0 \
    wheel==0.43.0

# Copy and install Python dependencies
COPY core/edge-ai-engine/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# =============================================================================
# Production stage - Distroless for minimal attack surface
# =============================================================================
FROM python:3.11-alpine AS production

# Security: Run as non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install only runtime dependencies
RUN apk add --no-cache \
    postgresql-libs \
    curl \
    ca-certificates \
    tzdata && \
    rm -rf /var/cache/apk/*

# Set secure working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=appuser:appgroup . .

# Create necessary directories
RUN mkdir -p /app/logs /app/models /app/metrics && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Security hardening
RUN chmod 700 /app/logs /app/models /app/metrics

# Environment variables for security
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV TZ=Europe/Paris

# Security: Disable unnecessary Python features
ENV PYTHONSTARTUP=""
ENV PYTHONHASHSEED=random

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8080

# Use exec form for proper signal handling
CMD ["python", "-m", "core.edge-ai-engine.explainable_ai_engine", "--serve", "--port=8080"]
