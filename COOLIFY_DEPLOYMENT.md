# 🚀 Guide de Déploiement Coolify - Station Traffeyère IoT/AI Platform

## 📋 Prérequis

- Serveur avec **Coolify installé** (https://coolify.io)
- **Docker** et **Docker Compose** disponibles
- **Domaines configurés** dans votre DNS (optionnel, peut être configuré dans Coolify)

## 🔧 Étapes de Déploiement

### 1. **Préparation du Repository**
```bash
git add .
git commit -m "🚀 Configuration Docker Compose pour Coolify"
git push origin main
```

### 2. **Configuration dans Coolify**

#### A. **Créer un nouveau projet**
1. Connectez-vous à votre interface Coolify
2. Créez un nouveau **Resource** > **Docker Compose**
3. Connectez votre repository Git

#### B. **Configuration Git**
- **Repository**: `https://github.com/bandidood/convergence-iot-ai-platform.git`
- **Branch**: `main` ou `master`
- **Docker Compose Path**: `docker-compose.yml` (racine)

### 3. **Variables d'Environnement** ⚙️

Configurez ces variables dans l'interface Coolify :

#### **🔐 Variables Obligatoires**
```env
POSTGRES_PASSWORD=VotreMotDePasseSecure123!
REDIS_PASSWORD=VotreRedisPassword123!
SECRET_KEY=VotreCleSecrete32CaracteresMinimum!
JWT_SECRET=VotreJWTSecret32CaracteresMinimum!
INFLUX_PASSWORD=VotreInfluxPassword123!
INFLUX_ADMIN_TOKEN=VotreTokenInflux64Caracteres!
```

#### **📊 Variables Optionnelles**
```env
# Configuration Personnalisée
POSTGRES_DB=station_traffeyere
POSTGRES_USER=postgres
INFLUX_USERNAME=admin
INFLUX_ORG=traffeyere
INFLUX_BUCKET=iot_sensors

# Grafana
GRAFANA_ADMIN_PASSWORD=VotreGrafanaPassword123!
GRAFANA_DB_PASSWORD=VotreGrafanaDBPassword123!

# MQTT
MQTT_USERNAME=iot_user
MQTT_PASSWORD=VotreMQTTPassword123!

# Station
STATION_ID=TRAFFEYERE_001
STATION_NAME=Station Traffeyère
STATION_LOCATION=45.764043,4.835659
```

### 4. **Configuration des Domaines** 🌐

Dans Coolify, configurez les domaines pour chaque service :

- **Frontend**: `traffeyere.ccdigital.fr` (port 3000)
- **Backend API**: `api.traffeyere.ccdigital.fr` (port 8000) 
- **Grafana**: `grafana.traffeyere.ccdigital.fr` (port 3001)
- **Prometheus**: `prometheus.traffeyere.ccdigital.fr` (port 9090)
- **InfluxDB**: `influx.traffeyere.ccdigital.fr` (port 8086)

### 5. **Lancement du Déploiement** ▶️

1. **Sauvegardez** la configuration
2. Cliquez sur **Deploy**
3. Surveillez les logs de build
4. Attendez que tous les services soient **healthy** ✅

## 📊 Services Déployés

### **🏗️ Architecture Complète RNCP 39394**

| Service | Port | Description | Status |
|---------|------|-------------|--------|
| **Frontend** | 3000 | Interface utilisateur Next.js | 🎨 |
| **Backend** | 8000 | API FastAPI + IA Edge | 🔧 |
| **PostgreSQL** | 5432 | Base données relationnelle + TimescaleDB | 🗄️ |
| **Redis** | 6379 | Cache et sessions | ⚡ |
| **InfluxDB** | 8086 | Base données temporelles IoT | 📈 |
| **Mosquitto** | 1883/9001 | Broker MQTT IoT | 📡 |
| **Grafana** | 3001 | Dashboard monitoring | 📊 |
| **Prometheus** | 9090 | Collecte métriques | 📋 |
| **Node Exporter** | 9100 | Métriques système | 🖥️ |

## ✅ Vérifications Post-Déploiement

### **1. Health Checks**
```bash
# Vérifier tous les services
curl https://api.traffeyere.ccdigital.fr/health
curl https://grafana.traffeyere.ccdigital.fr/api/health
```

### **2. Endpoints API Disponibles**
- **Documentation**: `https://api.traffeyere.ccdigital.fr/docs`
- **Health Check**: `https://api.traffeyere.ccdigital.fr/health`
- **Info Application**: `https://api.traffeyere.ccdigital.fr/info`
- **Capteurs IoT**: `https://api.traffeyere.ccdigital.fr/api/v1/sensors`
- **Anomalies IA**: `https://api.traffeyere.ccdigital.fr/api/v1/anomalies`

### **3. Dashboards Monitoring**
- **Grafana**: `https://grafana.traffeyere.ccdigital.fr`
  - Login: `admin` / `${GRAFANA_ADMIN_PASSWORD}`
- **Prometheus**: `https://prometheus.traffeyere.ccdigital.fr`

## 🔧 Dépannage

### **Problèmes Courants**

#### **1. Service ne démarre pas**
```bash
# Dans Coolify, vérifiez les logs
# Vérifiez les variables d'environnement
# Vérifiez les health checks
```

#### **2. Erreur de base de données**
- Vérifiez `POSTGRES_PASSWORD`
- Vérifiez la connectivité réseau
- Regardez les logs PostgreSQL

#### **3. Build échoue**
- Vérifiez que les Dockerfiles existent
- Vérifiez les chemins relatifs
- Regardez les logs de build détaillés

#### **4. Frontend ne charge pas l'API**
- Vérifiez `NEXT_PUBLIC_API_URL`
- Vérifiez que le backend est accessible
- Vérifiez la configuration CORS

## 📚 Documentation Supplémentaire

- **Architecture Technique**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **API Documentation**: Disponible à `/docs` une fois déployé
- **Variables d'Environnement**: [.env.example](./.env.example)

## 🎯 Validation RNCP 39394

Cette configuration démontre :
- ✅ **Architecture Cloud-Native** (Docker, Compose)
- ✅ **Microservices** (Services découplés)
- ✅ **IoT Integration** (MQTT, InfluxDB, TimescaleDB)
- ✅ **Edge AI** (FastAPI + ML)
- ✅ **Monitoring** (Prometheus, Grafana)
- ✅ **Sécurité** (Variables chiffrées, Health checks)
- ✅ **DevOps** (CI/CD ready, Infrastructure as Code)

---

## 🆘 Support

En cas de problème, vérifiez :
1. **Logs Coolify** dans l'interface
2. **Variables d'environnement** correctement définies
3. **DNS/Domaines** correctement configurés
4. **Ressources serveur** suffisantes (RAM, CPU, Disk)

**Bonne chance avec votre déploiement ! 🚀**