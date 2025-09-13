#!/bin/bash
# =============================================================================
# Docker Entrypoint - Station Traffeyère Backend
# Gestion gracieuse du démarrage et arrêt - RNCP 39394
# =============================================================================

set -e

# Configuration par défaut
: ${POSTGRES_HOST:="postgres"}
: ${POSTGRES_PORT:="5432"}
: ${REDIS_HOST:="redis"}
: ${REDIS_PORT:="6379"}
: ${INFLUXDB_HOST:="influxdb"}
: ${INFLUXDB_PORT:="8086"}
: ${MINIO_HOST:="minio"}
: ${MINIO_PORT:="9000"}

# Couleurs pour logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Attendre qu'un service soit disponible
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=60
    local attempt=1

    log "Waiting for $service_name ($host:$port)..."
    
    while ! nc -z $host $port; do
        if [ $attempt -ge $max_attempts ]; then
            error "Timeout waiting for $service_name after $max_attempts attempts"
            exit 1
        fi
        
        warn "Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log "$service_name is ready! ✅"
}

# Vérifier les services requis
check_dependencies() {
    log "🔍 Checking service dependencies..."
    
    # PostgreSQL/TimescaleDB
    wait_for_service $POSTGRES_HOST $POSTGRES_PORT "PostgreSQL/TimescaleDB"
    
    # Redis
    wait_for_service $REDIS_HOST $REDIS_PORT "Redis"
    
    # InfluxDB
    wait_for_service $INFLUXDB_HOST $INFLUXDB_PORT "InfluxDB"
    
    # MinIO (optionnel)
    if ! nc -z $MINIO_HOST $MINIO_PORT; then
        warn "MinIO not available, continuing without object storage"
    else
        log "MinIO is ready! ✅"
    fi
    
    log "✅ All required dependencies are ready!"
}

# Migrations de base de données
run_migrations() {
    log "🗄️ Running database migrations..."
    
    if [ -f "alembic.ini" ]; then
        log "Running Alembic migrations..."
        alembic upgrade head
        log "✅ Migrations completed successfully!"
    else
        warn "No alembic.ini found, skipping migrations"
    fi
}

# Initialisation des données
init_data() {
    log "🌱 Initializing application data..."
    
    if [ -f "scripts/init_data.py" ]; then
        log "Running data initialization script..."
        python scripts/init_data.py
        log "✅ Data initialization completed!"
    else
        log "No initialization script found, skipping"
    fi
}

# Validation de la configuration
validate_config() {
    log "⚙️ Validating configuration..."
    
    # Variables requises
    required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "JWT_SECRET"
        "API_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error "Required environment variable $var is not set!"
            exit 1
        fi
    done
    
    log "✅ Configuration validation passed!"
}

# Gestion gracieuse de l'arrêt
graceful_shutdown() {
    log "🛑 Received shutdown signal, stopping gracefully..."
    
    # Arrêter les processus enfants
    jobs -p | xargs -r kill -TERM
    
    # Attendre la fin des processus
    wait
    
    log "✅ Graceful shutdown completed"
    exit 0
}

# Configuration des signaux pour arrêt gracieux
trap graceful_shutdown SIGTERM SIGINT

# Fonction principale
main() {
    log "🚀 Starting Station Traffeyère Backend API..."
    log "🏷️ Version: ${APP_VERSION:-development}"
    log "🌍 Environment: ${FASTAPI_ENV:-production}"
    
    # Validation de la configuration
    validate_config
    
    # Vérification des dépendances
    check_dependencies
    
    # Migrations de base de données
    run_migrations
    
    # Initialisation des données
    init_data
    
    # Démarrage de l'application
    log "🎯 Starting FastAPI application..."
    log "📡 Listening on http://0.0.0.0:${UVICORN_PORT:-8000}"
    log "📊 Health check available at /healthz"
    log "📚 API Documentation available at /docs"
    
    # Exécuter la commande passée en paramètre
    exec "$@"
}

# Point d'entrée
if [ "$1" = "gunicorn" ] || [ "$1" = "uvicorn" ]; then
    main "$@"
elif [ "$1" = "shell" ]; then
    log "🐍 Starting Python shell..."
    exec python -i
elif [ "$1" = "test" ]; then
    log "🧪 Running tests..."
    exec pytest -v
elif [ "$1" = "migrate" ]; then
    check_dependencies
    run_migrations
elif [ "$1" = "init-data" ]; then
    check_dependencies
    init_data
else
    # Commande personnalisée
    log "📋 Running custom command: $@"
    exec "$@"
fi