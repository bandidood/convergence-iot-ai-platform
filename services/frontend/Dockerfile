# =============================================================================
# FRONTEND DOCKERFILE - Station Traffeyère IoT/AI Platform
# Multi-stage build: Node.js Builder + Nginx Runtime
# Optimisé pour Coolify & Production - RNCP 39394
# =============================================================================

# =============================================================================
# Stage 1: BUILD - Node.js avec cache optimisé
# =============================================================================
FROM node:18-alpine AS builder

# Metadata
LABEL org.opencontainers.image.title="Station Traffeyère Frontend"
LABEL org.opencontainers.image.description="React/Vite Frontend IoT Dashboard"
LABEL org.opencontainers.image.version="1.0.0"
LABEL maintainer="Johann Lebel <johann@johann-lebel.fr>"

# Variables d'environnement build
ENV NODE_ENV=production
ENV CI=true
ENV GENERATE_SOURCEMAP=false

# Optimisation couches Docker - Installation dépendances système
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# Répertoire de travail
WORKDIR /app

# Copie des fichiers de configuration npm (cache layer)
COPY package*.json ./
COPY yarn.lock* ./

# Installation dépendances avec cache npm
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production --ignore-scripts

# Copie du code source
COPY . .

# Variables d'environnement pour le build
ARG VITE_API_URL=https://backend-station.johann-lebel.fr
ARG VITE_WS_URL=wss://backend-station.johann-lebel.fr/ws
ARG VITE_GRAFANA_URL=https://grafana.johann-lebel.fr
ARG VITE_PROMETHEUS_URL=https://prometheus.johann-lebel.fr
ARG VITE_APP_VERSION=1.0.0

# Build de production avec Vite
RUN npm run build

# Optimisation taille - suppression fichiers dev
RUN rm -rf node_modules src public *.json *.config.* .git

# =============================================================================
# Stage 2: RUNTIME - Nginx Alpine production
# =============================================================================
FROM nginx:1.25-alpine AS production

# Security: utilisateur non-root
RUN addgroup -g 101 -S nginx && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# Installation outils production
RUN apk add --no-cache \
    curl \
    jq \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Configuration Nginx optimisée
COPY --from=builder /app/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html

# Fichier de health check
RUN echo '<!DOCTYPE html><html><body><h1>OK</h1></body></html>' > /usr/share/nginx/html/healthz

# Configuration SSL/TLS et sécurité
RUN mkdir -p /etc/nginx/ssl && \
    chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /etc/nginx/ssl && \
    chmod -R 755 /usr/share/nginx/html && \
    chmod 644 /usr/share/nginx/html/healthz

# Variables d'environnement runtime
ENV NGINX_WORKER_PROCESSES=auto
ENV NGINX_WORKER_CONNECTIONS=1024
ENV NGINX_KEEPALIVE_TIMEOUT=65
ENV NGINX_CLIENT_MAX_BODY_SIZE=10m

# Health check optimisé
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/healthz || exit 1

# Port exposition
EXPOSE 80

# Utilisateur non-root
USER nginx

# Signal handling pour arrêt gracieux
STOPSIGNAL SIGQUIT

# Commande par défaut
CMD ["nginx", "-g", "daemon off;"]