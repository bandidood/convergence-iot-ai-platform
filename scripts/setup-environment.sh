#!/bin/bash
# =============================================================================
# SCRIPT D'INITIALISATION ENVIRONNEMENT SÉCURISÉ
# Station Traffeyère IoT/AI Platform - RNCP 39394
# =============================================================================

set -euo pipefail

# Configuration
PROJECT_NAME="station-traffeyere-iot-ai-platform"
VERSION="v1.0.0"
LOG_FILE="/tmp/setup-traffeyere-$(date +%Y%m%d_%H%M%S).log"

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

# Bannière projet
show_banner() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                          🏭 STATION TRAFFEYÈRE IoT/AI PLATFORM 🏭                                           ║"
    echo "║                                                                                                              ║"
    echo "║    📚 Projet RNCP 39394 - Expert en Systèmes d'Information et Sécurité                                     ║"
    echo "║    🚀 Setup Environnement Sécurisé Automatisé                                                               ║"
    echo "║    📊 Architecture Convergente Zero Trust                                                                    ║"
    echo "║                                                                                                              ║"
    echo "║    🎯 38 Services • 🛡️ ISA/IEC 62443 SL3+ • 🤖 Edge AI • ⛓️ Blockchain • 🎮 Digital Twin                    ║"
    echo "║                                                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Vérification prérequis
check_requirements() {
    log "🔍 Vérification des prérequis système..."
    
    # OS Support
    if [[ "$OSTYPE" != "linux-gnu"* && "$OSTYPE" != "darwin"* ]]; then
        error "OS non supporté. Linux ou macOS requis."
    fi
    
    # Docker
    if ! command -v docker &> /dev/null; then
        error "Docker n'est pas installé. Installation requise : https://docs.docker.com/get-docker/"
    fi
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose n'est pas installé."
    fi
    
    # Git
    if ! command -v git &> /dev/null; then
        error "Git n'est pas installé."
    fi
    
    # Python (pour pre-commit)
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        warn "Python non détecté. Installation recommandée pour hooks de sécurité."
    fi
    
    # Node.js (pour interfaces)
    if ! command -v node &> /dev/null; then
        warn "Node.js non détecté. Installation recommandée pour frontend."
    fi
    
    # Espace disque (minimum 10GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    required_space=$((10 * 1024 * 1024)) # 10GB en KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        error "Espace disque insuffisant. 10GB minimum requis."
    fi
    
    log "✅ Prérequis système validés"
}

# Installation outils développement
install_dev_tools() {
    log "🛠️ Installation des outils de développement..."
    
    # Pre-commit hooks
    if command -v pip3 &> /dev/null; then
        pip3 install --user pre-commit detect-secrets bandit safety
        log "✅ Pre-commit et outils sécurité installés"
    elif command -v pip &> /dev/null; then
        pip install --user pre-commit detect-secrets bandit safety
        log "✅ Pre-commit et outils sécurité installés"
    else
        warn "Pip non disponible. Pre-commit hooks non installés."
    fi
    
    # Installation Trivy (scanner vulnérabilités)
    if ! command -v trivy &> /dev/null; then
        info "Installation Trivy scanner..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install trivy
            else
                warn "Homebrew non disponible. Installation manuelle de Trivy recommandée."
            fi
        fi
        log "✅ Trivy scanner installé"
    fi
}

# Génération des secrets sécurisés
generate_secrets() {
    log "🔐 Génération des secrets sécurisés..."
    
    ENV_FILE=".env.production"
    
    if [ -f "$ENV_FILE" ]; then
        warn "Fichier .env.production existant. Sauvegarde créée."
        cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Génération secrets aléatoires sécurisés
    POSTGRES_PWD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PWD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/")
    API_TOKEN=$(openssl rand -hex 32)
    VAULT_TOKEN=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    INFLUX_TOKEN=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    MINIO_ACCESS_KEY=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
    MINIO_SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    GRAFANA_PWD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32)
    
    # Création fichier .env.production
    cat > "$ENV_FILE" << EOF
# =============================================================================
# VARIABLES D'ENVIRONNEMENT PRODUCTION - STATION TRAFFEYÈRE IoT/AI PLATFORM
# Générées automatiquement le $(date)
# =============================================================================

# === CONFIGURATION GÉNÉRALE ===
ENVIRONMENT=production
DOMAIN_BASE=traffeyere.local
VERSION=$VERSION
PROJECT_NAME=$PROJECT_NAME

# === AUTHENTIFICATION & SÉCURITÉ ===
POSTGRES_PASSWORD=$POSTGRES_PWD
REDIS_PASSWORD=$REDIS_PWD
JWT_SECRET_KEY=$JWT_SECRET
API_TOKEN=$API_TOKEN
VAULT_ROOT_TOKEN=$VAULT_TOKEN
MODEL_ENCRYPTION_KEY=$ENCRYPTION_KEY

# === BASE DE DONNÉES ===
POSTGRES_DB=station_traffeyere
POSTGRES_USER=admin
DATABASE_URL=postgresql://admin:$POSTGRES_PWD@postgres:5432/station_traffeyere

# === INFLUXDB TIME-SERIES ===
INFLUX_USERNAME=admin
INFLUX_PASSWORD=$REDIS_PWD
INFLUX_ORG=traffeyere
INFLUX_BUCKET=iot_data
INFLUX_TOKEN=$INFLUX_TOKEN

# === STOCKAGE OBJET MINIO ===
MINIO_ROOT_USER=$MINIO_ACCESS_KEY
MINIO_ROOT_PASSWORD=$MINIO_SECRET_KEY
MINIO_BUCKET=traffeyere-data

# === MONITORING ===
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=$GRAFANA_PWD
PROMETHEUS_RETENTION=90d
PROMETHEUS_STORAGE_SIZE=10GB

# === EDGE AI CONFIGURATION ===
INFERENCE_BATCH_SIZE=32
MODEL_VERSION=v2.1.0
AI_LOG_LEVEL=INFO

# === IOT SIMULATION ===
IOT_DEVICE_COUNT=127
IOT_SIMULATION_SPEED=1.0

# === SÉCURITÉ AVANCÉE ===
ENABLE_2FA=true
SESSION_TIMEOUT=1800
MAX_LOGIN_ATTEMPTS=3
LOCKOUT_DURATION=900

# === CONFORMITÉ ===
SECURITY_LEVEL=SL3
AUDIT_LOGGING=true
COMPLIANCE_MODE=ISA_IEC_62443

# === NOTIFICATIONS ===
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=monitoring@traffeyere.com
# SMTP_PASSWORD=<à configurer manuellement>
# SLACK_WEBHOOK_URL=<à configurer manuellement>
EOF

    chmod 600 "$ENV_FILE"
    log "✅ Secrets générés et fichier .env.production créé"
    warn "🔒 IMPORTANT : Configurez manuellement SMTP_PASSWORD et SLACK_WEBHOOK_URL"
}

# Initialisation baseline détection secrets
init_secrets_baseline() {
    log "🔍 Initialisation baseline détection secrets..."
    
    if command -v detect-secrets &> /dev/null; then
        # Création baseline si inexistante
        if [ ! -f ".secrets.baseline" ]; then
            detect-secrets scan --all-files --baseline .secrets.baseline
            log "✅ Baseline secrets créée"
        else
            # Mise à jour baseline existante
            detect-secrets scan --baseline .secrets.baseline --update
            log "✅ Baseline secrets mise à jour"
        fi
    else
        warn "detect-secrets non disponible. Baseline non créée."
    fi
}

# Configuration hooks pre-commit
setup_pre_commit_hooks() {
    log "🪝 Configuration hooks pre-commit sécurisés..."
    
    if command -v pre-commit &> /dev/null; then
        # Installation hooks
        pre-commit install
        pre-commit install --hook-type commit-msg
        pre-commit install --hook-type pre-push
        
        # Test initial (optionnel, peut être long)
        info "Exécution test initial des hooks (peut prendre quelques minutes)..."
        if pre-commit run --all-files; then
            log "✅ Hooks pre-commit configurés et testés"
        else
            warn "Certains hooks ont échoué. Vérifiez la configuration."
        fi
    else
        warn "pre-commit non disponible. Hooks non configurés."
    fi
}

# Création structure volumes
create_volumes() {
    log "📁 Création des volumes persistants..."
    
    VOLUMES_PATH="./volumes"
    
    # Création dossiers volumes
    mkdir -p "$VOLUMES_PATH"/{postgres_data,redis_data,influxdb_data,minio_data,grafana_data,prometheus_data,edge_ai_models,iot_data,vault_data,splunk_data}
    
    # Configuration permissions sécurisées
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # PostgreSQL
        sudo chown -R 999:999 "$VOLUMES_PATH/postgres_data" 2>/dev/null || chown -R 999:999 "$VOLUMES_PATH/postgres_data"
        # Grafana
        sudo chown -R 472:472 "$VOLUMES_PATH/grafana_data" 2>/dev/null || chown -R 472:472 "$VOLUMES_PATH/grafana_data"
        # InfluxDB
        sudo chown -R 999:999 "$VOLUMES_PATH/influxdb_data" 2>/dev/null || chown -R 999:999 "$VOLUMES_PATH/influxdb_data"
    fi
    
    log "✅ Volumes créés avec permissions appropriées"
}

# Configuration réseaux Docker sécurisés
setup_docker_networks() {
    log "🌐 Configuration des réseaux Docker sécurisés..."
    
    # Création réseaux de segmentation si non existants
    docker network create --driver bridge \
        --subnet=172.20.1.0/24 \
        --gateway=172.20.1.1 \
        --label="security.zone=dmz-iot" \
        --label="security.level=sl1" \
        dmz-iot 2>/dev/null || warn "Réseau dmz-iot existe déjà"
    
    docker network create --driver bridge \
        --subnet=172.20.2.0/24 \
        --gateway=172.20.2.1 \
        --label="security.zone=edge-compute" \
        --label="security.level=sl2" \
        edge-compute 2>/dev/null || warn "Réseau edge-compute existe déjà"
    
    docker network create --driver bridge \
        --subnet=172.20.3.0/24 \
        --gateway=172.20.3.1 \
        --label="security.zone=cloud-platform" \
        --label="security.level=sl3" \
        cloud-platform 2>/dev/null || warn "Réseau cloud-platform existe déjà"
    
    docker network create --driver bridge \
        --subnet=172.20.4.0/24 \
        --gateway=172.20.4.1 \
        --label="security.zone=management" \
        --label="security.level=sl4" \
        management 2>/dev/null || warn "Réseau management existe déjà"
    
    log "✅ Réseaux de sécurité configurés"
}

# Téléchargement modèles ML factices
download_models() {
    log "🤖 Préparation modèles ML..."
    
    MODELS_PATH="./core/edge-ai-engine/models"
    mkdir -p "$MODELS_PATH"
    
    # Création modèles factices pour simulation (à remplacer par vrais modèles)
    if [ ! -f "$MODELS_PATH/anomaly_detection.tflite" ]; then
        info "Génération modèles factices pour simulation..."
        
        # Modèle TensorFlow Lite factice
        echo "# Modèle TensorFlow Lite factice - Station Traffeyère" > "$MODELS_PATH/anomaly_detection.tflite"
        echo "# Version: $VERSION" >> "$MODELS_PATH/anomaly_detection.tflite"
        echo "# Généré: $(date)" >> "$MODELS_PATH/anomaly_detection.tflite"
        
        # Scaler factice
        echo "# Scaler scikit-learn factice - Normalisation données IoT" > "$MODELS_PATH/scaler.pkl"
        
        # Data background factice
        echo "# Background data SHAP factice - Explicabilité IA" > "$MODELS_PATH/background_data.npy"
        
        log "✅ Modèles factices créés (à remplacer par vrais modèles)"
    else
        log "✅ Modèles ML détectés"
    fi
}

# Configuration certificats SSL
setup_certificates() {
    log "🔒 Configuration des certificats SSL..."
    
    CERTS_PATH="./security/pki"
    mkdir -p "$CERTS_PATH"/{ca-certificates,server-certificates,client-certificates}
    
    if [ ! -f "$CERTS_PATH/server-certificates/server.crt" ]; then
        info "Génération certificats auto-signés pour développement..."
        
        # Génération certificat serveur auto-signé
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$CERTS_PATH/server-certificates/server.key" \
            -out "$CERTS_PATH/server-certificates/server.crt" \
            -subj "/C=FR/ST=AuvergneRhoneAlpes/L=Lyon/O=StationTraffeyere/CN=*.traffeyere.local" \
            2>/dev/null
        
        # Génération CA racine
        openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
            -keyout "$CERTS_PATH/ca-certificates/ca.key" \
            -out "$CERTS_PATH/ca-certificates/ca.crt" \
            -subj "/C=FR/ST=AuvergneRhoneAlpes/L=Lyon/O=TraffeyereCA/CN=Traffeyere Root CA" \
            2>/dev/null
        
        # Permissions sécurisées
        chmod 600 "$CERTS_PATH"/*/*.key
        chmod 644 "$CERTS_PATH"/*/*.crt
        
        log "✅ Certificats SSL générés"
    else
        log "✅ Certificats SSL détectés"
    fi
}

# Tests de santé système
system_health_check() {
    log "🏥 Tests de santé système..."
    
    # Docker daemon
    if docker info > /dev/null 2>&1; then
        log "✅ Docker daemon opérationnel"
    else
        error "Docker daemon non accessible"
    fi
    
    # Espace disque restant
    available_space=$(df -h . | tail -1 | awk '{print $4}')
    log "💾 Espace disque disponible : $available_space"
    
    # Mémoire disponible
    if command -v free &> /dev/null; then
        available_mem=$(free -h | grep "Mem:" | awk '{print $7}')
        log "🧠 Mémoire disponible : $available_mem"
    fi
    
    # Validation configuration Docker Compose
    if [ -f "docker-compose.yml" ]; then
        if docker-compose config --quiet; then
            log "✅ Configuration Docker Compose valide"
        else
            warn "⚠️ Configuration Docker Compose contient des erreurs"
        fi
    fi
}

# Affichage informations finales
display_final_info() {
    log "📋 Informations de configuration finale"
    echo
    echo -e "${GREEN}🎯 ENVIRONNEMENT CONFIGURÉ${NC}"
    echo -e "• Projet: $PROJECT_NAME"
    echo -e "• Version: $VERSION"
    echo -e "• Environnement: Production"
    echo -e "• Logs setup: $LOG_FILE"
    echo
    echo -e "${BLUE}🔐 SÉCURITÉ${NC}"
    echo -e "• Secrets générés: .env.production"
    echo -e "• Certificats SSL: ./security/pki/"
    echo -e "• Hooks pre-commit: Actifs"
    echo -e "• Baseline secrets: .secrets.baseline"
    echo
    echo -e "${YELLOW}🚀 PROCHAINES ÉTAPES${NC}"
    echo -e "1. Configurer SMTP_PASSWORD dans .env.production"
    echo -e "2. Configurer SLACK_WEBHOOK_URL pour notifications"
    echo -e "3. Remplacer modèles factices par vrais modèles ML"
    echo -e "4. Lancer déploiement: docker-compose up -d"
    echo -e "5. Accéder monitoring: https://grafana.johann-lebel.fr"
    echo
    echo -e "${RED}⚡ COMMANDES UTILES${NC}"
    echo -e "• Démarrage:           docker-compose up -d"
    echo -e "• Logs:                docker-compose logs -f [service]"
    echo -e "• Status:              docker-compose ps"
    echo -e "• Tests sécurité:      ./scripts/security-scan.sh"
    echo -e "• Sauvegarde:          ./scripts/backup-volumes.sh"
    echo
}

# Fonction principale
main() {
    show_banner
    
    log "🚀 Début setup environnement Station Traffeyère IoT/AI Platform"
    
    check_requirements
    install_dev_tools
    generate_secrets
    init_secrets_baseline
    setup_pre_commit_hooks
    create_volumes
    setup_docker_networks
    download_models
    setup_certificates
    system_health_check
    display_final_info
    
    log "✅ Setup environnement terminé avec succès!"
    log "📊 Logs complets disponibles dans: $LOG_FILE"
    
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                   🎉 SETUP TERMINÉ AVEC SUCCÈS 🎉                                             ║"
    echo "║                                                                                                                ║"
    echo "║  Votre environnement Station Traffeyère IoT/AI Platform est maintenant configuré et sécurisé.               ║"
    echo "║  Vous pouvez procéder au déploiement de l'architecture complète.                                             ║"
    echo "║                                                                                                                ║"
    echo "║                              🚀 Prêt pour la révolution IoT/IA ! 🚀                                          ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Gestion des erreurs
trap 'error "Setup interrompu à la ligne $LINENO"' ERR

# Exécution si script appelé directement
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi