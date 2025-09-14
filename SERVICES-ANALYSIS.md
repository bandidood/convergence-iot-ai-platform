# 📊 Analyse Complète des Services - Station Traffeyère IoT/AI Platform

## 🎯 Services et Configuration Ports/URLs

### 🔧 **Services Core (Obligatoires)**

| Service | Port Local | URL Local | Description | Besoin URL Spécifique |
|---------|------------|-----------|-------------|----------------------|
| **Backend FastAPI** | 8000 | http://localhost:8000 | API REST + WebSocket + IA | ✅ `/health`, `/api/docs` |
| **Frontend React** | 3000 | http://localhost:3000 | Interface utilisateur | ✅ `/healthz` |
| **PostgreSQL** | 5432 | N/A (interne) | Base de données principale | ❌ |
| **Redis** | 6379 | N/A (interne) | Cache haute performance | ❌ |

### 📊 **Services IoT/Monitoring (Optionnels)**

| Service | Port Local | URL Local | Description | Besoin URL Spécifique |
|---------|------------|-----------|-------------|----------------------|
| **InfluxDB** | 8086 | http://localhost:8086 | Base de données temporelle | ✅ `/health` |
| **MQTT Mosquitto** | 1883, 9001 | N/A, ws://localhost:9001 | Message broker IoT | ✅ WebSocket |
| **Grafana** | 3001 | http://localhost:3001 | Monitoring dashboards | ✅ Login admin |
| **Prometheus** | 9090 | http://localhost:9090 | Collecte de métriques | ✅ `/targets` |
| **Node Exporter** | 9100 | http://localhost:9100 | Métriques système | ✅ `/metrics` |

## 🏠 **Configuration Locale Windows**

### docker-compose.local.yml
```yaml
services:
  # Core Services
  postgres:     # Port 5432 (interne)
  redis:        # Port 6379 (interne)
  backend:      # Port 8000 → http://localhost:8000
  frontend:     # Port 3000 → http://localhost:3000
  
  # IoT/Monitoring Services  
  influxdb:     # Port 8086 → http://localhost:8086
  mosquitto:    # Port 1883 (MQTT), 9001 (WebSocket)
  grafana:      # Port 3001 → http://localhost:3001
  prometheus:   # Port 9090 → http://localhost:9090
  node-exporter: # Port 9100 → http://localhost:9100
```

### URLs de Test Local
```bash
# Services Core
http://localhost:8000/health          # Backend health
http://localhost:8000/api/docs        # API documentation
http://localhost:3000                 # Frontend
http://localhost:3000/healthz         # Frontend health

# Services IoT/Monitoring
http://localhost:8086/health          # InfluxDB
http://localhost:3001                 # Grafana (admin/admin)
http://localhost:9090                 # Prometheus
http://localhost:9100/metrics         # Node Exporter
```

## 🐧 **Configuration Serveur Linux (Coolify)**

### Adaptation pour Production
```yaml
services:
  # Core Services (sans ports exposés)
  postgres:     # Interne seulement
  redis:        # Interne seulement  
  backend:      # Reverse proxy → https://api.domain.com
  frontend:     # Reverse proxy → https://app.domain.com
  
  # Services optionnels
  influxdb:     # Reverse proxy → https://influx.domain.com
  grafana:      # Reverse proxy → https://monitoring.domain.com
```

### URLs Production (Coolify)
```bash
# Services Core
https://api.traffeyere.domain.com     # Backend
https://app.traffeyere.domain.com     # Frontend

# Services Monitoring (optionnels)
https://influx.traffeyere.domain.com  # InfluxDB
https://grafana.traffeyere.domain.com # Grafana
```

## 🔄 **Migration Windows → Linux**

### Différences Clés
| Aspect | Windows Local | Linux Coolify |
|--------|---------------|---------------|
| **Ports** | Exposés (3000, 8000, etc.) | Reverse proxy |
| **SSL/TLS** | HTTP simple | HTTPS automatique |
| **Volumes** | Windows paths | Linux volumes |
| **Networks** | Bridge simple | Overlay/custom |

### Adaptations Nécessaires
1. **Suppression des ports exposés**
2. **Variables d'environnement** (secrets)
3. **Paths volumes** Windows → Linux
4. **URLs internes** (backend communication)

## 📋 **Plan de Déploiement**

### Phase 1: Test Local Windows ✅
```bash
# 1. Docker Compose local complet
docker-compose -f docker-compose.local.yml up -d

# 2. Test de tous les services
curl http://localhost:8000/health      # Backend
curl http://localhost:3000/healthz     # Frontend
curl http://localhost:8086/health      # InfluxDB

# 3. Validation interface web
# Ouvrir http://localhost:3000 dans le navigateur
# Ouvrir http://localhost:3001 pour Grafana
```

### Phase 2: Adaptation Linux 🚀
```bash
# 1. Créer docker-compose.production.yml
# 2. Supprimer les ports exposés
# 3. Configurer les variables d'environnement
# 4. Tester sur Coolify
```

## 🎯 **Services Recommandés par Priorité**

### 🔥 **Phase 1 - Minimal Viable Product**
1. **Backend FastAPI** (8000) - API core
2. **Frontend React** (3000) - Interface utilisateur
3. **PostgreSQL** (5432) - Base de données
4. **Redis** (6379) - Cache

### ⚡ **Phase 2 - IoT Features**
5. **InfluxDB** (8086) - Données temporelles IoT
6. **MQTT Mosquitto** (1883, 9001) - Communication IoT

### 📊 **Phase 3 - Monitoring Complete**
7. **Grafana** (3001) - Dashboards
8. **Prometheus** (9090) - Métriques
9. **Node Exporter** (9100) - Métriques système

## 🔧 **URLs Spécifiques Nécessaires**

### Backend (Port 8000)
- `/health` - Health check
- `/api/docs` - Documentation Swagger
- `/api/v1/*` - API endpoints
- `/ws` - WebSocket connections

### Frontend (Port 3000)
- `/` - Page d'accueil
- `/healthz` - Health check
- `/dashboard` - Tableau de bord IoT

### InfluxDB (Port 8086)
- `/health` - Health check
- `/api/v2/*` - API InfluxDB

### Grafana (Port 3001)
- `/login` - Interface de connexion
- `/api/health` - Health check

### Prometheus (Port 9090)
- `/targets` - État des targets
- `/metrics` - Métriques internes

## ⚡ **Prochaines Étapes**

1. **Créer docker-compose.local.yml** pour Windows
2. **Tester localement** tous les services
3. **Valider** les URLs et health checks
4. **Créer docker-compose.production.yml** adapté Linux
5. **Déployer** sur Coolify avec reverse proxy