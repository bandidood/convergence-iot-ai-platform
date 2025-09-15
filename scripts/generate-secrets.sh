#!/bin/bash
set -e

# =============================================================================
# GÉNÉRATEUR DE SECRETS - Station Traffeyère IoT/AI Platform
# Génère tous les secrets sécurisés nécessaires au déploiement
# =============================================================================

echo "🔐 Génération des secrets sécurisés pour Station Traffeyère..."

# Fonction pour générer un mot de passe sécurisé
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Fonction pour générer une clé hexadécimale
generate_hex_key() {
    openssl rand -hex 32
}

# Génération de tous les secrets
SECRET_KEY=$(generate_hex_key)
JWT_SECRET=$(generate_hex_key)
POSTGRES_PASSWORD=$(generate_password)
REDIS_PASSWORD=$(generate_password)
INFLUX_PASSWORD=$(generate_password)
INFLUX_ADMIN_TOKEN=$(generate_hex_key)
MQTT_PASSWORD=$(generate_password)
GRAFANA_ADMIN_PASSWORD=$(generate_password)
GRAFANA_DB_PASSWORD=$(generate_password)

# Affichage des secrets générés
echo ""
echo "✅ Secrets générés avec succès !"
echo ""
echo "📋 COPIEZ CES VALEURS DANS VOTRE .env :"
echo "=================================="
echo ""
echo "# Sécurité"
echo "SECRET_KEY=${SECRET_KEY}"
echo "JWT_SECRET=${JWT_SECRET}"
echo ""
echo "# Base de données"
echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
echo "REDIS_PASSWORD=${REDIS_PASSWORD}"
echo ""
echo "# InfluxDB"
echo "INFLUX_PASSWORD=${INFLUX_PASSWORD}"
echo "INFLUX_ADMIN_TOKEN=${INFLUX_ADMIN_TOKEN}"
echo ""
echo "# MQTT"  
echo "MQTT_PASSWORD=${MQTT_PASSWORD}"
echo ""
echo "# Monitoring"
echo "GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}"
echo "GRAFANA_DB_PASSWORD=${GRAFANA_DB_PASSWORD}"
echo ""
echo "=================================="
echo ""
echo "⚠️  IMPORTANT :"
echo "1. Sauvegardez ces secrets en lieu sûr"
echo "2. Ne les partagez JAMAIS dans un repository public"
echo "3. Utilisez-les dans votre fichier .env uniquement"
echo ""

# Option pour créer automatiquement le fichier .env
read -p "Voulez-vous créer automatiquement le fichier .env ? (y/n): " create_env

if [[ $create_env =~ ^[Yy]$ ]]; then
    # Demander le domaine (avec valeur par défaut CCDigital)
    read -p "Entrez votre domaine principal [traffeyere.ccdigital.fr]: " domain_name
    domain_name=${domain_name:-traffeyere.ccdigital.fr}
    read -p "Entrez votre email pour Let's Encrypt [admin@ccdigital.fr]: " acme_email
    acme_email=${acme_email:-admin@ccdigital.fr}
    
    # Créer le fichier .env
    cat > .env << EOF
# =============================================================================
# CONFIGURATION PRODUCTION - Station Traffeyère IoT/AI Platform
# Générée automatiquement le $(date)
# =============================================================================

# DOMAINES
DOMAIN_ROOT=${domain_name}
ACME_EMAIL=${acme_email}

# SÉCURITÉ
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}

# BASE DE DONNÉES
POSTGRES_DB=station_traffeyere
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
GRAFANA_DB_PASSWORD=${GRAFANA_DB_PASSWORD}

# INFLUXDB
INFLUX_USERNAME=admin
INFLUX_PASSWORD=${INFLUX_PASSWORD}
INFLUX_ORG=traffeyere
INFLUX_BUCKET=iot_sensors
INFLUX_ADMIN_TOKEN=${INFLUX_ADMIN_TOKEN}

# REDIS
REDIS_PASSWORD=${REDIS_PASSWORD}

# MQTT
MQTT_USERNAME=iot_user
MQTT_PASSWORD=${MQTT_PASSWORD}

# MONITORING
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}

# CONFIGURATION MÉTIER
STATION_ID=TRAFFEYERE_001
STATION_NAME=Station Traffeyère
STATION_LOCATION=45.764043,4.835659

# SEUILS ALERTES
TEMP_ALERT_THRESHOLD=35.0
PRESSURE_ALERT_THRESHOLD=2.5
PH_ALERT_THRESHOLD_MIN=6.0
PH_ALERT_THRESHOLD_MAX=8.5

# PARAMÈTRES IA
AI_CONFIDENCE_THRESHOLD=0.85
ANOMALY_DETECTION_WINDOW=3600
MODEL_UPDATE_INTERVAL=86400

# API KEYS IA (À CONFIGURER MANUELLEMENT)
# OPENAI_API_KEY=sk-your-openai-key
# ANTHROPIC_API_KEY=sk-ant-your-claude-key
# GOOGLE_API_KEY=your-gemini-key
# PERPLEXITY_API_KEY=pplx-your-perplexity-key

# MONITORING EXTERNE (OPTIONNEL)
# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
EOF

    echo "✅ Fichier .env créé avec succès !"
    echo ""
    echo "📝 PROCHAINES ÉTAPES :"
    echo "1. Vérifiez le contenu du fichier .env"
    echo "2. Ajoutez vos clés API IA (OpenAI, Claude, etc.)"
    echo "3. Configurez vos DNS pour pointer vers votre serveur"
    echo "4. Lancez le déploiement Coolify"
    echo ""
else
    echo "📝 Copiez manuellement les secrets ci-dessus dans votre .env"
fi

echo "🚀 Prêt pour le déploiement !"