# 🚀 Guide de Déploiement Coolify - Station Traffeyère

Guide complet pour déployer la **Station Traffeyère IoT/AI Platform** via Coolify étape par étape.

## 📋 Prérequis

### 🔧 Infrastructure
- **Serveur** : VPS/Dédié avec Docker (min 4 vCPU, 8GB RAM)
- **OS** : Ubuntu 22.04+ ou Debian 12+
- **Coolify** : Version 4.0+ installée et configurée
- **Domaines** : DNS configuré vers votre serveur

### 🌐 Sous-domaines requis
- `traffeyere-station.fr` (principal)
- `api.traffeyere-station.fr` (backend)
- `ws.traffeyere-station.fr` (websocket)
- `grafana.traffeyere-station.fr` (monitoring)
- `influx.traffeyere-station.fr` (base de données)
- `metrics.traffeyere-station.fr` (prometheus)

## 🎯 PHASE 1: Préparation Initiale

### 1. Cloner le Repository
```bash
git clone https://github.com/your-username/station-traffeyere-iot-ai-platform.git
cd station-traffeyere-iot-ai-platform
```

### 2. Générer les Secrets
```bash
# Clés secrètes
export SECRET_KEY=$(openssl rand -hex 32)
export JWT_SECRET=$(openssl rand -hex 32)

# Mots de passe base de données
export POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
export REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
export INFLUX_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
export INFLUX_ADMIN_TOKEN=$(openssl rand -hex 32)

# Monitoring
export GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# MQTT
export MQTT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
```

### 3. Créer le fichier .env
```bash
cp .env.production .env
# Éditer .env avec vos valeurs générées
nano .env
```

## 🎯 PHASE 2: Configuration Coolify

### 1. Accéder à Coolify
```
https://your-coolify-instance.com
```

### 2. Créer un nouveau projet
- **Nom** : `station-traffeyere-iot-ai`
- **Description** : `IoT/AI Platform - Production`
- **Repository** : `https://github.com/your-username/station-traffeyere-iot-ai-platform.git`

## 🎯 PHASE 3: Déploiement Services Base

### 🗄️ PostgreSQL Database
```yaml
# Dans Coolify > Services > Database
Type: PostgreSQL
Name: postgres-traffeyere
Version: 15
Database: station_traffeyere
Username: postgres
Password: [POSTGRES_PASSWORD from .env]
Volume: postgres-data:/var/lib/postgresql/data
Network: backend
```

### 🚀 Redis Cache
```yaml
# Dans Coolify > Services > Database
Type: Redis  
Name: redis-traffeyere
Version: 7
Password: [REDIS_PASSWORD from .env]
Volume: redis-data:/data
Network: backend
Command: redis-server --requirepass [REDIS_PASSWORD] --appendonly yes
```

### 📊 InfluxDB Time-Series
```yaml
# Dans Coolify > Services > Database
Type: InfluxDB
Name: influxdb-traffeyere
Version: 2.7
Admin User: admin
Admin Password: [INFLUX_PASSWORD from .env]
Organization: traffeyere
Bucket: iot_sensors
Admin Token: [INFLUX_ADMIN_TOKEN from .env]
Volume: influxdb-data:/var/lib/influxdb2
Network: backend
Domain: influx.traffeyere-station.fr
SSL: Enabled (Let's Encrypt)
```

## 🎯 PHASE 4: Déploiement Backend

### ⚙️ Backend FastAPI
```yaml
# Dans Coolify > Applications
Type: Docker Compose
Name: backend-traffeyere
Source: Git Repository
Build Context: ./services/backend
Dockerfile: Dockerfile

# Variables d'environnement:
DATABASE_URL: postgresql://postgres:[POSTGRES_PASSWORD]@postgres:5432/station_traffeyere
REDIS_URL: redis://redis:6379/0
REDIS_PASSWORD: [REDIS_PASSWORD]
INFLUX_URL: http://influxdb:8086
INFLUX_TOKEN: [INFLUX_ADMIN_TOKEN]
INFLUX_ORG: traffeyere
INFLUX_BUCKET: iot_sensors
SECRET_KEY: [SECRET_KEY]
JWT_SECRET: [JWT_SECRET]
ENVIRONMENT: production
DEBUG: false

# Domaines:
- api.traffeyere-station.fr (Port 8000)
- ws.traffeyere-station.fr (Port 8000, WebSocket)

# Networks: backend, iot-network
# Health Check: /health endpoint
```

## 🎯 PHASE 5: Déploiement Frontend

### 🌐 Frontend React
```yaml
# Dans Coolify > Applications
Type: Docker Compose
Name: frontend-traffeyere
Source: Git Repository
Build Context: ./services/frontend
Dockerfile: Dockerfile

# Build Arguments:
NODE_ENV: production
REACT_APP_API_URL: https://api.traffeyere-station.fr
REACT_APP_WS_URL: wss://ws.traffeyere-station.fr
REACT_APP_ENVIRONMENT: production

# Domaines:
- traffeyere-station.fr (Port 80)
- www.traffeyere-station.fr (redirect to main)

# Networks: frontend
# SSL: Enabled (Let's Encrypt)
```

## 🎯 PHASE 6: Monitoring Stack

### 📈 Prometheus
```yaml
# Dans Coolify > Applications
Type: Docker Image
Name: prometheus-traffeyere
Image: prom/prometheus:latest
Volume: ./monitoring/prometheus/prometheus.prod.yml:/etc/prometheus/prometheus.yml
Volume: prometheus-data:/prometheus
Domain: metrics.traffeyere-station.fr
Port: 9090
Network: monitoring, backend
```

### 📊 Grafana
```yaml
# Dans Coolify > Applications  
Type: Docker Image
Name: grafana-traffeyere
Image: grafana/grafana:latest

# Variables d'environnement:
GF_SECURITY_ADMIN_PASSWORD: [GRAFANA_ADMIN_PASSWORD]
GF_USERS_ALLOW_SIGN_UP: false
GF_SERVER_DOMAIN: grafana.traffeyere-station.fr
GF_SERVER_ROOT_URL: https://grafana.traffeyere-station.fr

Volume: grafana-data:/var/lib/grafana
Domain: grafana.traffeyere-station.fr
Port: 3000
Network: monitoring, backend
```

## 🎯 PHASE 7: Configuration MQTT (Optionnel)

### 📡 Mosquitto MQTT
```yaml
# Dans Coolify > Applications
Type: Docker Image
Name: mosquitto-traffeyere
Image: eclipse-mosquitto:2.0
Volume: ./config/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf
Volume: mosquitto-data:/mosquitto/data
Ports:
  - 1883:1883 (MQTT)
  - 9001:9001 (WebSocket)
Network: iot-network
```

## 🎯 PHASE 8: Vérification Déploiement

### ✅ Tests de Connectivité
```bash
# Vérifier les endpoints
curl -f https://traffeyere-station.fr
curl -f https://api.traffeyere-station.fr/health
curl -f https://grafana.traffeyere-station.fr/login
curl -f https://influx.traffeyere-station.fr
```

### 🔐 Connexions Admin
```
Grafana: https://grafana.traffeyere-station.fr
└─ Utilisateur: admin
└─ Mot de passe: [GRAFANA_ADMIN_PASSWORD]

InfluxDB: https://influx.traffeyere-station.fr  
└─ Utilisateur: admin
└─ Mot de passe: [INFLUX_PASSWORD]
```

### 📊 Monitoring Santé
```bash
# Vérifier les métriques
curl https://api.traffeyere-station.fr/metrics

# Vérifier les logs
docker logs backend-traffeyere
docker logs frontend-traffeyere
```

## 🔧 Configuration Post-Déploiement

### 1. Configuration IA Providers
```bash
# Dans Coolify > backend-traffeyere > Environment Variables
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-claude-key  
GOOGLE_API_KEY=your-gemini-key
PERPLEXITY_API_KEY=pplx-your-perplexity-key
```

### 2. Configuration MQTT Users
```bash
# Créer utilisateurs MQTT
docker exec mosquitto-traffeyere mosquitto_passwd -c /mosquitto/config/pwfile iot_user
```

### 3. Import Dashboards Grafana
1. Connectez-vous à Grafana
2. Import > Upload JSON files dans `monitoring/grafana/dashboards/`
3. Configurer data sources (Prometheus, InfluxDB)

## 🚨 Sécurité et Maintenance

### 🔒 Sécurisation
- ✅ SSL/TLS automatique via Let's Encrypt
- ✅ Mots de passe forts générés automatiquement
- ✅ Network isolation (backend/frontend séparés)
- ✅ Health checks configurés
- ✅ Monitoring actif

### 🔄 Backup Automatique
```yaml
# Service backup dans Coolify
Type: Docker Image
Name: backup-traffeyere
Image: prodrigestivill/postgres-backup-local:15
Environment:
  POSTGRES_HOST: postgres
  POSTGRES_DB: station_traffeyere
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: [POSTGRES_PASSWORD]
  SCHEDULE: "@daily"
  BACKUP_KEEP_DAYS: 7
Volume: backup-data:/backups
```

## 📞 Support et Dépannage

### 🔍 Logs Importants
```bash
# Backend logs
docker logs backend-traffeyere -f

# Database logs  
docker logs postgres-traffeyere -f

# Frontend build logs
docker logs frontend-traffeyere -f
```

### ⚡ Redémarrage Services
```bash
# Via Coolify interface ou API
curl -X POST https://coolify.example.com/api/v1/applications/{id}/restart \
  -H "Authorization: Bearer $COOLIFY_TOKEN"
```

### 🎯 Métriques Clés à Surveiller
- **Latence API** : < 500ms (objectif < 100ms)
- **CPU Backend** : < 70%  
- **RAM Usage** : < 80%
- **Database Connections** : < 80% pool
- **IoT Messages/sec** : Variable selon charge

---

## 🎉 Déploiement Terminé !

Votre **Station Traffeyère IoT/AI Platform** est maintenant déployée et opérationnelle ! 

🌐 **Accès Principal** : https://traffeyere-station.fr
📊 **Monitoring** : https://grafana.traffeyere-station.fr

Félicitations ! 🚀