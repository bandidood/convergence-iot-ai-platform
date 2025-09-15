# 🚨 RÉSOLUTION GATEWAY TIMEOUT 504 - COOLIFY

## 🔍 **DIAGNOSTIC PROBLÈME**

Le gateway timeout 504 nginx indique que vos services mettent **trop de temps** à démarrer ou consomment **trop de ressources** simultanément.

### **Services Problématiques Identifiés :**

| Service | Temps Démarrage | RAM Utilisée | Problème |
|---------|-----------------|--------------|-----------|
| 🐘 **Elasticsearch** | 120-300s | 1-2GB | JVM + indexation |
| 🧠 **XAI Dashboard** | 60-120s | 512MB-1GB | ML dependencies |
| 🔐 **Keycloak** | 60-180s | 512MB-1GB | JVM + DB init |
| 🎯 **Edge AI** | 45-90s | 256-512MB | TensorFlow build |
| 📊 **Kibana** | 90-240s | 512MB | Attente Elasticsearch |

---

## ✅ **SOLUTION 1 : DÉPLOIEMENT PROGRESSIF (RECOMMANDÉ)**

### **🚀 ÉTAPE 1 - Version Light (9 services)**
```bash
# Déployez d'abord la version allégée
docker-compose -f docker-compose.light.yml up -d
```

**Services inclus** : PostgreSQL, Redis, InfluxDB, Mosquitto, Prometheus, Grafana, Backend, Frontend
**Temps de démarrage** : < 60 secondes
**RAM requise** : ~2GB

### **🔧 ÉTAPE 2 - Ajout services AI (après succès étape 1)**
Une fois la version light fonctionnelle, ajoutez :
- MinIO (stockage)
- Edge AI (IA)
- XAI Dashboard (IA explicable)

### **📊 ÉTAPE 3 - Ajout monitoring avancé**
Enfin, ajoutez les services lourds :
- Elasticsearch
- Kibana  
- Keycloak

---

## ✅ **SOLUTION 2 : OPTIMISATIONS APPLIQUÉES**

### **🔧 Health Checks Optimisés**

| Service | Ancien | Nouveau | Amélioration |
|---------|---------|---------|-------------|
| **Elasticsearch** | start_period: 60s | start_period: 300s | +400% |
| **Keycloak** | start_period: 60s | start_period: 180s | +200% |
| **Kibana** | start_period: 60s | start_period: 240s | +300% |
| **Edge AI** | start_period: 30s | start_period: 120s | +300% |
| **XAI Dashboard** | start_period: 30s | start_period: 150s | +400% |

### **🧠 Réduction Mémoire Elasticsearch**
```yaml
# Avant : 1GB RAM
- "ES_JAVA_OPTS=-Xms1g -Xmx1g"

# Après : 512MB RAM  
- "ES_JAVA_OPTS=-Xms512m -Xmx512m"
- bootstrap.memory_lock=false
```

### **⚡ Health Check Moins Agressif**
```yaml
# Avant : Vérifications toutes les 30s
interval: 30s
timeout: 10s
retries: 3

# Après : Vérifications plus espacées
interval: 45-60s
timeout: 15-20s  
retries: 8-15
```

---

## ✅ **SOLUTION 3 : RECOMMANDATIONS COOLIFY**

### **🛠️ Configuration Coolify**

1. **Augmenter Timeout Nginx** dans Coolify :
   ```
   Coolify → Settings → Proxy → Nginx Timeout: 300s
   ```

2. **Ressources Serveur Recommandées** :
   - **CPU** : Minimum 4 vCPU  
   - **RAM** : Minimum 8GB (16GB recommandé)
   - **Stockage** : SSD 50GB minimum

3. **Variables d'Environnement** - Ajoutez dans Coolify :
   ```bash
   # Optimisations JVM
   JAVA_OPTS="-Xms256m -Xmx512m"
   
   # Timeouts applicatifs
   APP_STARTUP_TIMEOUT=300
   HEALTH_CHECK_TIMEOUT=60
   ```

---

## 🚀 **PROCÉDURE DE DÉPLOIEMENT RECOMMANDÉE**

### **Phase 1 : Core Platform (Immédiat)**
```bash
# 1. Remplacez votre docker-compose.yml actuel
cp docker-compose.light.yml docker-compose.yml

# 2. Déployez sur Coolify
# ✅ 9 services essentiels - démarrage rapide garanti
```

### **Phase 2 : AI Services (Après validation Phase 1)**  
```bash
# Ajoutez progressivement :
# - MinIO (stockage)
# - Edge AI (intelligence artificielle)  
# - XAI Dashboard (IA explicable)
```

### **Phase 3 : Advanced Monitoring (Après validation Phase 2)**
```bash
# Ajoutez les services lourds :
# - Elasticsearch (SIEM)
# - Kibana (dashboards SIEM)
# - Keycloak (authentification)
```

---

## 🔧 **DIAGNOSTIC EN TEMPS RÉEL**

### **Commandes de Debug sur Coolify :**

```bash
# 1. Vérifier status des containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Vérifier les logs des services lents  
docker logs -f <container_name>

# 3. Vérifier la consommation ressources
docker stats --no-stream

# 4. Test health checks manuels
docker exec <container> curl -f http://localhost:<port>/health
```

### **Signaux d'Alerte :**
- ❌ Container **Restarting (1)** = Health check failure
- ❌ Container **Exit (125)** = Erreur configuration  
- ❌ Container **Exit (137)** = Out Of Memory (OOM)
- ⚠️ Container **Starting** > 5min = Timeout imminent

---

## 📊 **MONITORING POST-DÉPLOIEMENT**

Une fois déployé avec succès :

1. **Vérifiez les endpoints** :
   ```bash
   ✅ https://traffeyere.johann-lebel.fr (Frontend)
   ✅ https://backend-station.johann-lebel.fr/health (Backend)
   ✅ https://grafana.johann-lebel.fr (Monitoring)
   ```

2. **Surveillez les métriques** :
   - Temps de réponse < 500ms
   - CPU < 70% 
   - RAM < 80%
   - Disk I/O < 80%

3. **Tests de charge** :
   ```bash
   # Test simple endpoint
   curl -w "@curl-format.txt" https://backend-station.johann-lebel.fr/health
   
   # Test WebSocket temps réel
   wscat -c wss://backend-station.johann-lebel.fr/ws
   ```

---

## 🎯 **RÉSUMÉ ACTIONS IMMÉDIATES**

1. ✅ **Utilisez docker-compose.light.yml** pour le premier déploiement
2. ✅ **Validez que la version light fonctionne** (9 services)
3. ✅ **Ajoutez progressivement** les services AI puis monitoring
4. ✅ **Surveillez les ressources** serveur pendant le déploiement
5. ✅ **Configurez les timeouts** nginx dans Coolify

**Avec cette approche progressive, le timeout 504 sera évité !** 🚀