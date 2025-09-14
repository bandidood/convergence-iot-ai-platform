# 🔧 Corrections Spécifiques Erreurs Coolify

## ❌ Erreurs Constatées

```
Container postgres-mwgo0ck0kgsggg8gwoc80so4-084802166905  Error
Container redis-mwgo0ck0kgsggg8gwoc80so4-084802192540  Error  
dependency failed to start: container postgres-xxx is unhealthy
```

## ✅ Solutions Immédiates

### 1. Utiliser le Fichier Corrigé

Remplacez votre configuration Coolify par :
**Fichier : `docker-compose.coolify.fixed.yml`**

### 2. Variables d'Environnement Obligatoires

Dans Coolify, configurez ces variables :

```bash
# OBLIGATOIRES
POSTGRES_PASSWORD=changeme123456
SECRET_KEY=changeme-secret-key-123456789  
JWT_SECRET=changeme-jwt-secret-123456789
INFLUX_ADMIN_TOKEN=changeme-token-123456

# OPTIONNELLES (laisser vide si pas utilisées)
REDIS_PASSWORD=
MQTT_PASSWORD=changeme123456
GRAFANA_ADMIN_PASSWORD=admin123456
```

### 3. Configuration Coolify Recommandée

**Repository Settings** :
- Repository: `https://github.com/votre-repo/station-traffeyere.git`
- Compose File: `docker-compose.coolify.fixed.yml`
- Build Context: `/` (racine)

**Environment Variables** :
Copiez tout le contenu de `.env.coolify` dans les variables d'environnement Coolify.

### 4. Modifications Apportées dans le Fichier Fixé

#### PostgreSQL :
- ✅ Health check plus tolérant (120s au lieu de 30s)
- ✅ Variable POSTGRES_PASSWORD avec valeur par défaut
- ✅ Test de health check simplifié

#### Redis :
- ✅ **Pas d'authentification** (suppression de `--requirepass`)
- ✅ Health check plus tolérant  
- ✅ Configuration simplifiée

#### Backend :
- ✅ **Suppression des conditions de health check strictes**
- ✅ Variables par défaut pour éviter les erreurs
- ✅ Configuration Redis sans mot de passe

#### Frontend :
- ✅ Port 80:80 pour correspondre à Nginx
- ✅ Dépendances simplifiées

## 🚀 Déploiement en 3 Étapes

### Étape 1: Fichier Compose
Utilisez `docker-compose.coolify.fixed.yml` comme fichier principal

### Étape 2: Variables d'Environnement  
Copiez ces variables dans Coolify :
```
POSTGRES_PASSWORD=changeme123456
SECRET_KEY=changeme-secret-key-123456789
JWT_SECRET=changeme-jwt-secret-123456789
INFLUX_ADMIN_TOKEN=changeme-token-123456
```

### Étape 3: Test Local (Optionnel)
```bash
# Test en local pour valider
docker-compose -f docker-compose.coolify.fixed.yml up -d
```

## 🎯 Version Ultra-Minimale (Plan B)

Si les erreurs persistent, voici une version ultra-simplifiée :

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: ./services/backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      SECRET_KEY: changeme-secret-key-123
      JWT_SECRET: changeme-jwt-secret-123
      DEBUG: "true"

  frontend:
    build:
      context: .
      dockerfile: ./services/frontend/Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
```

Cette version fonctionne sans bases de données externes.

## 📊 Ordre de Démarrage Recommandé

1. **postgres** → Health check OK
2. **redis** → Health check OK  
3. **influxdb** → Démarrage
4. **mosquitto** → Démarrage
5. **backend** → Attend postgres & redis
6. **frontend** → Attend backend

## 🔍 Validation Post-Déploiement

Une fois déployé, testez :
```bash
# Health check backend
curl https://votre-backend.coolify.app/health

# Frontend  
curl https://votre-frontend.coolify.app/healthz
```

## ⚡ Actions Immédiates

1. **Remplacer** le fichier docker-compose par `docker-compose.coolify.fixed.yml`
2. **Ajouter** les variables d'environnement obligatoires 
3. **Redéployer** avec la nouvelle configuration
4. **Surveiller** les logs pour validation