# Docker Compose Microservices - Station Traffeyère IoT/AI Platform

## Vue d'ensemble

Cette architecture modulaire sépare la plateforme Station Traffeyère en microservices indépendants pour faciliter le déploiement, la maintenance et la scalabilité.

## Structure des Services

```
docker-compose/
├── docker-compose.infrastructure.yml    # Couche Infrastructure
├── docker-compose.application.yml       # Couche Application  
├── docker-compose.monitoring.yml        # Couche Monitoring
├── docker-compose.iot.yml              # Couche IoT
├── docker-compose.security.yml         # Couche Sécurité
├── docker-compose.blockchain.yml       # Couche Blockchain
└── docker-compose.env.example          # Variables d'environnement
```

## Déploiement par Couches

### 1. Infrastructure (Base de données, Cache, Storage)
```bash
# Démarrer l'infrastructure
docker-compose -f docker-compose.infrastructure.yml up -d

# Services inclus:
# - PostgreSQL + TimescaleDB (port 5432)
# - Redis Cache (port 6379)
# - InfluxDB (port 8086)
# - MinIO S3 Storage (ports 9000, 9001)
# - MQTT Mosquitto (ports 1883, 8083)
```

### 2. Application (Backend, Frontend, IA)
```bash
# Démarrer les applications (nécessite infrastructure)
docker-compose -f docker-compose.application.yml up -d

# Services inclus:
# - Backend FastAPI (port 8000)
# - Edge AI Engine (port 8001)
# - Frontend React (port 3080)
# - XAI Dashboard (port 8092)
```

### 3. Monitoring (Observabilité)
```bash
# Démarrer le monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Services inclus:
# - Prometheus (port 9090)
# - Grafana (port 3000)
# - AlertManager (port 9093)
# - Node Exporter (port 9100)
# - cAdvisor (port 8080)
# - Loki + Promtail (port 3100)
```

### 4. IoT (Simulateurs et générateurs)
```bash
# Démarrer les simulateurs IoT
docker-compose -f docker-compose.iot.yml up -d

# Services inclus:
# - IoT Data Generator (127 capteurs)
# - Secure Station Simulator
# - Legacy System Simulator (port 5020)
# - Test Simulator (profile test/dev)
```

### 5. Sécurité (SIEM, SOC, Compliance)
```bash
# Démarrer la sécurité
docker-compose -f docker-compose.security.yml up -d

# Services inclus:
# - Elasticsearch (port 9200)
# - Kibana SIEM (port 5601)
# - SOC Dashboard (port 3001)
# - HashiCorp Vault (port 8200)
# - Wazuh Manager (ports 1514, 1515, 55000)
# - NGINX Security Proxy (ports 443, 8443)
```

### 6. Blockchain (Hyperledger Fabric)
```bash
# Démarrer la blockchain
docker-compose -f docker-compose.blockchain.yml up -d

# Services inclus:
# - 3 Orderers RAFT (ports 7050, 8050, 9050)
# - Peer0 SAUR + CouchDB (ports 7051, 5984)
# - Peer0 Regulator + CouchDB (ports 9051, 6984)
# - Blockchain API Gateway (port 8090)
```

## Configuration des Variables d'Environnement

### Fichier .env requis
```bash
# Base de données
POSTGRES_PASSWORD=votre_password_postgres
REDIS_PASSWORD=votre_password_redis
INFLUX_PASSWORD=votre_password_influx
INFLUX_ADMIN_TOKEN=votre_token_influx

# MinIO S3
MINIO_ROOT_PASSWORD=votre_password_minio

# Sécurité
SECRET_KEY=votre_secret_key_32_chars
JWT_SECRET=votre_jwt_secret_key
GRAFANA_ADMIN_PASSWORD=votre_password_grafana

# MQTT
MQTT_PASSWORD=votre_password_mqtt

# Elasticsearch
ELASTIC_PASSWORD=votre_password_elastic
KIBANA_ENCRYPTION_KEY=votre_encryption_key_32_chars

# Vault
VAULT_ROOT_TOKEN=votre_vault_token

# Wazuh
WAZUH_ADMIN_PASSWORD=votre_password_wazuh

# Alerting
SLACK_WEBHOOK_SECURITY=https://hooks.slack.com/services/...
SMTP_PASSWORD=votre_password_smtp
```

## Réseaux Partagés

Les services communiquent via des réseaux Docker partagés :

- **traffeyere-backend** : Communication interne des services
- **traffeyere-frontend** : Services publics (web, API)
- **traffeyere-iot** : Communication IoT et capteurs  
- **traffeyere-monitoring** : Stack d'observabilité
- **traffeyere-security** : Services de sécurité isolés
- **traffeyere-blockchain** : Réseau Hyperledger Fabric

## Commandes de Gestion

### Démarrage complet par étapes
```bash
# 1. Infrastructure (obligatoire en premier)
docker-compose -f docker-compose.infrastructure.yml up -d

# 2. Application (attend infrastructure)
docker-compose -f docker-compose.application.yml up -d

# 3. Monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# 4. IoT (optionnel)
docker-compose -f docker-compose.iot.yml up -d

# 5. Sécurité (optionnel)
docker-compose -f docker-compose.security.yml up -d

# 6. Blockchain (optionnel)
docker-compose -f docker-compose.blockchain.yml up -d
```

### Arrêt sélectif
```bash
# Arrêter seulement les simulateurs IoT
docker-compose -f docker-compose.iot.yml down

# Arrêter la blockchain sans affecter les autres
docker-compose -f docker-compose.blockchain.yml down

# Arrêter tout sauf l'infrastructure
docker-compose -f docker-compose.application.yml down
docker-compose -f docker-compose.monitoring.yml down
```

### Mise à l'échelle
```bash
# Scaler l'edge AI engine
docker-compose -f docker-compose.application.yml up -d --scale edge-ai-engine=3

# Scaler les générateurs IoT
docker-compose -f docker-compose.iot.yml up -d --scale iot-data-generator=2
```

### Logs et debugging
```bash
# Logs d'un service spécifique
docker-compose -f docker-compose.application.yml logs -f backend

# Status de tous les services d'une couche
docker-compose -f docker-compose.monitoring.yml ps

# Restart d'un service
docker-compose -f docker-compose.application.yml restart edge-ai-engine
```

## Volumes Persistants

### Données critiques
- **postgres_data** : Base de données principale
- **influxdb_data** : Métriques IoT haute fréquence
- **minio_data** : Modèles IA et fichiers
- **redis_data** : Cache applicatif

### Logs et monitoring
- **backend_logs, edge_ai_logs** : Logs applicatifs
- **prometheus_data** : Métriques (30 jours)
- **grafana_data** : Dashboards et configuration
- **elasticsearch_data** : Événements sécurité

### Blockchain
- **orderer0_data, peer0_saur_data** : Ledger blockchain
- **couchdb0_saur_data** : État des smart contracts

## Health Checks et Monitoring

Tous les services incluent des health checks :
- **Interval** : 20-30s selon la criticité
- **Timeout** : 5-15s selon la complexité
- **Start period** : 30-120s selon le temps de démarrage
- **Retries** : 3-5 tentatives

## Ressources et Limitations

### Limites par défaut
- **Infrastructure** : 1-2G RAM par service DB
- **Application** : 512M-2G selon la charge
- **IoT** : 128-512M pour les simulateurs
- **Monitoring** : 256M-1G selon les métriques
- **Sécurité** : 1-3G pour Elasticsearch
- **Blockchain** : 256-512M par peer/orderer

### Optimisation
- Ajuster `deploy.resources` selon l'environnement
- Utiliser des profiles pour dev/test/prod
- Scaler horizontalement les services sans état

## Troubleshooting

### Problèmes courants
1. **Erreur de réseau** : Vérifier que l'infrastructure est démarrée
2. **Timeout de démarrage** : Augmenter `start_period` dans les health checks
3. **Problème de volumes** : Vérifier les permissions et l'espace disque
4. **Configuration manquante** : Copier et adapter le fichier .env.example

### Logs utiles
```bash
# Logs complets d'une couche
docker-compose -f docker-compose.infrastructure.yml logs

# Logs en temps réel
docker-compose -f docker-compose.application.yml logs -f --tail=100

# Inspection d'un service
docker inspect traffeyere-backend
```

Cette architecture modulaire permet une gestion fine des services selon les besoins de déploiement, test et production.