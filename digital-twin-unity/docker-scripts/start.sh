#!/bin/bash
# =====================================================================================
# Station Traffeyère Digital Twin - Script de démarrage
# RNCP 39394 - Orchestration des services Unity + API
# =====================================================================================

set -e  # Arrêt en cas d'erreur

# Couleurs pour logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# =====================================================================================
# INITIALISATION
# =====================================================================================

log_info "🚀 Démarrage Station Traffeyère Digital Twin v2.1.0"
log_info "📋 RNCP 39394 - Digital Twin convergent IoT/IA sécurisé"

# Vérification environnement
if [ ! -d "/app/logs" ]; then
    mkdir -p /app/logs
    log_info "📁 Création répertoire logs"
fi

if [ ! -d "/app/unity" ]; then
    log_error "❌ Répertoire Unity manquant: /app/unity"
    exit 1
fi

# Variables d'environnement par défaut
export UNITY_APP_PATH=${UNITY_APP_PATH:-"/app/unity/StationTraffeyere.x86_64"}
export API_PORT=${API_PORT:-8080}
export WEB_PORT=${WEB_PORT:-8081}
export UNITY_LOG_LEVEL=${UNITY_LOG_LEVEL:-3}
export MQTT_BROKER_HOST=${MQTT_BROKER_HOST:-"mqtt-broker"}
export MQTT_BROKER_PORT=${MQTT_BROKER_PORT:-1883}

log_info "🔧 Configuration:"
log_info "   - Unity App: $UNITY_APP_PATH"
log_info "   - API Port: $API_PORT"
log_info "   - Web Port: $WEB_PORT"
log_info "   - MQTT Broker: $MQTT_BROKER_HOST:$MQTT_BROKER_PORT"

# =====================================================================================
# ATTENTE DES SERVICES
# =====================================================================================

log_info "⏳ Attente des services externes..."

# Attente MQTT Broker
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_wait=60
    local count=0
    
    log_info "🔍 Attente $service_name ($host:$port)..."
    
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $count -ge $max_wait ]; then
            log_error "❌ Timeout attente $service_name"
            return 1
        fi
        sleep 2
        count=$((count + 2))
    done
    
    log_success "✅ $service_name disponible"
    return 0
}

# Services critiques
wait_for_service "$MQTT_BROKER_HOST" "$MQTT_BROKER_PORT" "MQTT Broker" || {
    log_warning "⚠️ MQTT Broker non disponible - Continuité en mode dégradé"
}

# Redis si configuré
if [ -n "$REDIS_HOST" ]; then
    wait_for_service "$REDIS_HOST" "${REDIS_PORT:-6379}" "Redis" || {
        log_warning "⚠️ Redis non disponible - Cache désactivé"
    }
fi

# =====================================================================================
# DÉMARRAGE SERVICES
# =====================================================================================

log_info "🎯 Démarrage des services via Supervisor..."

# Configuration Supervisor dynamique
cat > /tmp/supervisord-dynamic.conf << EOF
[supervisord]
nodaemon=true
user=unity
logfile=/app/logs/supervisor.log
pidfile=/tmp/supervisord.pid
childlogdir=/app/logs/

[program:digital-twin-api]
command=python3 /app/api/main.py
directory=/app/api
user=unity
autostart=true
autorestart=true
startretries=3
stdout_logfile=/app/logs/api-stdout.log
stderr_logfile=/app/logs/api-stderr.log
environment=PYTHONPATH="/app/api",API_PORT="$API_PORT",MQTT_BROKER_HOST="$MQTT_BROKER_HOST",MQTT_BROKER_PORT="$MQTT_BROKER_PORT"

[program:unity-digital-twin]
command=/app/start-unity.sh
directory=/app
user=unity
autostart=true
autorestart=true
startretries=3
stdout_logfile=/app/logs/unity-stdout.log
stderr_logfile=/app/logs/unity-stderr.log
environment=DISPLAY=:99,UNITY_LOG_LEVEL="$UNITY_LOG_LEVEL"

[program:xvfb]
command=Xvfb :99 -screen 0 1920x1080x24
user=unity
autostart=true
autorestart=true
stdout_logfile=/app/logs/xvfb-stdout.log
stderr_logfile=/app/logs/xvfb-stderr.log

[program:web-server]
command=http-server /app/web -p $WEB_PORT --cors
directory=/app/web
user=unity
autostart=true
autorestart=true
stdout_logfile=/app/logs/web-stdout.log
stderr_logfile=/app/logs/web-stderr.log
EOF

# Script de démarrage Unity
cat > /app/start-unity.sh << 'EOF'
#!/bin/bash
set -e

log_info() {
    echo "[UNITY] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_info "🎮 Démarrage Unity Digital Twin Headless"

# Attendre Xvfb
sleep 5

# Vérification du binaire Unity
if [ ! -f "$UNITY_APP_PATH" ]; then
    log_info "❌ Binaire Unity non trouvé: $UNITY_APP_PATH"
    log_info "🔄 Utilisation du simulateur pour développement"
    /usr/local/bin/unity-simulator
    exit 0
fi

# Paramètres Unity headless optimisés
UNITY_PARAMS=(
    "-batchmode"
    "-nographics"
    "-logFile" "/app/logs/unity-console.log"
    "-force-vulkan"
    "-screen-width" "1920"
    "-screen-height" "1080"
)

# Ajout paramètres selon niveau de log
case $UNITY_LOG_LEVEL in
    0) UNITY_PARAMS+=("-silent") ;;
    1) UNITY_PARAMS+=("-logLevel" "Error") ;;
    2) UNITY_PARAMS+=("-logLevel" "Warning") ;;
    3) UNITY_PARAMS+=("-logLevel" "Info") ;;
    4) UNITY_PARAMS+=("-logLevel" "Debug") ;;
esac

log_info "🚀 Lancement Unity avec paramètres: ${UNITY_PARAMS[*]}"

# Démarrage Unity
exec "$UNITY_APP_PATH" "${UNITY_PARAMS[@]}"
EOF

chmod +x /app/start-unity.sh

# Simulateur Unity pour développement
cat > /usr/local/bin/unity-simulator << 'EOF'
#!/bin/bash
# Simulateur Unity pour tests sans build réel

log_info() {
    echo "[UNITY-SIM] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_info "🎮 Simulateur Unity Digital Twin démarré"
log_info "📡 Connexion MQTT simulée"
log_info "🔧 Mode développement - RNCP 39394"

# Boucle principale avec heartbeat
while true; do
    log_info "💓 Unity Digital Twin actif - $(date)"
    log_info "📊 127 capteurs simulés"
    log_info "🎯 API REST disponible sur port $API_PORT"
    sleep 30
done
EOF

chmod +x /usr/local/bin/unity-simulator

# =====================================================================================
# LANCEMENT SUPERVISOR
# =====================================================================================

log_info "🎬 Lancement Supervisor avec configuration dynamique"

# Affichage final
log_success "✅ Station Traffeyère Digital Twin prêt!"
log_success "🌐 API REST: http://localhost:$API_PORT/docs"
log_success "🎮 Web Interface: http://localhost:$WEB_PORT"
log_success "📊 Métriques: http://localhost:$API_PORT/metrics"

# Démarrage Supervisor en premier plan
exec /usr/bin/supervisord -c /tmp/supervisord-dynamic.conf
