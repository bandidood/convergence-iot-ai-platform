# 🔧 Résolution Erreurs Coolify - Station Traffeyère

## 😅 Le Problème Rencontré

Vous avez rencontré ces erreurs lors du déploiement :

```
The "DOMAIN_ROOT" variable is not set. Defaulting to a blank string.
The "GIT_REPOSITORY_URL" variable is not set. Defaulting to a blank string.
services.postgres.healthcheck.timeout must be a string
exit status 1
```

## ✅ Solutions Immédiates

### 1. Variables d'Environnement Manquantes

Les variables `DOMAIN_ROOT` et `GIT_REPOSITORY_URL` ne sont pas définies. Voici comment les configurer :

#### Option A : Via Interface Coolify

1. **Connectez-vous à votre Coolify** : `https://votre-coolify.com`
2. **Allez dans Settings > Environment Variables**
3. **Ajoutez ces variables** :

```bash
DOMAIN_ROOT=votre-domaine.com
GIT_REPOSITORY_URL=https://github.com/bandidood/convergence-iot-ai-platform.git
POSTGRES_DB=station_traffeyere
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<secret-généré>
REDIS_PASSWORD=<secret-généré>
SECRET_KEY=<secret-généré>
JWT_SECRET=<secret-généré>
GRAFANA_ADMIN_PASSWORD=<secret-généré>
```

#### Option B : Fichier .env Local

Créez ou mettez à jour votre fichier `.env` :

```bash
# Générez les secrets d'abord
./generate-secrets.sh

# Puis ajoutez ces variables
echo "DOMAIN_ROOT=votre-domaine.com" >> .env
echo "GIT_REPOSITORY_URL=https://github.com/bandidood/convergence-iot-ai-platform.git" >> .env
```

### 2. Format des Health Checks Corrigé

Le problème `timeout must be a string` est résolu dans `coolify-simple.yml`.

## 🚀 Déploiement Correct - 3 Options

### Option 1 : Via Interface Coolify (Recommandé)

```bash
# 1. Générez vos secrets
./generate-secrets.sh

# 2. Transférez les fichiers sur votre serveur Ubuntu
./deploy-to-ubuntu.ps1 -ServerIP "IP_SERVEUR" -Username "ubuntu"

# 3. Dans l'interface Coolify :
# - Créez un nouveau projet
# - Importez coolify-simple.yml
# - Définissez les variables d'environnement
# - Lancez le déploiement
```

### Option 2 : Via API Coolify (Automatisé)

```bash
# Déploiement automatisé avec variables
./deploy-to-coolify.ps1 `
  -CoolifyURL "https://votre-coolify.com" `
  -CoolifyToken "votre-token-api" `
  -ServerIP "IP_SERVEUR" `
  -Username "ubuntu" `
  -GitRepository "https://github.com/bandidood/convergence-iot-ai-platform.git"
```

### Option 3 : Docker Compose Direct

```bash
# Sur votre serveur Ubuntu
ssh ubuntu@IP_SERVEUR
cd ~/station-traffeyere

# Configurez les variables
export DOMAIN_ROOT="votre-domaine.com"
export GIT_REPOSITORY_URL="https://github.com/bandidood/convergence-iot-ai-platform.git"

# Déployez avec docker-compose
docker-compose -f coolify-simple.yml up -d
```

## 🔧 Configuration Détaillée

### Variables d'Environnement Requises

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DOMAIN_ROOT` | Votre domaine principal | `traffeyere.example.com` |
| `GIT_REPOSITORY_URL` | URL du repository | `https://github.com/bandidood/convergence-iot-ai-platform.git` |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL | Généré par script |
| `REDIS_PASSWORD` | Mot de passe Redis | Généré par script |
| `SECRET_KEY` | Clé secrète application | Généré par script |
| `JWT_SECRET` | Secret JWT | Généré par script |

### DNS Requis

Configurez ces enregistrements DNS :

```dns
votre-domaine.com         A    IP_DE_VOTRE_SERVEUR
api.votre-domaine.com     A    IP_DE_VOTRE_SERVEUR
app.votre-domaine.com     A    IP_DE_VOTRE_SERVEUR
grafana.votre-domaine.com A    IP_DE_VOTRE_SERVEUR
mqtt.votre-domaine.com    A    IP_DE_VOTRE_SERVEUR
influx.votre-domaine.com  A    IP_DE_VOTRE_SERVEUR
```

## 🆘 Dépannage Avancé

### Si l'erreur persiste

1. **Vérifiez que toutes les variables sont définies** :

```bash
# Sur le serveur Ubuntu
echo $DOMAIN_ROOT
echo $GIT_REPOSITORY_URL
```

2. **Testez la validation du fichier** :

```bash
# Validez le docker-compose
docker-compose -f coolify-simple.yml config
```

3. **Vérifiez les logs Coolify** :

```bash
# Sur le serveur Ubuntu (si Coolify est installé)
docker logs coolify
```

### Si les services ne se lancent pas

1. **Vérifiez les ressources** :

```bash
# Mémoire et espace disque
free -h
df -h
```

2. **Vérifiez Docker** :

```bash
# Status Docker
docker ps -a
docker-compose logs
```

## ✅ Validation du Déploiement

Une fois déployé, vérifiez que tout fonctionne :

### 1. Services Base

```bash
# PostgreSQL
docker exec postgres-traffeyere pg_isready

# Redis  
docker exec redis-traffeyere redis-cli ping

# InfluxDB
curl -f http://localhost:8086/health
```

### 2. Applications

```bash
# Backend API
curl -f https://api.votre-domaine.com/health

# Frontend
curl -I https://app.votre-domaine.com

# Grafana
curl -I https://grafana.votre-domaine.com
```

## 🎯 Checklist de Déploiement

- [ ] Variables d'environnement définies dans Coolify
- [ ] DNS configuré et propagé
- [ ] Certificats SSL générés automatiquement
- [ ] Tous les services "Running" dans Coolify
- [ ] Backend accessible via API
- [ ] Frontend accessible via navigateur
- [ ] Grafana accessible avec login admin
- [ ] MQTT broker fonctionnel
- [ ] InfluxDB accessible

## 🔄 Commandes de Redéploiement

Si vous devez redéployer :

```bash
# Arrêt propre
docker-compose -f coolify-simple.yml down

# Nettoyage (optionnel - supprime les données)
docker-compose -f coolify-simple.yml down -v

# Redéploiement
docker-compose -f coolify-simple.yml up -d

# Monitoring
docker-compose -f coolify-simple.yml logs -f
```

## 📞 Support

Si vous rencontrez encore des problèmes :

1. **Vérifiez les logs** : `docker-compose logs`
2. **Consultez la documentation Coolify** : https://coolify.io/docs
3. **Vérifiez votre configuration DNS**
4. **Testez étape par étape**

---

*🚀 Avec cette configuration corrigée, votre déploiement devrait fonctionner parfaitement !*