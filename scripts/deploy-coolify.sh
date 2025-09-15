#!/bin/bash
set -euo pipefail

# =============================================================================
# SCRIPT DE DÉPLOIEMENT COOLIFY - Station Traffeyère IoT/AI Platform
# Déploiement automatisé étape par étape via Coolify
# =============================================================================

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

# Variables de configuration
PROJECT_NAME="station-traffeyere-iot-ai-platform"
COOLIFY_API_URL="${COOLIFY_API_URL:-http://localhost:8000/api/v1}"
COOLIFY_TOKEN="${COOLIFY_TOKEN}"
DOMAIN_ROOT="${DOMAIN_ROOT:-traffeyere-station.fr}"

# Vérification des prérequis
check_prerequisites() {
    log_step "Vérification des prérequis..."
    
    # Vérifier Coolify Token
    if [ -z "${COOLIFY_TOKEN:-}" ]; then
        log_error "COOLIFY_TOKEN non défini. Exportez votre token Coolify."
        exit 1
    fi
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    # Vérifier curl
    if ! command -v curl &> /dev/null; then
        log_error "curl n'est pas installé"
        exit 1
    fi
    
    log_success "Prérequis validés"
}

# Génération des secrets sécurisés
generate_secrets() {
    log_step "Génération des secrets sécurisés..."
    
    export SECRET_KEY=$(openssl rand -hex 32)
    export JWT_SECRET=$(openssl rand -hex 32)
    export POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    export REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    export INFLUX_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    export INFLUX_ADMIN_TOKEN=$(openssl rand -hex 32)
    export MQTT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    export GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    export GRAFANA_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    log_success "Secrets générés avec succès"
}

# Création du fichier .env pour production
create_production_env() {
    log_step "Création du fichier .env pour production..."
    
    cat > .env << EOF
# Configuration production générée automatiquement
DOMAIN_ROOT=${DOMAIN_ROOT}
ACME_EMAIL=admin@${DOMAIN_ROOT}

# Secrets générés
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}

# Base de données
POSTGRES_DB=station_traffeyere
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
GRAFANA_DB_PASSWORD=${GRAFANA_DB_PASSWORD}

# InfluxDB
INFLUX_USERNAME=admin
INFLUX_PASSWORD=${INFLUX_PASSWORD}
INFLUX_ORG=traffeyere
INFLUX_BUCKET=iot_sensors
INFLUX_ADMIN_TOKEN=${INFLUX_ADMIN_TOKEN}

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}

# MQTT
MQTT_USERNAME=iot_user
MQTT_PASSWORD=${MQTT_PASSWORD}

# Grafana
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}

# Configuration métier
STATION_ID=TRAFFEYERE_001
STATION_NAME=Station Traffeyère
STATION_LOCATION=45.764043,4.835659

# API Keys (à configurer manuellement)
OPENAI_API_KEY=${OPENAI_API_KEY:-}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
GOOGLE_API_KEY=${GOOGLE_API_KEY:-}
PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY:-}

# Monitoring
SENTRY_DSN=${SENTRY_DSN:-}
EOF
    
    log_success "Fichier .env créé"
}

# API Coolify - Créer un nouveau projet
create_coolify_project() {
    log_step "Création du projet dans Coolify..."
    
    PROJECT_DATA='{
        "name": "'${PROJECT_NAME}'",
        "description": "Station Traffeyère IoT/AI Platform - Production Ready",
        "repository": {
            "url": "https://github.com/your-username/'${PROJECT_NAME}'.git",
            "branch": "main"
        },
        "environment": "production"
    }'
    
    RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "${PROJECT_DATA}" \
        "${COOLIFY_API_URL}/projects")
    
    PROJECT_ID=$(echo $RESPONSE | jq -r '.id')
    
    if [ "$PROJECT_ID" != "null" ]; then
        log_success "Projet créé avec ID: $PROJECT_ID"
        export COOLIFY_PROJECT_ID=$PROJECT_ID
    else
        log_error "Erreur création projet: $RESPONSE"
        exit 1
    fi
}

# Configuration des services dans Coolify
deploy_database_services() {
    log_step "Déploiement des services de base de données..."
    
    # PostgreSQL
    log_info "Déploiement PostgreSQL..."
    curl -s -X POST \
        -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "postgres-traffeyere",
            "image": "postgres:15-alpine",
            "environment": {
                "POSTGRES_DB": "station_traffeyere",
                "POSTGRES_USER": "postgres",
                "POSTGRES_PASSWORD": "'${POSTGRES_PASSWORD}'"
            },
            "volumes": [
                "postgres-data:/var/lib/postgresql/data"
            ],
            "networks": ["backend"]
        }' \
        "${COOLIFY_API_URL}/projects/${COOLIFY_PROJECT_ID}/services"
    
    # Redis
    log_info "Déploiement Redis..."
    curl -s -X POST \
        -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "redis-traffeyere",
            "image": "redis:7-alpine",
            "command": "redis-server --requirepass '${REDIS_PASSWORD}' --appendonly yes",
            "volumes": [
                "redis-data:/data"
            ],
            "networks": ["backend"]
        }' \
        "${COOLIFY_API_URL}/projects/${COOLIFY_PROJECT_ID}/services"
    
    # InfluxDB
    log_info "Déploiement InfluxDB..."
    curl -s -X POST \
        -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "influxdb-traffeyere",
            "image": "influxdb:2.7-alpine",
            "environment": {
                "DOCKER_INFLUXDB_INIT_MODE": "setup",
                "DOCKER_INFLUXDB_INIT_USERNAME": "admin",
                "DOCKER_INFLUXDB_INIT_PASSWORD": "'${INFLUX_PASSWORD}'",
                "DOCKER_INFLUXDB_INIT_ORG": "traffeyere",
                "DOCKER_INFLUXDB_INIT_BUCKET": "iot_sensors",
                "DOCKER_INFLUXDB_INIT_ADMIN_TOKEN": "'${INFLUX_ADMIN_TOKEN}'"
            },
            "volumes": [
                "influxdb-data:/var/lib/influxdb2"
            ],
            "domains": [
                "influx.'${DOMAIN_ROOT}'"
            ],
            "networks": ["backend"]
        }' \
        "${COOLIFY_API_URL}/projects/${COOLIFY_PROJECT_ID}/services"
    
    log_success "Services base de données déployés"
}

# Déploiement du backend
deploy_backend() {
    log_step "Déploiement du backend FastAPI..."
    
    curl -s -X POST \
        -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "backend-traffeyere",
            "build": {
                "context": "./services/backend",
                "dockerfile": "Dockerfile"
            },
            "environment": {
                "DATABASE_URL": "postgresql://postgres:'${POSTGRES_PASSWORD}'@postgres:5432/station_traffeyere",
                "REDIS_URL": "redis://redis:6379/0",
                "REDIS_PASSWORD": "'${REDIS_PASSWORD}'",
                "INFLUX_URL": "http://influxdb:8086",
                "INFLUX_TOKEN": "'${INFLUX_ADMIN_TOKEN}'",
                "INFLUX_ORG": "traffeyere",
                "INFLUX_BUCKET": "iot_sensors",
                "SECRET_KEY": "'${SECRET_KEY}'",
                "JWT_SECRET": "'${JWT_SECRET}'",
                "ENVIRONMENT": "production"
            },
            "domains": [
                "api.'${DOMAIN_ROOT}'",
                "ws.'${DOMAIN_ROOT}'"
            ],
            "healthcheck": {
                "test": "curl -f http://localhost:8000/health",
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            },
            "networks": ["backend", "iot-network"],
            "depends_on": ["postgres-traffeyere", "redis-traffeyere", "influxdb-traffeyere"]
        }' \
        "${COOLIFY_API_URL}/projects/${COOLIFY_PROJECT_ID}/services"
    
    log_success "Backend déployé"
}

# Déploiement du frontend
deploy_frontend() {
    log_step "Déploiement du frontend React..."
    
    curl -s -X POST \
        -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "frontend-traffeyere",
            "build": {
                "context": "./services/frontend",
                "dockerfile": "Dockerfile",
                "args": {
                    "NODE_ENV": "production",
                    "REACT_APP_API_URL": "https://api.'${DOMAIN_ROOT}'",
                    "REACT_APP_WS_URL": "wss://ws.'${DOMAIN_ROOT}'",
                    "REACT_APP_ENVIRONMENT": "production"
                }
            },
            "domains": [
                "'${DOMAIN_ROOT}'",
                "www.'${DOMAIN_ROOT}'"
            ],
            "networks": ["frontend"]
        }' \
        "${COOLIFY_API_URL}/projects/${COOLIFY_PROJECT_ID}/services"
    
    log_success "Frontend déployé"
}

# Déploiement du monitoring
deploy_monitoring() {
    log_step "Déploiement du stack monitoring..."
    
    # Prometheus
    log_info "Déploiement Prometheus..."
    curl -s -X POST \
        -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "prometheus-traffeyere",
            "image": "prom/prometheus:latest",
            "volumes": [
                "./monitoring/prometheus/prometheus.prod.yml:/etc/prometheus/prometheus.yml",
                "prometheus-data:/prometheus"
            ],
            "domains": [
                "metrics.'${DOMAIN_ROOT}'"
            ],
            "networks": ["monitoring", "backend"]
        }' \
        "${COOLIFY_API_URL}/projects/${COOLIFY_PROJECT_ID}/services"
    
    # Grafana
    log_info "Déploiement Grafana..."
    curl -s -X POST \
        -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "grafana-traffeyere",
            "image": "grafana/grafana:latest",
            "environment": {
                "GF_SECURITY_ADMIN_PASSWORD": "'${GRAFANA_ADMIN_PASSWORD}'",
                "GF_USERS_ALLOW_SIGN_UP": "false",
                "GF_SERVER_DOMAIN": "grafana.'${DOMAIN_ROOT}'",
                "GF_SERVER_ROOT_URL": "https://grafana.'${DOMAIN_ROOT}'"
            },
            "volumes": [
                "grafana-data:/var/lib/grafana"
            ],
            "domains": [
                "grafana.'${DOMAIN_ROOT}'"
            ],
            "networks": ["monitoring", "backend"]
        }' \
        "${COOLIFY_API_URL}/projects/${COOLIFY_PROJECT_ID}/services"
    
    log_success "Stack monitoring déployé"
}

# Vérification du déploiement
verify_deployment() {
    log_step "Vérification du déploiement..."
    
    # Attendre que les services démarrent
    log_info "Attente du démarrage des services (60s)..."
    sleep 60
    
    # Vérifier les endpoints
    ENDPOINTS=(
        "https://${DOMAIN_ROOT}"
        "https://api.${DOMAIN_ROOT}/health"
        "https://grafana.${DOMAIN_ROOT}"
        "https://influx.${DOMAIN_ROOT}"
    )
    
    for endpoint in "${ENDPOINTS[@]}"; do
        log_info "Vérification de $endpoint..."
        if curl -s -f "$endpoint" > /dev/null; then
            log_success "$endpoint - OK"
        else
            log_warning "$endpoint - En cours de démarrage..."
        fi
    done
}

# Affichage des informations de connexion
display_access_info() {
    log_step "Informations d'accès déploiement"
    
    echo ""
    echo "🎉 DÉPLOIEMENT TERMINÉ avec succès !"
    echo ""
    echo "📋 URLS D'ACCÈS :"
    echo "  🌐 Application principale : https://${DOMAIN_ROOT}"
    echo "  🚀 API Backend :           https://api.${DOMAIN_ROOT}"
    echo "  📊 Grafana Dashboard :     https://grafana.${DOMAIN_ROOT}"
    echo "  💾 InfluxDB Interface :    https://influx.${DOMAIN_ROOT}"
    echo "  📈 Métriques Prometheus :  https://metrics.${DOMAIN_ROOT}"
    echo ""
    echo "🔑 COMPTES ADMINISTRATEUR :"
    echo "  Grafana : admin / ${GRAFANA_ADMIN_PASSWORD}"
    echo "  InfluxDB : admin / ${INFLUX_PASSWORD}"
    echo ""
    echo "📝 FICHIER .env créé avec tous les secrets"
    echo "⚠️  IMPORTANT : Sauvegardez le fichier .env en sécurité !"
    echo ""
}

# Fonction principale
main() {
    echo ""
    log_info "🚀 Déploiement Station Traffeyère IoT/AI Platform via Coolify"
    echo ""
    
    check_prerequisites
    generate_secrets
    create_production_env
    create_coolify_project
    deploy_database_services
    deploy_backend
    deploy_frontend
    deploy_monitoring
    verify_deployment
    display_access_info
    
    log_success "🎯 Déploiement terminé avec succès !"
}

# Gestion des arguments
case "${1:-main}" in
    "check")
        check_prerequisites
        ;;
    "secrets")
        generate_secrets
        ;;
    "database")
        deploy_database_services
        ;;
    "backend")
        deploy_backend
        ;;
    "frontend")
        deploy_frontend
        ;;
    "monitoring")
        deploy_monitoring
        ;;
    "verify")
        verify_deployment
        ;;
    *)
        main
        ;;
esac