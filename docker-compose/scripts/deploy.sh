#!/bin/bash

# ============================================================================
# SCRIPT DE DÉPLOIEMENT - Station Traffeyère IoT/AI Platform
# Déploiement modulaire par couches de microservices
# ============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$COMPOSE_DIR")"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
ENVIRONMENT=${ENVIRONMENT:-production}
LOG_FILE="${PROJECT_ROOT}/logs/deployment.log"

# Fonctions utilitaires
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    echo "[ERROR] $1" >> "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Vérifications préalables
check_prerequisites() {
    log "Vérification des prérequis..."
    
    # Docker et Docker Compose
    if ! command -v docker &> /dev/null; then
        error "Docker n'est pas installé"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose n'est pas installé"
    fi
    
    # Fichier .env
    if [[ ! -f "${COMPOSE_DIR}/.env" ]]; then
        warn "Fichier .env manquant. Copie de .env.example..."
        cp "${COMPOSE_DIR}/.env.example" "${COMPOSE_DIR}/.env"
        warn "ATTENTION: Configurez le fichier .env avant de continuer"
        exit 1
    fi
    
    # Répertoire logs
    mkdir -p "${PROJECT_ROOT}/logs"
    
    log "Prérequis vérifiés ✓"
}

# Création des réseaux
create_networks() {
    log "Création des réseaux Docker..."
    
    networks=(
        "traffeyere-backend"
        "traffeyere-frontend" 
        "traffeyere-iot"
        "traffeyere-monitoring"
        "traffeyere-security"
        "traffeyere-blockchain"
    )
    
    for network in "${networks[@]}"; do
        if ! docker network ls | grep -q "$network"; then
            docker network create "$network" --driver bridge
            log "Réseau $network créé"
        else
            info "Réseau $network existe déjà"
        fi
    done
}

# Déploiement par couches
deploy_infrastructure() {
    log "=== DÉPLOIEMENT INFRASTRUCTURE ==="
    cd "$COMPOSE_DIR"
    
    docker-compose -f docker-compose.infrastructure.yml pull
    docker-compose -f docker-compose.infrastructure.yml up -d
    
    # Attendre que les services soient prêts
    log "Attente de la disponibilité des services infrastructure..."
    sleep 30
    
    # Vérification santé PostgreSQL
    while ! docker exec traffeyere-postgres pg_isready -U postgres; do
        info "Attente PostgreSQL..."
        sleep 5
    done
    
    # Vérification Redis
    while ! docker exec traffeyere-redis redis-cli -a "$REDIS_PASSWORD" ping; do
        info "Attente Redis..."
        sleep 5
    done
    
    log "Infrastructure déployée ✓"
}

deploy_application() {
    log "=== DÉPLOIEMENT APPLICATION ==="
    cd "$COMPOSE_DIR"
    
    docker-compose -f docker-compose.application.yml build --no-cache
    docker-compose -f docker-compose.application.yml up -d
    
    # Attendre que le backend soit prêt
    log "Attente de la disponibilité du backend..."
    sleep 60
    
    while ! curl -f http://localhost:8000/health; do
        info "Attente backend API..."
        sleep 10
    done
    
    log "Application déployée ✓"
}

deploy_monitoring() {
    log "=== DÉPLOIEMENT MONITORING ==="
    cd "$COMPOSE_DIR"
    
    docker-compose -f docker-compose.monitoring.yml pull
    docker-compose -f docker-compose.monitoring.yml up -d
    
    # Attendre Prometheus
    sleep 45
    while ! curl -f http://localhost:9090/-/healthy; do
        info "Attente Prometheus..."
        sleep 10
    done
    
    # Attendre Grafana
    while ! curl -f http://localhost:3000/api/health; do
        info "Attente Grafana..."
        sleep 10
    done
    
    log "Monitoring déployé ✓"
}

deploy_iot() {
    log "=== DÉPLOIEMENT IOT ==="
    cd "$COMPOSE_DIR"
    
    docker-compose -f docker-compose.iot.yml build
    docker-compose -f docker-compose.iot.yml up -d
    
    sleep 30
    log "IoT Services déployés ✓"
}

deploy_security() {
    log "=== DÉPLOIEMENT SÉCURITÉ ==="
    cd "$COMPOSE_DIR"
    
    docker-compose -f docker-compose.security.yml pull
    docker-compose -f docker-compose.security.yml up -d
    
    # Attendre Elasticsearch (peut prendre du temps)
    log "Attente Elasticsearch (peut prendre 2-3 minutes)..."
    sleep 120
    
    while ! curl -u "elastic:$ELASTIC_PASSWORD" -f http://localhost:9200/_cluster/health; do
        info "Attente Elasticsearch..."
        sleep 15
    done
    
    log "Sécurité déployée ✓"
}

deploy_blockchain() {
    log "=== DÉPLOIEMENT BLOCKCHAIN ==="
    cd "$COMPOSE_DIR"
    
    docker-compose -f docker-compose.blockchain.yml pull
    docker-compose -f docker-compose.blockchain.yml up -d
    
    sleep 60
    log "Blockchain déployée ✓"
}

# Vérification de l'état final
check_deployment() {
    log "=== VÉRIFICATION DÉPLOIEMENT ==="
    
    # Services critiques
    services=(
        "traffeyere-postgres:5432"
        "traffeyere-redis:6379"
        "traffeyere-backend:8000"
        "traffeyere-prometheus:9090"
        "traffeyere-grafana:3000"
    )
    
    for service in "${services[@]}"; do
        container="${service%:*}"
        port="${service#*:}"
        
        if docker ps | grep -q "$container"; then
            log "✓ $container en cours d'exécution"
        else
            error "✗ $container non démarré"
        fi
    done
    
    # URLs de test
    log "URLs disponibles:"
    info "- Backend API: http://localhost:8000"
    info "- Frontend: http://localhost:3080"
    info "- Grafana: http://localhost:3000"
    info "- Prometheus: http://localhost:9090"
    info "- Edge AI: http://localhost:8001"
    info "- XAI Dashboard: http://localhost:8092"
    
    if [[ "$DEPLOY_SECURITY" == "true" ]]; then
        info "- Kibana SIEM: http://localhost:5601"
        info "- SOC Dashboard: http://localhost:3001"
    fi
    
    if [[ "$DEPLOY_BLOCKCHAIN" == "true" ]]; then
        info "- Blockchain API: http://localhost:8090"
    fi
}

# Affichage de l'aide
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --full              Déploiement complet (toutes les couches)
    --infrastructure    Déploiement infrastructure uniquement
    --application       Déploiement application uniquement  
    --monitoring        Déploiement monitoring uniquement
    --iot              Déploiement IoT uniquement
    --security         Déploiement sécurité uniquement
    --blockchain       Déploiement blockchain uniquement
    --minimal          Déploiement minimal (infrastructure + application)
    --check            Vérification de l'état sans déploiement
    --help             Afficher cette aide

Variables d'environnement:
    ENVIRONMENT        Environment (dev/staging/production)
    REDIS_PASSWORD     Mot de passe Redis
    ELASTIC_PASSWORD   Mot de passe Elasticsearch

Exemples:
    $0 --full                    # Déploiement complet
    $0 --minimal                 # Infrastructure + Application seulement
    $0 --infrastructure --monitoring  # Infrastructure et monitoring
    $0 --check                   # Vérification de l'état

EOF
}

# Gestion des arguments
DEPLOY_INFRASTRUCTURE=false
DEPLOY_APPLICATION=false
DEPLOY_MONITORING=false
DEPLOY_IOT=false
DEPLOY_SECURITY=false
DEPLOY_BLOCKCHAIN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            DEPLOY_INFRASTRUCTURE=true
            DEPLOY_APPLICATION=true
            DEPLOY_MONITORING=true
            DEPLOY_IOT=true
            DEPLOY_SECURITY=true
            DEPLOY_BLOCKCHAIN=true
            shift
            ;;
        --minimal)
            DEPLOY_INFRASTRUCTURE=true
            DEPLOY_APPLICATION=true
            shift
            ;;
        --infrastructure)
            DEPLOY_INFRASTRUCTURE=true
            shift
            ;;
        --application)
            DEPLOY_APPLICATION=true
            shift
            ;;
        --monitoring)
            DEPLOY_MONITORING=true
            shift
            ;;
        --iot)
            DEPLOY_IOT=true
            shift
            ;;
        --security)
            DEPLOY_SECURITY=true
            shift
            ;;
        --blockchain)
            DEPLOY_BLOCKCHAIN=true
            shift
            ;;
        --check)
            check_deployment
            exit 0
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            error "Option inconnue: $1. Utilisez --help pour l'aide."
            ;;
    esac
done

# Si aucune option, afficher l'aide
if [[ "$DEPLOY_INFRASTRUCTURE" == "false" && "$DEPLOY_APPLICATION" == "false" && "$DEPLOY_MONITORING" == "false" && "$DEPLOY_IOT" == "false" && "$DEPLOY_SECURITY" == "false" && "$DEPLOY_BLOCKCHAIN" == "false" ]]; then
    show_help
    exit 1
fi

# Exécution du déploiement
main() {
    log "=== DÉMARRAGE DÉPLOIEMENT STATION TRAFFEYÈRE ==="
    log "Environment: $ENVIRONMENT"
    
    check_prerequisites
    create_networks
    
    # Ordre de déploiement important
    if [[ "$DEPLOY_INFRASTRUCTURE" == "true" ]]; then
        deploy_infrastructure
    fi
    
    if [[ "$DEPLOY_APPLICATION" == "true" ]]; then
        deploy_application
    fi
    
    if [[ "$DEPLOY_MONITORING" == "true" ]]; then
        deploy_monitoring
    fi
    
    if [[ "$DEPLOY_IOT" == "true" ]]; then
        deploy_iot
    fi
    
    if [[ "$DEPLOY_SECURITY" == "true" ]]; then
        deploy_security
    fi
    
    if [[ "$DEPLOY_BLOCKCHAIN" == "true" ]]; then
        deploy_blockchain
    fi
    
    check_deployment
    log "=== DÉPLOIEMENT TERMINÉ AVEC SUCCÈS ==="
}

# Gestion des signaux pour nettoyage
trap 'error "Déploiement interrompu"' INT TERM

# Exécution
main