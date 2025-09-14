# 🔧 Erreur Port 8000 Déjà Utilisé - Coolify

## ❌ Erreur Constatée
```
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint backend-xxx: Bind for 0.0.0.0:8000 failed: port is already allocated
```

## 🎯 Cause du Problème
Coolify utilise un reverse proxy automatique (Traefik) qui gère les ports. Il ne faut **pas** exposer les ports dans le docker-compose.

## ✅ Solutions Immédiates

### Solution 1: Utiliser la Version Sans Ports
Remplacez votre fichier docker-compose par :
**`docker-compose.coolify.noports.yml`**

Cette version supprime tous les `ports:` et utilise le reverse proxy Coolify.

### Solution 2: Modifier le Fichier Existant
Dans votre docker-compose actuel, remplacez :

```yaml
# ❌ NE PAS FAIRE
backend:
  ports:
    - "8000:8000"

frontend:
  ports:
    - "80:80"
```

Par :

```yaml
# ✅ CORRECT POUR COOLIFY
backend:
  expose:
    - "8000"  # Optionnel

frontend:
  expose:
    - "80"    # Optionnel
```

Ou encore mieux, supprimez complètement les sections `ports:` et `expose:`.

## 🚀 Configuration Coolify

Dans l'interface Coolify :

### Backend Service
- **Port**: `8000` (Coolify détecte automatiquement)
- **Domain**: `https://votre-backend.coolify.app`
- **Health Check**: `/health`

### Frontend Service  
- **Port**: `80` (Coolify détecte automatiquement)
- **Domain**: `https://votre-frontend.coolify.app`
- **Health Check**: `/healthz`

## 🔧 Étapes de Correction

### Étape 1: Nouveau Fichier
Utilisez `docker-compose.coolify.noports.yml`

### Étape 2: Variables d'Environnement
```bash
POSTGRES_PASSWORD=changeme123456
SECRET_KEY=changeme-secret-key-123456789
JWT_SECRET=changeme-jwt-secret-123456789
INFLUX_ADMIN_TOKEN=changeme-token-123456
```

### Étape 3: Configuration des Services Coolify
- **Backend**: Port interne `8000`, exposé via reverse proxy
- **Frontend**: Port interne `80`, exposé via reverse proxy

### Étape 4: Redéploiement
1. Sauvegarder la configuration
2. Redéployer le projet
3. Coolify assignera automatiquement les URLs

## 🎯 Avantages de Cette Approche

### ✅ Reverse Proxy Automatique
- Coolify gère automatiquement les ports
- SSL/TLS automatique
- Load balancing intégré

### ✅ Pas de Conflits de Ports
- Aucun risque de "port already allocated"
- Isolation complète des services

### ✅ URLs Propres
- `https://backend.votredomaine.com`
- `https://frontend.votredomaine.com`

## 🔍 Test de Validation

Une fois déployé :

```bash
# Backend via reverse proxy Coolify
curl https://votre-backend.coolify.app/health

# Frontend via reverse proxy Coolify  
curl https://votre-frontend.coolify.app/healthz
```

## 📋 Checklist

- [ ] Fichier docker-compose sans ports exposés
- [ ] Variables d'environnement configurées
- [ ] Services Coolify configurés avec ports internes
- [ ] Redéploiement effectué
- [ ] Test des URLs finales

## ⚡ Résultat Attendu

✅ **Aucune erreur de port**  
✅ **Reverse proxy automatique**  
✅ **SSL/TLS automatique**  
✅ **URLs propres et accessibles**

**Déploiement réussi en moins de 2 minutes !** 🎉