#!/bin/bash

# ============================================================================
# SCRIPT D'ARRÊT - Station Traffeyère IoT/AI Platform
# Arrêt sélectif des microservices par couches
# ============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Arrêt des services par couche
stop_blockchain() {
    log "=== ARRÊT BLOCKCHAIN ==="
    cd "$COMPOSE_DIR"
    
    if docker-compose -f docker-compose.blockchain.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.blockchain.yml down
        log "Blockchain arrêtée ✓"
    else
        info "Blockchain déjà arrêtée"
    fi
}

stop_security() {
    log "=== ARRÊT SÉCURITÉ ==="
    cd "$COMPOSE_DIR"
    
    if docker-compose -f docker-compose.security.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.security.yml down
        log "Sécurité arrêtée ✓"
    else
        info "Sécurité déjà arrêtée"
    fi
}

stop_iot() {
    log "=== ARRÊT IOT ==="
    cd "$COMPOSE_DIR"
    
    if docker-compose -f docker-compose.iot.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.iot.yml down
        log "IoT Services arrêtés ✓"
    else
        info "IoT Services déjà arrêtés"
    fi
}

stop_monitoring() {
    log "=== ARRÊT MONITORING ==="
    cd "$COMPOSE_DIR"
    
    if docker-compose -f docker-compose.monitoring.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.monitoring.yml down
        log "Monitoring arrêté ✓"
    else
        info "Monitoring déjà arrêté"
    fi
}

stop_application() {
    log "=== ARRÊT APPLICATION ==="
    cd "$COMPOSE_DIR"
    
    if docker-compose -f docker-compose.application.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.application.yml down
        log "Application arrêtée ✓"
    else
        info "Application déjà arrêtée"
    fi
}

stop_infrastructure() {
    log "=== ARRÊT INFRASTRUCTURE ==="
    cd "$COMPOSE_DIR"
    
    if docker-compose -f docker-compose.infrastructure.yml ps | grep -q "Up"; then
        warn "ATTENTION: L'arrêt de l'infrastructure supprimera l'accès aux données"
        read -p "Confirmer l'arrêt de l'infrastructure ? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose -f docker-compose.infrastructure.yml down
            log "Infrastructure arrêtée ✓"
        else
            info "Arrêt de l'infrastructure annulé"
        fi
    else
        info "Infrastructure déjà arrêtée"
    fi
}

# Nettoyage complet
cleanup_all() {
    log "=== NETTOYAGE COMPLET ==="
    cd "$COMPOSE_DIR"
    
    warn "ATTENTION: Cette opération supprimera tous les conteneurs et volumes"
    read -p "Confirmer le nettoyage complet ? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Arrêt de tous les services
        docker-compose -f docker-compose.blockchain.yml down -v 2>/dev/null || true
        docker-compose -f docker-compose.security.yml down -v 2>/dev/null || true
        docker-compose -f docker-compose.iot.yml down -v 2>/dev/null || true
        docker-compose -f docker-compose.monitoring.yml down -v 2>/dev/null || true
        docker-compose -f docker-compose.application.yml down -v 2>/dev/null || true
        docker-compose -f docker-compose.infrastructure.yml down -v 2>/dev/null || true
        
        # Suppression des réseaux
        networks=(
            "traffeyere-blockchain"
            "traffeyere-security"
            "traffeyere-monitoring"
            "traffeyere-iot"
            "traffeyere-frontend"
            "traffeyere-backend"
        )
        
        for network in "${networks[@]}"; do
            if docker network ls | grep -q "$network"; then
                docker network rm "$network" 2>/dev/null || true
                log "Réseau $network supprimé"
            fi
        done
        
        # Nettoyage des images non utilisées
        docker image prune -f
        
        log "Nettoyage complet terminé ✓"
    else
        info "Nettoyage annulé"
    fi
}

# Arrêt rapide (tout sauf infrastructure)
quick_stop() {
    log "=== ARRÊT RAPIDE (SANS INFRASTRUCTURE) ==="
    
    stop_blockchain
    stop_security
    stop_iot
    stop_monitoring
    stop_application
    
    log "Arrêt rapide terminé ✓"
    info "Infrastructure conservée pour préserver les données"
}

# Affichage du statut
show_status() {
    log "=== STATUT DES SERVICES ==="
    cd "$COMPOSE_DIR"
    
    echo
    info "📊 INFRASTRUCTURE:"
    docker-compose -f docker-compose.infrastructure.yml ps 2>/dev/null || echo "Aucun service infrastructure"
    
    echo
    info "🚀 APPLICATION:"
    docker-compose -f docker-compose.application.yml ps 2>/dev/null || echo "Aucun service application"
    
    echo
    info "📈 MONITORING:"
    docker-compose -f docker-compose.monitoring.yml ps 2>/dev/null || echo "Aucun service monitoring"
    
    echo
    info "🔌 IOT:"
    docker-compose -f docker-compose.iot.yml ps 2>/dev/null || echo "Aucun service IoT"
    
    echo
    info "🔒 SÉCURITÉ:"
    docker-compose -f docker-compose.security.yml ps 2>/dev/null || echo "Aucun service sécurité"
    
    echo
    info "🔗 BLOCKCHAIN:"
    docker-compose -f docker-compose.blockchain.yml ps 2>/dev/null || echo "Aucun service blockchain"
    
    echo
    info "📡 RÉSEAUX:"
    docker network ls | grep traffeyere || echo "Aucun réseau Traffeyère"
}

# Arrêt avec sauvegarde
stop_with_backup() {
    log "=== ARRÊT AVEC SAUVEGARDE ==="
    
    # Sauvegarde des données critiques
    BACKUP_DIR="${COMPOSE_DIR}/../backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    log "Sauvegarde en cours vers $BACKUP_DIR..."
    
    # Sauvegarde PostgreSQL
    if docker ps | grep -q traffeyere-postgres; then
        docker exec traffeyere-postgres pg_dumpall -U postgres > "$BACKUP_DIR/postgres_backup.sql"
        log "Sauvegarde PostgreSQL ✓"
    fi
    
    # Sauvegarde Redis
    if docker ps | grep -q traffeyere-redis; then
        docker exec traffeyere-redis redis-cli -a "$REDIS_PASSWORD" --rdb /tmp/dump.rdb 2>/dev/null || true
        docker cp traffeyere-redis:/tmp/dump.rdb "$BACKUP_DIR/redis_backup.rdb" 2>/dev/null || true
        log "Sauvegarde Redis ✓"
    fi
    
    # Copie des volumes importants
    if docker volume ls | grep -q prometheus_data; then
        docker run --rm -v prometheus_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/prometheus_data.tar.gz -C /data .
        log "Sauvegarde Prometheus ✓"
    fi
    
    # Arrêt normal
    quick_stop
    
    log "Sauvegarde terminée: $BACKUP_DIR"
}

# Redémarrage d'un service spécifique
restart_service() {
    local service=$1
    local compose_file=""
    
    case $service in
        postgres|redis|influxdb|minio|mosquitto)
            compose_file="docker-compose.infrastructure.yml"
            ;;
        backend|edge-ai-engine|frontend|xai-dashboard)
            compose_file="docker-compose.application.yml"
            ;;
        prometheus|grafana|alertmanager)
            compose_file="docker-compose.monitoring.yml"
            ;;
        iot-data-generator|secure-station-simulator)
            compose_file="docker-compose.iot.yml"
            ;;
        elasticsearch|kibana|soc-dashboard)
            compose_file="docker-compose.security.yml"
            ;;
        orderer*|peer*|blockchain-api-gateway)
            compose_file="docker-compose.blockchain.yml"
            ;;
        *)
            error "Service non reconnu: $service"
            ;;
    esac
    
    if [[ -n "$compose_file" ]]; then
        cd "$COMPOSE_DIR"
        log "Redémarrage de $service..."
        docker-compose -f "$compose_file" restart "$service"
        log "$service redémarré ✓"
    fi
}

# Affichage de l'aide
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --all               Arrêt complet (toutes les couches)
    --infrastructure    Arrêt infrastructure
    --application       Arrêt application
    --monitoring        Arrêt monitoring
    --iot              Arrêt IoT
    --security         Arrêt sécurité
    --blockchain       Arrêt blockchain
    --quick            Arrêt rapide (sans infrastructure)
    --cleanup          Nettoyage complet (supprime volumes)
    --backup           Arrêt avec sauvegarde des données
    --status           Affichage du statut
    --restart SERVICE   Redémarrage d'un service spécifique
    --help             Afficher cette aide

Exemples:
    $0 --quick                   # Arrêt rapide (garde l'infrastructure)
    $0 --application --iot       # Arrêt application et IoT seulement
    $0 --backup                  # Arrêt avec sauvegarde
    $0 --cleanup                 # Nettoyage complet
    $0 --restart backend         # Redémarrage du backend
    $0 --status                  # Affichage du statut

EOF
}

# Gestion des arguments
if [[ $# -eq 0 ]]; then
    show_help
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            stop_blockchain
            stop_security
            stop_iot
            stop_monitoring
            stop_application
            stop_infrastructure
            shift
            ;;
        --quick)
            quick_stop
            shift
            ;;
        --infrastructure)
            stop_infrastructure
            shift
            ;;
        --application)
            stop_application
            shift
            ;;
        --monitoring)
            stop_monitoring
            shift
            ;;
        --iot)
            stop_iot
            shift
            ;;
        --security)
            stop_security
            shift
            ;;
        --blockchain)
            stop_blockchain
            shift
            ;;
        --cleanup)
            cleanup_all
            shift
            ;;
        --backup)
            stop_with_backup
            shift
            ;;
        --status)
            show_status
            shift
            ;;
        --restart)
            shift
            if [[ $# -gt 0 ]]; then
                restart_service "$1"
                shift
            else
                error "Service manquant pour --restart"
            fi
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

log "Opération terminée"