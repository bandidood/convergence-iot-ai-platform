# Guide de Déploiement Coolify - Station Traffeyère IoT/AI Platform

## 📋 Version Optimisée

Votre `docker-compose.yml` a été remplacé par la version optimisée pour Coolify avec :
- **15 services essentiels** au lieu de 20+ services complets
- **Architecture complète** maintenue (IoT, AI, monitoring, sécurité)
- **Taille réduite** pour éviter les limites de Coolify
- **Variables d'environnement** compatibles Coolify

## 🔧 Services Inclus

### Core Platform (6 services)
- **PostgreSQL** - Base de données principale
- **Redis** - Cache et sessions
- **InfluxDB** - Base de données time-series IoT
- **MinIO** - Stockage S3 compatible
- **Keycloak** - Authentification et autorisation
- **Mosquitto** - Broker MQTT IoT

### Monitoring & Observability (2 services)
- **Prometheus** - Collecte de métriques
- **Grafana** - Dashboards et visualisation

### AI & Applications (4 services)
- **Edge AI** - Engine d'intelligence artificielle
- **XAI Dashboard** - Interface d'IA explicable avec SHAP/LIME
- **Backend** - API FastAPI
- **Frontend** - Interface utilisateur React

### Security & Analytics (3 services)
- **Elasticsearch** - SIEM et recherche
- **Kibana** - Interface SIEM et analytics

## 🌍 Variables d'Environnement Coolify

Configurez ces variables dans l'interface Coolify :

### Database & Cache
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=station_traffeyere
REDIS_PASSWORD=your_redis_password
```

### InfluxDB
```bash
INFLUX_ADMIN_TOKEN=your_influx_admin_token
INFLUX_BUCKET=station_traffeyere
INFLUX_ORG=traffeyere
```

### Storage MinIO
```bash
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_minio_password
```

### Authentication Keycloak
```bash
KEYCLOAK_ADMIN_PASSWORD=your_keycloak_admin_password
KEYCLOAK_DB_PASSWORD=your_keycloak_db_password
```

### Monitoring
```bash
GRAFANA_ADMIN_PASSWORD=your_grafana_password
GRAFANA_DB_PASSWORD=your_grafana_db_password
```

### Application Secrets
```bash
SECRET_KEY=your_application_secret_key
JWT_SECRET=your_jwt_secret_key
STATION_ID=TRAFFEYERE_001
```

## 🚀 Déploiement sur Coolify

### 1. Préparation
```bash
# Vérifiez que la syntaxe est correcte
docker-compose config --quiet

# Sauvegarde créée automatiquement
# docker-compose.backup.yml contient l'ancienne version
```

### 2. Dans Coolify
1. Créez un nouveau projet
2. Sélectionnez "Docker Compose" comme type de déploiement
3. Uploadez le fichier `docker-compose.yml`
4. Configurez toutes les variables d'environnement ci-dessus
5. Déployez !

### 3. Domaines suggérés
- **Frontend principal**: `traffeyere.johann-lebel.fr`
- **Backend API**: `backend-station.johann-lebel.fr`
- **Grafana**: `grafana.johann-lebel.fr`
- **Kibana SIEM**: `siem.johann-lebel.fr`
- **Edge AI**: `edge-ai.johann-lebel.fr`
- **XAI Dashboard**: `xai.johann-lebel.fr`
- **Keycloak Auth**: `auth.johann-lebel.fr`

## 📊 Architecture Complète Maintenue

Malgré la taille réduite, tous les composants essentiels sont préservés :

- ✅ **IoT Platform**: MQTT, InfluxDB, données temps réel
- ✅ **AI Engine**: Edge AI, modèles ML, détection d'anomalies  
- ✅ **Monitoring**: Prometheus + Grafana, métriques complètes
- ✅ **Security**: SIEM Elastic Stack, authentification Keycloak
- ✅ **Scalability**: Redis cache, PostgreSQL, stockage S3
- ✅ **DevOps**: Health checks, restart policies, réseaux isolés

### ✅ Service XAI Ajouté
**Nouveau service intégré** :
- **XAI Dashboard** - Interface d'IA explicable (SHAP/LIME)
- **Domaine** : `xai.johann-lebel.fr`
- **Port** : 8092
- **Fonctionnalités** : Explications d'IA, visualisations SHAP, interface conversationnelle

### 🔄 Services Temporairement Retirés

Ces services pourront être rajoutés après le déploiement initial :
- Digital Twin Unity 3D (nécessite GPU)
- AlertManager (intégré à Prometheus)
- Logstash (traitement peut se faire côté application)
- Blockchain Hyperledger Fabric (déploiement séparé recommandé)

## 🛡️ Sécurité & Production

- **Secrets**: Tous les mots de passe sont externalisés
- **Networks**: Isolation réseau entre frontend/backend/IoT
- **Health Checks**: Surveillance de tous les services critiques
- **Restart Policies**: `unless-stopped` pour haute disponibilité
- **Volumes**: Persistance de toutes les données critiques

## 📁 Fichiers de Configuration

- `docker-compose.yml` - Version optimisée active
- `docker-compose.backup.yml` - Ancienne version complète (sauvegarde)
- `docker-compose.override.yml.disabled` - Override désactivé pour Coolify

## 🎯 Prochaines Étapes

1. ✅ Déploiement de base sur Coolify
2. 🔄 Configuration des domaines SSL
3. 🔄 Import des dashboards Grafana
4. 🔄 Configuration des alertes
5. 🔄 Tests de bout en bout
6. 🔄 Ajout progressif des services avancés

## 🛠️ Corrections Appliquées

### ❌ Problème Résolu: Variable `$SYS` 
**Erreur**: `failed to read /artifacts/.env: line 41: unexpected character "$" in variable name "$SYS="`

**Solution appliquée**:
- ✅ Fichiers `.env` problématiques désactivés
- ✅ Nouveau fichier `.env` minimal et propre créé
- ✅ Fichier `docker-compose.override.yml` désactivé
- ✅ Variables d'environnement conformes aux standards POSIX

### ❌ Problème Résolu: Chemin Edge AI
**Erreur**: `lstat /artifacts/.../services/edge-ai: no such file or directory`

**Solution appliquée**:
- ✅ Correction chemin Dockerfile: `./core/edge-ai-engine/Dockerfile.simple`
- ✅ Dockerfile simplifié sans CUDA pour compatibilité Coolify
- ✅ Chemins COPY corrigés pour contexte de build racine
- ✅ Image Python standard au lieu de nvidia/cuda

**Fichiers modifiés**:
- `.env` → Nouveau fichier minimal
- `.env.local.backup` → Ancien fichier sauvegardé
- `.env.coolify.example.disabled` → Exemple désactivé
- `docker-compose.override.yml.disabled` → Override désactivé
- `docker-compose.yml` → Chemin edge-ai corrigé
- `core/edge-ai-engine/Dockerfile.simple` → Version Coolify créée

---

**Status**: ✅ Prêt pour déploiement Coolify
**Version**: Optimisée 15 services
**Validation**: `docker-compose config` ✅ Passé
**Correction**: Problème `$SYS` ✅ Résolu
