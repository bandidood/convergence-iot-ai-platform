# 🖥️ Guide de Test Local Windows - Station Traffeyère IoT/AI Platform

## 🎯 Objectif
Tester l'ensemble de la plateforme localement sous Windows avant le déploiement Linux/Coolify.

## 📋 Prérequis

### Logiciels Requis
- ✅ **Docker Desktop** pour Windows (avec WSL2)
- ✅ **Docker Compose** v2.0+
- ✅ **Git** pour Windows
- ✅ **PowerShell** 5.1+
- ✅ **Navigateur Web** moderne

### Vérification de l'Environnement
```powershell
# Vérifier Docker
docker --version
docker-compose --version

# Vérifier que Docker fonctionne
docker run hello-world

# Vérifier l'espace disque (minimum 10GB libres)
Get-PSDrive C
```

## 🚀 Démarrage de la Stack Complète

### Étape 1: Préparation
```powershell
# Se placer dans le répertoire du projet
cd C:\Users\joh_l\station-traffeyere-iot-ai-platform\station-traffeyere-iot-ai-platform

# Copier les variables d'environnement
Copy-Item .env.local .env

# Vérifier les fichiers nécessaires
ls docker-compose.local.yml
ls config/prometheus.yml
ls services/backend/Dockerfile
ls services/frontend/Dockerfile
```

### Étape 2: Construction et Démarrage
```powershell
# Construire les images personnalisées
docker-compose -f docker-compose.local.yml build

# Démarrer tous les services
docker-compose -f docker-compose.local.yml up -d

# Surveiller les logs en temps réel (optionnel)
docker-compose -f docker-compose.local.yml logs -f
```

### Étape 3: Vérification du Démarrage
```powershell
# Vérifier que tous les conteneurs sont up
docker-compose -f docker-compose.local.yml ps

# Surveiller les health checks
docker-compose -f docker-compose.local.yml ps --format table
```

## 🔍 Tests de Validation

### 🔧 Services Core

#### Backend FastAPI (Port 8000)
```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Documentation API
Start-Process "http://localhost:8000/api/docs"

# Version et informations
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/info"
```

#### Frontend React (Port 3000)
```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:3000/healthz"

# Page d'accueil dans le navigateur
Start-Process "http://localhost:3000"

# Vérifier le dashboard IoT
Start-Process "http://localhost:3000/dashboard"
```

#### PostgreSQL (Port 5432)
```powershell
# Test de connexion via psql (si installé)
# psql -h localhost -p 5432 -U postgres -d station_traffeyere

# Ou via Docker
docker exec -it station-traffeyere-iot-ai-platform-postgres-1 psql -U postgres -d station_traffeyere -c "\l"
```

#### Redis (Port 6379)
```powershell
# Test de connexion
docker exec -it station-traffeyere-iot-ai-platform-redis-1 redis-cli ping
```

### 📊 Services IoT/Monitoring

#### InfluxDB (Port 8086)
```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8086/health"

# Interface web
Start-Process "http://localhost:8086"
# Login: admin / StationTraffeyereInflux2024
```

#### MQTT Mosquitto (Ports 1883, 9001)
```powershell
# Test MQTT via Docker (publish/subscribe)
# Terminal 1: Subscribe
docker run -it --rm --network station-traffeyere-iot-ai-platform_default eclipse-mosquitto:2.0 mosquitto_sub -h mosquitto -t "test/topic"

# Terminal 2: Publish
docker run -it --rm --network station-traffeyere-iot-ai-platform_default eclipse-mosquitto:2.0 mosquitto_pub -h mosquitto -t "test/topic" -m "Hello IoT Platform!"
```

#### Grafana (Port 3001)
```powershell
# Interface de monitoring
Start-Process "http://localhost:3001"
# Login: admin / admin
```

#### Prometheus (Port 9090)
```powershell
# Interface de métriques
Start-Process "http://localhost:9090"

# Vérifier les targets
Start-Process "http://localhost:9090/targets"
```

#### Node Exporter (Port 9100)
```powershell
# Métriques système
Invoke-RestMethod -Uri "http://localhost:9100/metrics" | Select-String "node_cpu"
```

## 📊 Dashboard de Validation Complète

### Checklist des Services
```bash
✅ Backend FastAPI      → http://localhost:8000/health
✅ Frontend React       → http://localhost:3000/healthz  
✅ PostgreSQL          → docker exec postgres psql test
✅ Redis               → docker exec redis redis-cli ping
✅ InfluxDB            → http://localhost:8086/health
✅ MQTT Mosquitto      → Test pub/sub
✅ Grafana             → http://localhost:3001 (admin/admin)
✅ Prometheus          → http://localhost:9090/targets
✅ Node Exporter       → http://localhost:9100/metrics
```

### URLs d'Interface Web
| Service | URL | Login |
|---------|-----|-------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000/api/docs | - |
| **InfluxDB** | http://localhost:8086 | admin/StationTraffeyereInflux2024 |
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |

## 🧪 Tests Fonctionnels Avancés

### Test IoT End-to-End
```powershell
# 1. Publier des données IoT via MQTT
$message = '{"sensor_id": "TEMP_001", "value": 23.5, "timestamp": "2025-09-14T10:00:00Z"}'
docker run -it --rm --network station-traffeyere-iot-ai-platform_default eclipse-mosquitto:2.0 mosquitto_pub -h mosquitto -t "sensors/temperature" -m $message

# 2. Vérifier dans les logs backend
docker-compose -f docker-compose.local.yml logs backend | Select-String "sensor"

# 3. Consulter dans InfluxDB
# Via interface web http://localhost:8086
```

### Test API Backend
```powershell
# Créer un capteur fictif
$sensor = @{
    id = "TEMP_001"
    name = "Température Hall"
    type = "temperature"
    location = "45.764043,4.835659"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sensors" -Method POST -Body $sensor -ContentType "application/json"

# Lister les capteurs
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sensors"
```

## 🐛 Dépannage

### Problèmes Courants

#### Services qui ne démarrent pas
```powershell
# Vérifier les logs d'erreur
docker-compose -f docker-compose.local.yml logs [service_name]

# Redémarrer un service spécifique
docker-compose -f docker-compose.local.yml restart [service_name]
```

#### Ports déjà utilisés
```powershell
# Vérifier qui utilise un port
netstat -ano | findstr ":8000"

# Arrêter tous les services
docker-compose -f docker-compose.local.yml down
```

#### Problèmes de volumes
```powershell
# Nettoyer les volumes (ATTENTION: perte des données)
docker-compose -f docker-compose.local.yml down -v

# Redémarrer proprement
docker-compose -f docker-compose.local.yml up -d
```

## 🎯 Validation Finale

### Critères de Réussite
- ✅ Tous les services démarrent sans erreur
- ✅ Les health checks retournent OK
- ✅ Les interfaces web sont accessibles
- ✅ Les logs ne montrent pas d'erreurs critiques
- ✅ La communication inter-services fonctionne

### Performance Attendue
- ✅ Démarrage complet < 5 minutes
- ✅ Temps de réponse backend < 100ms
- ✅ Frontend responsive < 2 secondes
- ✅ Utilisation mémoire < 4GB total

## ➡️ Étape Suivante: Production Linux

Une fois tous les tests locaux validés, nous pourrons :

1. ✅ Adapter la configuration pour Coolify (suppression des ports)
2. ✅ Configurer les variables d'environnement production  
3. ✅ Déployer sur le serveur Linux
4. ✅ Configurer les domaines et SSL

**Temps estimé de validation locale : 30-45 minutes** 🕐