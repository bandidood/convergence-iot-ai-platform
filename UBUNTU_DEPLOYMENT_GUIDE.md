# 🚀 Guide de Déploiement Ubuntu Server - Station Traffeyère IoT/AI Platform

Ce guide détaille le processus complet de déploiement de la plateforme Station Traffeyère sur un serveur Ubuntu Server via Coolify.

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Architecture de Déploiement](#architecture-de-déploiement)
3. [Phase 1: Préparation Windows](#phase-1-préparation-windows)
4. [Phase 2: Transfert vers Ubuntu](#phase-2-transfert-vers-ubuntu)
5. [Phase 3: Installation Ubuntu](#phase-3-installation-ubuntu)
6. [Phase 4: Configuration DNS](#phase-4-configuration-dns)
7. [Phase 5: Déploiement Coolify](#phase-5-déploiement-coolify)
8. [Phase 6: Vérification et Tests](#phase-6-vérification-et-tests)
9. [Maintenance et Monitoring](#maintenance-et-monitoring)
10. [Dépannage](#dépannage)

---

## 🔧 Prérequis

### Serveur Ubuntu
- **OS**: Ubuntu Server 20.04 LTS ou supérieur
- **RAM**: Minimum 4 Go (8 Go recommandés)
- **Stockage**: Minimum 50 Go SSD
- **CPU**: 2 vCPU minimum (4 vCPU recommandés)
- **Réseau**: IP publique statique
- **Accès**: SSH activé avec clés ou mot de passe

### Poste Windows (développement)
- **PowerShell**: Version 5.1 ou supérieure
- **SSH Client**: OpenSSH ou Git Bash
- **Outils**: SCP pour le transfert de fichiers

### DNS et Domaine
- Nom de domaine configuré
- Accès aux enregistrements DNS
- Certificats SSL (Let's Encrypt supporté)

---

## 🏗️ Architecture de Déploiement

```
                    Internet
                       |
                   [DNS/CDN]
                       |
              [Ubuntu Server + UFW]
                       |
            ┌──────────┴──────────┐
            │      Coolify        │
            │   (Reverse Proxy)   │
            └──────────┬──────────┘
                       │
      ┌────────────────┼────────────────┐
      │                │                │
 [Frontend]        [Backend]      [Monitoring]
 Next.js App      FastAPI App    Grafana/Prometheus
      │                │                │
      └────────────────┼────────────────┘
                       │
           ┌───────────┼───────────┐
           │           │           │
    [PostgreSQL]   [Redis]    [InfluxDB]
     Database       Cache      Time-Series
           │           │           │
           └───────────┼───────────┘
                       │
                [MQTT Broker]
               Eclipse Mosquitto
```

---

## 📦 Phase 1: Préparation Windows

### 1.1 Génération des Secrets

Sur votre poste Windows, dans le répertoire du projet :

```powershell
# Génération des secrets
./generate-secrets.sh
```

### 1.2 Vérification des Fichiers

Vérifiez que vous avez tous les fichiers nécessaires :

```
station-traffeyere/
├── .env.production              # Template de configuration
├── generate-secrets.sh          # Générateur de secrets
├── deploy-coolify.sh           # Script de déploiement Coolify
├── ubuntu-setup.sh             # Script d'installation Ubuntu
├── deploy-to-ubuntu.ps1        # Script de transfert Windows → Ubuntu
├── docker-compose.prod.yml     # Configuration Docker
├── backend/                    # Code backend FastAPI
├── frontend/                   # Code frontend Next.js
├── config/                     # Configurations diverses
├── DEPLOYMENT_GUIDE.md         # Guide détaillé
└── README-DEPLOYMENT.md        # Résumé du déploiement
```

---

## 🔄 Phase 2: Transfert vers Ubuntu

### 2.1 Transfert avec Clé SSH

```powershell
# Avec clé SSH privée
.\deploy-to-ubuntu.ps1 -ServerIP "VOTRE_IP_SERVEUR" -Username "ubuntu" -KeyPath "C:\path\to\private_key.pem"
```

### 2.2 Transfert avec Mot de Passe

```powershell
# Avec authentification par mot de passe
.\deploy-to-ubuntu.ps1 -ServerIP "VOTRE_IP_SERVEUR" -Username "ubuntu"
```

### 2.3 Options Avancées

```powershell
# Avec génération automatique du .env
.\deploy-to-ubuntu.ps1 -ServerIP "192.168.1.100" -Username "ubuntu" -CreateEnv

# Avec chemin personnalisé sur Ubuntu
.\deploy-to-ubuntu.ps1 -ServerIP "192.168.1.100" -Username "ubuntu" -ProjectPath "/opt/station-traffeyere"
```

---

## ⚙️ Phase 3: Installation Ubuntu

### 3.1 Connexion au Serveur

```bash
# Connexion SSH au serveur Ubuntu
ssh ubuntu@VOTRE_IP_SERVEUR

# Navigation vers le projet
cd ~/station-traffeyere  # ou votre chemin personnalisé
```

### 3.2 Installation Automatique (Recommandée)

```bash
# Installation complète automatique
chmod +x ubuntu-setup.sh
./ubuntu-setup.sh --full
```

### 3.3 Installation Interactive

```bash
# Installation avec menu interactif
./ubuntu-setup.sh
# Sélectionnez option 1 pour l'installation complète
```

### 3.4 Vérification de l'Installation

```bash
# Vérifier les services installés
./ubuntu-setup.sh --check
```

### 3.5 Installation Manuelle (Si Nécessaire)

Si l'installation automatique échoue :

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation de Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Installation de Coolify
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

# Redémarrage de session pour appliquer les permissions
exit
# Reconnexion SSH requise
```

---

## 🌐 Phase 4: Configuration DNS

### 4.1 Enregistrements DNS Requis

Configurez ces enregistrements dans votre zone DNS :

| Sous-domaine | Type | Valeur | Description |
|--------------|------|--------|-------------|
| @ | A | IP_SERVEUR | Domaine principal |
| www | CNAME | @ | Alias vers domaine principal |
| app | A | IP_SERVEUR | Application frontend |
| api | A | IP_SERVEUR | API backend |
| grafana | A | IP_SERVEUR | Tableau de bord monitoring |
| coolify | A | IP_SERVEUR | Interface Coolify |

### 4.2 Exemple de Configuration DNS

Pour le domaine `traffeyere-station.fr` :

```dns
traffeyere-station.fr.          A     203.0.113.10
www.traffeyere-station.fr.      CNAME traffeyere-station.fr.
app.traffeyere-station.fr.      A     203.0.113.10
api.traffeyere-station.fr.      A     203.0.113.10
grafana.traffeyere-station.fr.  A     203.0.113.10
coolify.traffeyere-station.fr.  A     203.0.113.10
```

### 4.3 Vérification DNS

```bash
# Vérifier la résolution DNS
nslookup app.votre-domaine.com
dig api.votre-domaine.com
```

---

## 🚀 Phase 5: Déploiement Coolify

### 5.1 Accès à Coolify

1. Ouvrez votre navigateur sur `http://VOTRE_IP:8000`
2. Créez le compte administrateur initial
3. Configurez votre serveur local

### 5.2 Configuration Initiale

```bash
# Sur le serveur, configuration du domaine dans .env
nano .env

# Modifiez ces lignes selon votre domaine :
DOMAIN_ROOT=traffeyere-station.fr
ACME_EMAIL=admin@traffeyere-station.fr
```

### 5.3 Déploiement Automatique via Script

```bash
# Lancement du déploiement Coolify
chmod +x deploy-coolify.sh
./deploy-coolify.sh
```

### 5.4 Déploiement Manuel via Interface Coolify

#### 5.4.1 Création du Projet

1. **Nouveau Projet** → `station-traffeyere-iot`
2. **Type** → Docker Compose
3. **Repository** → Votre dépôt Git ou fichiers locaux

#### 5.4.2 Services à Déployer

**Base de Données PostgreSQL :**
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
```

**Cache Redis :**
```yaml
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
```

**Backend FastAPI :**
```yaml
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.${DOMAIN_ROOT}`)"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
```

**Frontend Next.js :**
```yaml
  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=https://api.${DOMAIN_ROOT}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`app.${DOMAIN_ROOT}`)"
      - "traefik.http.routers.app.tls.certresolver=letsencrypt"
```

---

## ✅ Phase 6: Vérification et Tests

### 6.1 Vérification des Services

```bash
# Statut des conteneurs
docker ps

# Logs des services
docker-compose logs backend
docker-compose logs frontend

# Santé des services
curl -f http://localhost:8000/health
curl -f http://localhost:3000/api/health
```

### 6.2 Tests des Endpoints

```bash
# Test API Backend
curl -X GET https://api.votre-domaine.com/health
curl -X GET https://api.votre-domaine.com/stations

# Test Frontend
curl -I https://app.votre-domaine.com
```

### 6.3 Vérification SSL

```bash
# Test des certificats SSL
openssl s_client -connect api.votre-domaine.com:443 -servername api.votre-domaine.com

# Vérification via curl
curl -I https://app.votre-domaine.com
```

### 6.4 Monitoring

Accès aux tableaux de bord :
- **Grafana** : `https://grafana.votre-domaine.com`
- **Coolify Dashboard** : `https://coolify.votre-domaine.com`

---

## 📊 Maintenance et Monitoring

### 7.1 Surveillance des Logs

```bash
# Logs en temps réel
docker-compose logs -f

# Logs spécifiques
docker-compose logs -f backend
docker-compose logs -f postgres
```

### 7.2 Sauvegarde

```bash
# Sauvegarde de la base de données
docker-compose exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_$(date +%Y%m%d_%H%M%S).sql

# Sauvegarde des volumes
docker run --rm -v station-traffeyere_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

### 7.3 Mise à Jour

```bash
# Mise à jour des conteneurs
docker-compose pull
docker-compose up -d --force-recreate

# Mise à jour du système Ubuntu
sudo apt update && sudo apt upgrade -y
```

### 7.4 Monitoring des Ressources

```bash
# Utilisation des ressources
htop
df -h
docker stats

# Espace disque des volumes Docker
docker system df -v
```

---

## 🔧 Dépannage

### 8.1 Problèmes Courants

#### Service ne démarre pas
```bash
# Vérifier les logs
docker-compose logs service_name

# Recréer le service
docker-compose up -d --force-recreate service_name
```

#### Problème de permissions Docker
```bash
# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER
# Redémarrer la session SSH
exit
```

#### Certificats SSL non générés
```bash
# Vérifier la configuration DNS
dig +short app.votre-domaine.com

# Forcer le renouvellement
docker-compose exec traefik traefik version
```

#### Base de données inaccessible
```bash
# Vérifier le status PostgreSQL
docker-compose exec postgres pg_isready

# Réinitialiser le mot de passe
docker-compose exec postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'nouveau_mot_de_passe';"
```

### 8.2 Commandes de Diagnostic

```bash
# État des services système
sudo systemctl status docker
sudo systemctl status fail2ban
sudo ufw status

# Tests de connectivité
nc -zv localhost 5432  # PostgreSQL
nc -zv localhost 6379  # Redis
nc -zv localhost 8000  # Backend API

# Espace disque et inodes
df -h
df -i

# Processus consommant des ressources
ps aux --sort=-%cpu | head -10
ps aux --sort=-%mem | head -10
```

### 8.3 Réinitialisation Complète

En cas de problème majeur :

```bash
# ATTENTION : Ceci supprime toutes les données !

# Arrêt et suppression des conteneurs
docker-compose down -v

# Suppression des images
docker system prune -a

# Redéploiement
./deploy-coolify.sh
```

---

## 📞 Support

### Ressources Utiles

- **Documentation Coolify** : https://coolify.io/docs
- **Documentation Docker** : https://docs.docker.com/
- **Documentation Ubuntu Server** : https://ubuntu.com/server/docs

### Logs Importants

- **Ubuntu Setup** : `~/station-traffeyere/ubuntu-setup.log`
- **Docker Compose** : `docker-compose logs`
- **Système** : `/var/log/syslog`
- **Fail2Ban** : `/var/log/fail2ban.log`

---

## 🎯 Checklist de Déploiement

- [ ] Serveur Ubuntu préparé (IP, SSH, DNS)
- [ ] Fichiers transférés depuis Windows
- [ ] Installation Ubuntu complétée (`ubuntu-setup.sh`)
- [ ] Configuration DNS propagée
- [ ] Coolify accessible et configuré
- [ ] Variables d'environnement définies (`.env`)
- [ ] Services déployés via Coolify
- [ ] Certificats SSL générés
- [ ] Tests d'endpoints réussis
- [ ] Monitoring opérationnel (Grafana)
- [ ] Sauvegarde configurée
- [ ] Documentation mise à jour

---

*Guide rédigé pour Station Traffeyère IoT/AI Platform - Version Ubuntu Server*
*Dernière mise à jour : $(date +'%Y-%m-%d')*