#!/bin/bash

# =============================================================================
# INSTALLATION AUTOMATISÉE - Station Traffeyère IoT/AI Platform
# Script d'installation complète pour Ubuntu Server 20.04/22.04 LTS
# =============================================================================

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Variables globales
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$PROJECT_DIR/ubuntu-setup.log"
DOMAIN=""
EMAIL=""

echo -e "${BLUE}🚀 Installation Station Traffeyère IoT/AI Platform${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""
echo -e "${CYAN}📋 Ce script va installer:${NC}"
echo -e "   • Docker et Docker Compose"
echo -e "   • Coolify (plateforme de déploiement)"
echo -e "   • Dépendances système requises"
echo -e "   • Configuration des permissions"
echo -e "   • Génération des secrets"
echo ""

# Fonction de logging
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "${RED}❌ Erreur: $1${NC}"
    exit 1
}

success() {
    log "${GREEN}✅ $1${NC}"
}

info() {
    log "${BLUE}ℹ️  $1${NC}"
}

warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

# Vérification des privilèges
check_privileges() {
    info "Vérification des privilèges..."
    
    if [[ $EUID -eq 0 ]]; then
        error_exit "Ce script ne doit PAS être exécuté en tant que root. Utilisez sudo uniquement quand nécessaire."
    fi
    
    # Vérifier si l'utilisateur peut utiliser sudo
    if ! sudo -n true 2>/dev/null; then
        info "Privilèges sudo requis. Vous devrez saisir votre mot de passe."
    fi
    
    success "Privilèges vérifiés"
}

# Vérification de la version Ubuntu
check_ubuntu_version() {
    info "Vérification de la version Ubuntu..."
    
    if ! command -v lsb_release >/dev/null 2>&1; then
        sudo apt update && sudo apt install -y lsb-release
    fi
    
    UBUNTU_VERSION=$(lsb_release -rs)
    UBUNTU_CODENAME=$(lsb_release -cs)
    
    info "Ubuntu $UBUNTU_VERSION ($UBUNTU_CODENAME) détectée"
    
    # Vérifier que c'est une version supportée
    case $UBUNTU_VERSION in
        20.04|22.04|24.04)
            success "Version Ubuntu supportée: $UBUNTU_VERSION"
            ;;
        *)
            warning "Version Ubuntu non testée: $UBUNTU_VERSION. Continuons quand même..."
            ;;
    esac
}

# Installation des dépendances système
install_system_dependencies() {
    info "Installation des dépendances système..."
    
    # Mise à jour des paquets
    sudo apt update
    
    # Installation des paquets essentiels
    local packages=(
        "curl"
        "wget"
        "git"
        "openssl"
        "pwgen"
        "jq"
        "unzip"
        "apt-transport-https"
        "ca-certificates"
        "gnupg"
        "lsb-release"
        "software-properties-common"
        "ufw"
        "fail2ban"
        "htop"
        "nano"
        "vim"
    )
    
    sudo apt install -y "${packages[@]}"
    
    success "Dépendances système installées"
}

# Installation de Docker
install_docker() {
    info "Installation de Docker..."
    
    if command -v docker >/dev/null 2>&1; then
        warning "Docker est déjà installé"
        docker --version
        return 0
    fi
    
    # Suppression d'anciennes versions
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Installation via le script officiel Docker
    curl -fsSL https://get.docker.com | sh
    
    # Ajout de l'utilisateur au groupe docker
    sudo usermod -aG docker $USER
    
    # Activation du service
    sudo systemctl enable docker
    sudo systemctl start docker
    
    success "Docker installé avec succès"
    info "⚠️  Vous devrez vous reconnecter pour que les permissions Docker soient appliquées"
}

# Installation de Docker Compose
install_docker_compose() {
    info "Installation de Docker Compose..."
    
    if command -v docker-compose >/dev/null 2>&1; then
        warning "Docker Compose est déjà installé"
        docker-compose --version
        return 0
    fi
    
    # Installation via apt (version récente sur Ubuntu 20.04+)
    sudo apt install -y docker-compose-plugin docker-compose
    
    # Vérification
    docker-compose --version
    
    success "Docker Compose installé"
}

# Configuration du firewall
setup_firewall() {
    info "Configuration du firewall UFW..."
    
    # Activation d'UFW
    sudo ufw --force enable
    
    # Règles de base
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Autoriser SSH
    sudo ufw allow OpenSSH
    
    # Autoriser HTTP et HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Ports pour Coolify (si nécessaire)
    sudo ufw allow 8000/tcp  # Coolify UI
    
    # Affichage du statut
    sudo ufw status
    
    success "Firewall configuré"
}

# Configuration de Fail2Ban
setup_fail2ban() {
    info "Configuration de Fail2Ban..."
    
    # Création de la configuration personnalisée
    sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF
    
    # Redémarrage du service
    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    
    success "Fail2Ban configuré"
}

# Installation de Coolify
install_coolify() {
    info "Installation de Coolify..."
    
    # Vérification si Docker fonctionne
    if ! docker ps >/dev/null 2>&1; then
        error_exit "Docker n'est pas accessible. Redémarrez votre session SSH et relancez le script."
    fi
    
    # Installation de Coolify
    curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
    
    success "Coolify installé"
    info "Coolify sera accessible sur: http://$(curl -s http://whatismyip.akamai.com/):8000"
}

# Génération des secrets
generate_secrets() {
    info "Génération des secrets de sécurité..."
    
    if [[ ! -f "$PROJECT_DIR/generate-secrets.sh" ]]; then
        error_exit "Le script generate-secrets.sh n'a pas été trouvé"
    fi
    
    # Rendre le script exécutable
    chmod +x "$PROJECT_DIR/generate-secrets.sh"
    
    # Demander les informations de domaine
    echo ""
    read -p "Entrez votre domaine principal (ex: traffeyere-station.fr): " DOMAIN
    read -p "Entrez votre email pour Let's Encrypt: " EMAIL
    
    # Générer les secrets avec création automatique du .env
    echo -e "y\n$DOMAIN\n$EMAIL" | "$PROJECT_DIR/generate-secrets.sh"
    
    success "Secrets générés dans .env"
}

# Configuration des permissions
setup_permissions() {
    info "Configuration des permissions..."
    
    # Permissions des scripts
    chmod +x "$PROJECT_DIR"/*.sh 2>/dev/null || true
    
    # Permissions des dossiers de configuration
    if [[ -d "$PROJECT_DIR/config" ]]; then
        chmod -R 755 "$PROJECT_DIR/config"
    fi
    
    # Permissions des fichiers de configuration
    find "$PROJECT_DIR" -name "*.yml" -exec chmod 644 {} \; 2>/dev/null || true
    find "$PROJECT_DIR" -name "*.yaml" -exec chmod 644 {} \; 2>/dev/null || true
    find "$PROJECT_DIR" -name "*.json" -exec chmod 644 {} \; 2>/dev/null || true
    find "$PROJECT_DIR" -name "*.conf" -exec chmod 644 {} \; 2>/dev/null || true
    
    # Protection du fichier .env
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        chmod 600 "$PROJECT_DIR/.env"
    fi
    
    success "Permissions configurées"
}

# Optimisations système
optimize_system() {
    info "Optimisations système..."
    
    # Augmentation des limites de fichiers ouverts
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
    
    # Configuration de swappiness
    echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
    
    # Configuration réseau pour Docker
    echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
    
    # Application immédiate
    sudo sysctl -p
    
    success "Optimisations système appliquées"
}

# Vérifications finales
final_checks() {
    info "Vérifications finales..."
    
    # Vérifier Docker
    if docker --version >/dev/null 2>&1; then
        success "Docker: OK"
    else
        error_exit "Docker n'est pas correctement installé"
    fi
    
    # Vérifier Docker Compose
    if docker-compose --version >/dev/null 2>&1; then
        success "Docker Compose: OK"
    else
        error_exit "Docker Compose n'est pas correctement installé"
    fi
    
    # Vérifier les permissions Docker
    if groups $USER | grep -q docker; then
        success "Permissions Docker: OK"
    else
        warning "Permissions Docker: vous devez vous reconnecter pour appliquer les permissions"
    fi
    
    # Vérifier le fichier .env
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        success "Fichier .env: OK"
    else
        warning "Fichier .env non trouvé. Lancez generate-secrets.sh manuellement."
    fi
}

# Affichage des informations finales
show_final_info() {
    echo ""
    echo -e "${GREEN}🎉 INSTALLATION TERMINÉE AVEC SUCCÈS !${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo ""
    echo -e "${CYAN}📋 RÉSUMÉ DE L'INSTALLATION:${NC}"
    echo -e "   ✅ Ubuntu $(lsb_release -rs) préparé"
    echo -e "   ✅ Docker installé"
    echo -e "   ✅ Docker Compose installé"
    echo -e "   ✅ Coolify installé"
    echo -e "   ✅ Firewall configuré"
    echo -e "   ✅ Fail2Ban activé"
    echo -e "   ✅ Secrets générés"
    echo -e "   ✅ Permissions configurées"
    echo ""
    echo -e "${PURPLE}🌐 ACCÈS AUX SERVICES:${NC}"
    echo -e "   Coolify UI: http://$(curl -s http://whatismyip.akamai.com/):8000"
    echo -e "   SSH: ssh $USER@$(curl -s http://whatismyip.akamai.com/)"
    echo ""
    echo -e "${YELLOW}⚠️  ACTIONS REQUISES:${NC}"
    echo -e "   1. Reconnectez-vous via SSH pour appliquer les permissions Docker"
    echo -e "   2. Configurez vos DNS pour pointer vers cette IP: $(curl -s http://whatismyip.akamai.com/)"
    echo -e "   3. Complétez la configuration Coolify via l'interface web"
    echo -e "   4. Lancez le déploiement avec: ./deploy-coolify.sh"
    echo ""
    echo -e "${BLUE}📖 Documentation:${NC}"
    echo -e "   • README-DEPLOYMENT.md - Guide complet de déploiement"
    echo -e "   • DEPLOYMENT_GUIDE.md - Instructions détaillées"
    echo -e "   • Log d'installation: $LOG_FILE"
    echo ""
    
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        echo -e "${GREEN}📁 Fichier .env créé avec le domaine: $DOMAIN${NC}"
        echo -e "${CYAN}   N'oubliez pas d'ajouter vos clés API IA dans ce fichier !${NC}"
    fi
    echo ""
}

# Menu principal
main_menu() {
    echo -e "${CYAN}🔧 OPTIONS D'INSTALLATION:${NC}"
    echo "1) Installation complète automatique (recommandé)"
    echo "2) Installation personnalisée"
    echo "3) Vérifier les prérequis seulement"
    echo "4) Quitter"
    echo ""
    read -p "Choisissez une option [1-4]: " choice
    
    case $choice in
        1)
            full_installation
            ;;
        2)
            custom_installation
            ;;
        3)
            check_prerequisites_only
            ;;
        4)
            echo "Installation annulée."
            exit 0
            ;;
        *)
            echo "Option invalide."
            main_menu
            ;;
    esac
}

# Installation complète
full_installation() {
    info "Début de l'installation complète..."
    
    check_privileges
    check_ubuntu_version
    install_system_dependencies
    install_docker
    install_docker_compose
    setup_firewall
    setup_fail2ban
    optimize_system
    setup_permissions
    install_coolify
    generate_secrets
    final_checks
    show_final_info
}

# Installation personnalisée
custom_installation() {
    info "Installation personnalisée..."
    
    check_privileges
    check_ubuntu_version
    
    echo ""
    echo -e "${CYAN}Sélectionnez les composants à installer:${NC}"
    
    read -p "Installer les dépendances système ? [Y/n]: " install_deps
    [[ $install_deps =~ ^[Nn]$ ]] || install_system_dependencies
    
    read -p "Installer Docker ? [Y/n]: " install_dock
    [[ $install_dock =~ ^[Nn]$ ]] || install_docker
    
    read -p "Installer Docker Compose ? [Y/n]: " install_compose
    [[ $install_compose =~ ^[Nn]$ ]] || install_docker_compose
    
    read -p "Configurer le firewall ? [Y/n]: " setup_fw
    [[ $setup_fw =~ ^[Nn]$ ]] || setup_firewall
    
    read -p "Configurer Fail2Ban ? [Y/n]: " setup_f2b
    [[ $setup_f2b =~ ^[Nn]$ ]] || setup_fail2ban
    
    read -p "Installer Coolify ? [Y/n]: " install_cool
    [[ $install_cool =~ ^[Nn]$ ]] || install_coolify
    
    read -p "Générer les secrets ? [Y/n]: " gen_secrets
    [[ $gen_secrets =~ ^[Nn]$ ]] || generate_secrets
    
    setup_permissions
    optimize_system
    final_checks
    show_final_info
}

# Vérification des prérequis uniquement
check_prerequisites_only() {
    info "Vérification des prérequis..."
    
    check_privileges
    check_ubuntu_version
    
    echo ""
    echo -e "${CYAN}État des composants:${NC}"
    
    # Docker
    if command -v docker >/dev/null 2>&1; then
        success "Docker: installé ($(docker --version | cut -d' ' -f3))"
    else
        warning "Docker: non installé"
    fi
    
    # Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        success "Docker Compose: installé ($(docker-compose --version | cut -d' ' -f3))"
    else
        warning "Docker Compose: non installé"
    fi
    
    # Coolify
    if docker ps | grep -q coolify; then
        success "Coolify: en fonctionnement"
    else
        warning "Coolify: non installé ou arrêté"
    fi
    
    # UFW
    if sudo ufw status | grep -q "Status: active"; then
        success "UFW Firewall: actif"
    else
        warning "UFW Firewall: inactif"
    fi
    
    # Fail2Ban
    if systemctl is-active --quiet fail2ban; then
        success "Fail2Ban: actif"
    else
        warning "Fail2Ban: inactif"
    fi
    
    echo ""
    info "Vérification terminée"
}

# Point d'entrée principal
main() {
    # Création du fichier de log
    touch "$LOG_FILE"
    log "$(date): Début de l'installation Ubuntu"
    
    # Affichage du menu si aucun argument
    if [[ $# -eq 0 ]]; then
        main_menu
    else
        case $1 in
            --full)
                full_installation
                ;;
            --check)
                check_prerequisites_only
                ;;
            --help|-h)
                echo "Usage: $0 [--full|--check|--help]"
                echo "  --full    Installation complète automatique"
                echo "  --check   Vérifier les prérequis seulement"
                echo "  --help    Afficher cette aide"
                ;;
            *)
                error_exit "Option inconnue: $1. Utilisez --help pour les options disponibles."
                ;;
        esac
    fi
}

# Gestion des signaux
trap 'echo -e "\n${RED}Installation interrompue par l\'utilisateur${NC}"; exit 1' INT TERM

# Lancement du script
main "$@"