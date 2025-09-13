#!/bin/bash
# =============================================================================
# Script de déploiement local - Station Traffeyère IoT/AI Platform
# Test et développement avant déploiement Coolify
# RNCP 39394
# =============================================================================

set -e

# Configuration
PROJECT_NAME="station-traffeyere"
COMPOSE_FILE="docker-compose.coolify.yml"
ENV_FILE="infrastructure/.env.sample"
BACKUP_DIR="infrastructure/backups"

# Couleurs pour logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonction de logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Banner
show_banner() {
    echo -e "${BLUE}"
    cat << 'EOF'
 ____  _        _   _               _____           __  __               
/ ___|| |_ __ _| |_(_) ___  _ __   |_   _| __ __ _ / _|/ _| ___ _   _  ___ _ __ ___  
\___ \| __/ _` | __| |/ _ \| '_ \    | || '__/ _` | |_| |_ / _ \ | | |/ _ \ '__/ _ \ 
 ___) | || (_| | |_| | (_) | | | |   | || | | (_| |  _|  _|  __/ |_| |  __/ | |  __/
|____/ \__\__,_|\__|_|\___/|_| |_|   |_||_|  \__,_|_| |_|  \___|\__, |\___|_|  \___|
                                                               |___/               
           IoT/AI Platform - Déploiement Local - RNCP 39394
EOF
    echo -e "${NC}"
}

# Vérifier les prérequis
check_prerequisites() {
    log "Vérification des prérequis..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        error "Docker n'est pas installé!"
        exit 1
    fi
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose n'est pas installé!"
        exit 1
    fi
    
    # Fichier de configuration
    if [ ! -f "$ENV_FILE" ]; then
        error "Fichier de configuration non trouvé: $ENV_FILE"
        exit 1
    fi
    
    log "✅ Prérequis vérifiés"
}

# Charger variables d'environnement
load_environment() {
    log "Chargement variables d'environnement..."
    
    # Copier le fichier d'exemple si .env n'existe pas
    if [ ! -f ".env" ]; then
        log "Création du fichier .env à partir de .env.sample"
        cp "$ENV_FILE" ".env"
        warn "⚠️  Modifiez le fichier .env avec vos valeurs spécifiques!"
    fi
    
    # Charger les variables
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
        log "✅ Variables d'environnement chargées"
    fi
}

# Générer secrets pour développement local
generate_dev_secrets() {
    log "Génération des secrets pour développement local..."
    
    # Fonction pour générer secret aléatoire
    generate_secret() {
        openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
    }
    
    # Remplacer les secrets par défaut
    sed -i.bak \
        -e "s/CHANGEME_POSTGRES_PROD_PASSWORD/$(generate_secret)/g" \
        -e "s/CHANGEME_REDIS_PROD_PASSWORD/$(generate_secret)/g" \
        -e "s/CHANGEME_INFLUXDB_ADMIN_PASSWORD/$(generate_secret)/g" \
        -e "s/CHANGEME_MINIO_ROOT_USER/admin$(generate_secret | cut -c1-8)/g" \
        -e "s/CHANGEME_MINIO_ROOT_PASSWORD/$(generate_secret)/g" \
        -e "s/CHANGEME_JWT_SECRET_256_BITS_MIN/$(generate_secret)/g" \
        -e "s/CHANGEME_API_SECRET_KEY_256_BITS/$(generate_secret)/g" \
        ".env"
    
    log "✅ Secrets générés pour développement"
}

# Créer répertoires nécessaires
create_directories() {
    log "Création des répertoires..."
    
    directories=(
        "$BACKUP_DIR"
        "logs"
        "data/postgres"
        "data/redis"
        "data/influxdb"
        "data/minio"
        "data/grafana"
        "data/prometheus"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log "✅ Répertoire créé: $dir"
    done
}

# Sauvegarder déploiement existant
backup_existing() {
    log "Sauvegarde du déploiement existant..."
    
    # Vérifier si des conteneurs existent
    if docker-compose -f "$COMPOSE_FILE" ps -q | wc -l > 0; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_file="$BACKUP_DIR/backup_$timestamp.tar.gz"
        
        log "Création de la sauvegarde: $backup_file"
        
        # Sauvegarder volumes
        docker run --rm \
            -v ${PROJECT_NAME}_postgres_data:/data/postgres:ro \
            -v ${PROJECT_NAME}_grafana_data:/data/grafana:ro \
            -v "$PWD/$BACKUP_DIR":/backup \
            alpine tar czf "/backup/backup_$timestamp.tar.gz" /data
        
        log "✅ Sauvegarde créée"
    else
        log "Aucun déploiement existant trouvé"
    fi
}

# Arrêter services existants
stop_existing() {
    log "Arrêt des services existants..."
    
    if docker-compose -f "$COMPOSE_FILE" ps -q >/dev/null 2>&1; then
        docker-compose -f "$COMPOSE_FILE" down --remove-orphans
        log "✅ Services arrêtés"
    else
        log "Aucun service à arrêter"
    fi
}

# Construire les images
build_images() {
    log "Construction des images..."
    
    # Build avec cache pour optimiser
    docker-compose -f "$COMPOSE_FILE" build --parallel
    
    log "✅ Images construites"
}

# Déployer services
deploy_services() {
    log "Déploiement des services..."
    
    # Démarrer en arrière-plan
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log "✅ Services déployés"
}

# Attendre que les services soient prêts
wait_for_services() {
    log "Attente de la disponibilité des services..."
    
    # Services à vérifier avec leur endpoint de health check
    services=(
        "backend:8000:/healthz"
        "frontend:80:/healthz"
        "grafana:3000:/api/health"
        "prometheus:9090/-/healthy"
        "influxdb:8086/health"
    )
    
    for service_info in "${services[@]}"; do
        service=$(echo "$service_info" | cut -d':' -f1)
        port=$(echo "$service_info" | cut -d':' -f2)
        endpoint=$(echo "$service_info" | cut -d':' -f3)
        url="http://localhost:$port$endpoint"
        
        log "Vérification $service ($url)..."
        
        max_attempts=30
        attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -s -f "$url" >/dev/null 2>&1; then
                log "✅ $service est prêt"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                warn "⚠️  $service non accessible après $max_attempts tentatives"
            else
                sleep 2
                attempt=$((attempt + 1))
            fi
        done
    done
}

# Afficher résumé du déploiement
show_summary() {
    log "Génération du résumé de déploiement..."
    
    echo ""
    echo -e "${BLUE}=== RÉSUMÉ DU DÉPLOIEMENT ===${NC}"
    echo ""
    echo "🌐 Services accessibles:"
    echo "  • Frontend:    http://localhost:80"
    echo "  • Backend API: http://localhost:8000"
    echo "  • Grafana:     http://localhost:3000 (admin/admin)"
    echo "  • Prometheus:  http://localhost:9090"
    echo "  • InfluxDB:    http://localhost:8086"
    echo "  • MinIO:       http://localhost:9001"
    echo ""
    echo "📊 Status des conteneurs:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "💾 Utilisation des volumes:"
    docker system df -v | grep "$PROJECT_NAME" || true
    echo ""
    echo "🔧 Commandes utiles:"
    echo "  • Voir les logs:     docker-compose -f $COMPOSE_FILE logs -f"
    echo "  • Arrêter:           docker-compose -f $COMPOSE_FILE down"
    echo "  • Redémarrer:        docker-compose -f $COMPOSE_FILE restart"
    echo "  • Shell backend:     docker-compose -f $COMPOSE_FILE exec backend bash"
    echo ""
}

# Tests de fumée
run_smoke_tests() {
    log "Exécution des tests de fumée..."
    
    tests_passed=0
    tests_total=0
    
    # Test 1: Backend health
    tests_total=$((tests_total + 1))
    if curl -s -f "http://localhost:8000/healthz" >/dev/null; then
        log "✅ Test Backend Health: PASSED"
        tests_passed=$((tests_passed + 1))
    else
        error "❌ Test Backend Health: FAILED"
    fi
    
    # Test 2: Frontend health
    tests_total=$((tests_total + 1))
    if curl -s -f "http://localhost:80/healthz" >/dev/null; then
        log "✅ Test Frontend Health: PASSED"
        tests_passed=$((tests_passed + 1))
    else
        error "❌ Test Frontend Health: FAILED"
    fi
    
    # Test 3: Prometheus metrics
    tests_total=$((tests_total + 1))
    if curl -s "http://localhost:9090/api/v1/query?query=up" | grep -q "success"; then
        log "✅ Test Prometheus Metrics: PASSED"
        tests_passed=$((tests_passed + 1))
    else
        error "❌ Test Prometheus Metrics: FAILED"
    fi
    
    # Test 4: Base de données
    tests_total=$((tests_total + 1))
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U station_user >/dev/null 2>&1; then
        log "✅ Test Database: PASSED"
        tests_passed=$((tests_passed + 1))
    else
        error "❌ Test Database: FAILED"
    fi
    
    echo ""
    echo "📊 Résultats des tests: $tests_passed/$tests_total réussis"
    
    if [ $tests_passed -eq $tests_total ]; then
        log "🎉 Tous les tests de fumée sont passés!"
        return 0
    else
        error "⚠️  Certains tests ont échoué"
        return 1
    fi
}

# Fonction principale
main() {
    show_banner
    
    log "🚀 Démarrage du déploiement local de Station Traffeyère..."
    
    # Vérifications préliminaires
    check_prerequisites
    
    # Chargement environnement
    load_environment
    
    # Génération secrets dev
    generate_dev_secrets
    
    # Préparation
    create_directories
    backup_existing
    stop_existing
    
    # Déploiement
    build_images
    deploy_services
    
    # Vérification
    wait_for_services
    
    # Tests
    run_smoke_tests
    
    # Résumé
    show_summary
    
    log "🎉 Déploiement local terminé avec succès!"
    log "📚 Documentation: https://github.com/votre-repo/station-traffeyere"
    log "🆘 Support: johann@johann-lebel.fr"
}

# Gestion des signaux
cleanup() {
    warn "Interruption détectée, nettoyage..."
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    exit 1
}

trap cleanup SIGINT SIGTERM

# Vérification des arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Usage: $0 [help|stop|restart|logs|status]"
        echo ""
        echo "Commandes:"
        echo "  help     - Affiche cette aide"
        echo "  stop     - Arrête tous les services"
        echo "  restart  - Redémarre tous les services"
        echo "  logs     - Affiche les logs en temps réel"
        echo "  status   - Affiche le statut des services"
        exit 0
        ;;
    "stop")
        log "Arrêt des services..."
        docker-compose -f "$COMPOSE_FILE" down
        log "✅ Services arrêtés"
        exit 0
        ;;
    "restart")
        log "Redémarrage des services..."
        docker-compose -f "$COMPOSE_FILE" restart
        log "✅ Services redémarrés"
        exit 0
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f
        exit 0
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        exit 0
        ;;
    "")
        # Déploiement complet
        main "$@"
        ;;
    *)
        error "Commande inconnue: $1"
        echo "Utilisez '$0 help' pour voir les commandes disponibles"
        exit 1
        ;;
esac