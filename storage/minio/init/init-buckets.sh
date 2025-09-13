#!/bin/bash
# =============================================================================
# Script d'initialisation MinIO - Station Traffeyère
# Création automatique des buckets et configuration sécurité
# =============================================================================

set -e

# Configuration MinIO
MINIO_ENDPOINT="http://minio:9000"
MINIO_ACCESS_KEY="${MINIO_ROOT_USER:-admin}"
MINIO_SECRET_KEY="${MINIO_ROOT_PASSWORD:-ChangeMeInProduction123!}"

# Couleurs pour logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Attendre que MinIO soit disponible
wait_for_minio() {
    log "Waiting for MinIO to be ready..."
    local max_attempts=60
    local attempt=1
    
    while ! curl -s "$MINIO_ENDPOINT/minio/health/live" >/dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            error "MinIO not available after $max_attempts attempts"
            exit 1
        fi
        
        warn "Attempt $attempt/$max_attempts: MinIO not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log "MinIO is ready! ✅"
}

# Configuration mc (MinIO Client)
configure_mc() {
    log "Configuring MinIO client..."
    
    # Alias pour notre instance MinIO
    mc alias set station-minio "$MINIO_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
    
    if mc admin info station-minio >/dev/null 2>&1; then
        log "MinIO client configured successfully ✅"
    else
        error "Failed to configure MinIO client"
        exit 1
    fi
}

# Création des buckets
create_buckets() {
    log "Creating MinIO buckets..."
    
    # Liste des buckets à créer
    buckets=(
        "uploads:rw"           # Uploads utilisateurs
        "models:rw"            # Modèles IA/ML
        "logs:rw"              # Logs applicatifs  
        "backups:rw"           # Sauvegardes
        "iot-data:rw"          # Données IoT archivées
        "dashboards:rw"        # Exports dashboards
        "reports:rw"           # Rapports générés
        "temp:rw"              # Fichiers temporaires
        "static:r"             # Assets statiques
        "public:r"             # Fichiers publics
    )
    
    for bucket_info in "${buckets[@]}"; do
        bucket_name=$(echo "$bucket_info" | cut -d':' -f1)
        bucket_policy=$(echo "$bucket_info" | cut -d':' -f2)
        
        # Créer le bucket s'il n'existe pas
        if ! mc ls "station-minio/$bucket_name" >/dev/null 2>&1; then
            log "Creating bucket: $bucket_name"
            mc mb "station-minio/$bucket_name"
            
            # Appliquer la politique de sécurité
            case "$bucket_policy" in
                "rw")
                    # Lecture/Écriture pour utilisateurs authentifiés
                    cat > /tmp/policy-$bucket_name.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject", "s3:PutObject"],
            "Resource": "arn:aws:s3:::$bucket_name/*"
        }
    ]
}
EOF
                    ;;
                "r")
                    # Lecture seule
                    cat > /tmp/policy-$bucket_name.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": "arn:aws:s3:::$bucket_name/*"
        }
    ]
}
EOF
                    ;;
            esac
            
            # Appliquer la politique
            mc policy set-json /tmp/policy-$bucket_name.json "station-minio/$bucket_name"
            rm -f /tmp/policy-$bucket_name.json
            
            log "✅ Bucket '$bucket_name' created with $bucket_policy policy"
        else
            log "Bucket '$bucket_name' already exists"
        fi
    done
}

# Configuration lifecycle (rétention)
setup_lifecycle() {
    log "Configuring bucket lifecycle policies..."
    
    # Politique pour bucket temporaire (7 jours)
    cat > /tmp/lifecycle-temp.json << 'EOF'
{
    "Rules": [
        {
            "ID": "TempCleanup",
            "Status": "Enabled",
            "Expiration": {
                "Days": 7
            }
        }
    ]
}
EOF
    
    mc ilm add station-minio/temp < /tmp/lifecycle-temp.json
    
    # Politique pour logs (90 jours)
    cat > /tmp/lifecycle-logs.json << 'EOF'
{
    "Rules": [
        {
            "ID": "LogsCleanup", 
            "Status": "Enabled",
            "Expiration": {
                "Days": 90
            }
        }
    ]
}
EOF
    
    mc ilm add station-minio/logs < /tmp/lifecycle-logs.json
    
    # Politique pour données IoT anciennes (1 an)
    cat > /tmp/lifecycle-iot.json << 'EOF'
{
    "Rules": [
        {
            "ID": "IoTArchive",
            "Status": "Enabled", 
            "Transition": {
                "Days": 30,
                "StorageClass": "GLACIER"
            },
            "Expiration": {
                "Days": 365
            }
        }
    ]
}
EOF
    
    mc ilm add station-minio/iot-data < /tmp/lifecycle-iot.json
    
    # Nettoyage fichiers temporaires
    rm -f /tmp/lifecycle-*.json
    
    log "✅ Lifecycle policies configured"
}

# Configuration monitoring
setup_monitoring() {
    log "Configuring MinIO monitoring..."
    
    # Activer l'audit log
    mc admin config set station-minio audit webhook:1 \
        endpoint="http://backend:8000/webhooks/minio" \
        auth_token="${MINIO_WEBHOOK_TOKEN}"
    
    # Configuration Prometheus metrics
    mc admin prometheus generate station-minio
    
    log "✅ Monitoring configured"
}

# Création d'utilisateurs de service
create_service_users() {
    log "Creating service users..."
    
    # Utilisateur pour backend
    mc admin user add station-minio backend-service "${MINIO_BACKEND_PASSWORD}"
    
    # Politique pour le backend
    cat > /tmp/backend-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject", 
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::uploads/*",
                "arn:aws:s3:::uploads",
                "arn:aws:s3:::models/*",
                "arn:aws:s3:::models",
                "arn:aws:s3:::reports/*",
                "arn:aws:s3:::reports"
            ]
        }
    ]
}
EOF
    
    mc admin policy add station-minio backend-policy /tmp/backend-policy.json
    mc admin policy set station-minio backend-policy user=backend-service
    
    # Utilisateur pour IoT data
    mc admin user add station-minio iot-service "${MINIO_IOT_PASSWORD}"
    
    cat > /tmp/iot-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::iot-data/*"
            ]
        }
    ]
}
EOF
    
    mc admin policy add station-minio iot-policy /tmp/iot-policy.json
    mc admin policy set station-minio iot-policy user=iot-service
    
    # Nettoyage
    rm -f /tmp/*-policy.json
    
    log "✅ Service users created"
}

# Fonction principale
main() {
    log "🚀 Starting MinIO initialization for Station Traffeyère..."
    
    # Attendre MinIO
    wait_for_minio
    
    # Configuration client
    configure_mc
    
    # Création buckets
    create_buckets
    
    # Configuration lifecycle
    setup_lifecycle
    
    # Configuration monitoring
    setup_monitoring
    
    # Création utilisateurs
    create_service_users
    
    log "🎉 MinIO initialization completed successfully!"
    log "📊 Buckets created and configured for Station Traffeyère IoT/AI Platform"
    
    # Affichage résumé
    echo ""
    echo "=== MINIO CONFIGURATION SUMMARY ==="
    mc ls station-minio/
    echo ""
    mc admin info station-minio
}

# Vérifier si mc (MinIO Client) est installé
if ! command -v mc &> /dev/null; then
    log "Installing MinIO client..."
    curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
    chmod +x mc
    sudo mv mc /usr/local/bin/
fi

# Exécution
main "$@"