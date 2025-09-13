#!/bin/bash

# =============================================================================
# VALIDATEUR DE CONFIGURATION DOCKER - Ubuntu Server
# Vérifie et valide les configurations Docker avant déploiement
# =============================================================================

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Validation des Configurations Docker pour Ubuntu Server${NC}"
echo "=========================================================="
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ERRORS=0
WARNINGS=0

# Fonction d'affichage des résultats
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Vérification des fichiers Docker
check_docker_files() {
    info "Vérification des fichiers Docker..."
    
    # Docker Compose
    if [[ -f "$PROJECT_DIR/docker-compose.prod.yml" ]]; then
        success "docker-compose.prod.yml trouvé"
        
        # Validation de la syntaxe YAML
        if command -v docker-compose >/dev/null 2>&1; then
            if docker-compose -f docker-compose.prod.yml config >/dev/null 2>&1; then
                success "Syntaxe docker-compose.prod.yml valide"
            else
                error "Erreur de syntaxe dans docker-compose.prod.yml"
            fi
        else
            warning "docker-compose non installé, impossible de valider la syntaxe"
        fi
    else
        error "docker-compose.prod.yml non trouvé"
    fi
    
    # Dockerfile principal
    if [[ -f "$PROJECT_DIR/Dockerfile" ]]; then
        success "Dockerfile principal trouvé"
    else
        warning "Dockerfile principal non trouvé"
    fi
}

# Vérification de la structure des répertoires
check_directory_structure() {
    info "Vérification de la structure des répertoires..."
    
    local required_dirs=(
        "backend"
        "frontend" 
        "config"
        "config/mosquitto"
        "config/grafana"
        "config/database"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$PROJECT_DIR/$dir" ]]; then
            success "Répertoire $dir existe"
        else
            error "Répertoire $dir manquant"
        fi
    done
}

# Vérification des fichiers de configuration
check_config_files() {
    info "Vérification des fichiers de configuration..."
    
    # Configuration Mosquitto
    if [[ -f "$PROJECT_DIR/config/mosquitto/mosquitto.conf" ]]; then
        success "Configuration Mosquitto trouvée"
    else
        error "Configuration Mosquitto manquante"
    fi
    
    # Configuration Prometheus
    if [[ -f "$PROJECT_DIR/config/monitoring/prometheus.yml" ]]; then
        success "Configuration Prometheus trouvée"
    else
        warning "Configuration Prometheus manquante (peut être générée automatiquement)"
    fi
    
    # Fichier .env
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        success "Fichier .env trouvé"
        
        # Vérification des variables critiques
        local required_vars=(
            "POSTGRES_PASSWORD"
            "REDIS_PASSWORD" 
            "SECRET_KEY"
            "JWT_SECRET"
            "DOMAIN_ROOT"
            "ACME_EMAIL"
        )
        
        for var in "${required_vars[@]}"; do
            if grep -q "^${var}=" "$PROJECT_DIR/.env" 2>/dev/null; then
                success "Variable $var définie"
            else
                error "Variable $var manquante dans .env"
            fi
        done
    else
        error "Fichier .env non trouvé. Lancez ./generate-secrets.sh"
    fi
}

# Vérification des Dockerfiles spécifiques
check_service_dockerfiles() {
    info "Vérification des Dockerfiles des services..."
    
    # Backend Dockerfile
    if [[ -f "$PROJECT_DIR/backend/Dockerfile" ]]; then
        success "Dockerfile backend trouvé"
        
        # Vérification des bonnes pratiques Ubuntu
        if grep -q "FROM.*alpine" "$PROJECT_DIR/backend/Dockerfile"; then
            success "Image Alpine utilisée (optimisée pour Ubuntu)"
        else
            warning "Pas d'image Alpine détectée"
        fi
        
        if grep -q "USER.*[^root]" "$PROJECT_DIR/backend/Dockerfile"; then
            success "Utilisateur non-root configuré"
        else
            error "Aucun utilisateur non-root configuré (sécurité)"
        fi
    else
        error "Dockerfile backend manquant"
    fi
    
    # Frontend Dockerfile
    if [[ -f "$PROJECT_DIR/frontend/Dockerfile" ]]; then
        success "Dockerfile frontend trouvé"
    else
        error "Dockerfile frontend manquant"
    fi
}

# Vérification des permissions Unix
check_unix_permissions() {
    info "Vérification des permissions Unix..."
    
    # Scripts exécutables
    local scripts=(
        "generate-secrets.sh"
        "deploy-coolify.sh" 
        "ubuntu-setup.sh"
        "validate-docker-config.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$PROJECT_DIR/$script" ]]; then
            if [[ -x "$PROJECT_DIR/$script" ]]; then
                success "Script $script exécutable"
            else
                warning "Script $script non exécutable (chmod +x requis)"
            fi
        fi
    done
    
    # Répertoires de configuration
    if [[ -d "$PROJECT_DIR/config" ]]; then
        local config_perms=$(stat -c "%a" "$PROJECT_DIR/config" 2>/dev/null || echo "unknown")
        if [[ "$config_perms" == "755" ]]; then
            success "Permissions config/ correctes (755)"
        else
            warning "Permissions config/ : $config_perms (755 recommandé)"
        fi
    fi
}

# Vérification de la compatibilité Ubuntu
check_ubuntu_compatibility() {
    info "Vérification de la compatibilité Ubuntu Server..."
    
    # Vérification des volumes Docker
    if grep -q "driver: local" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null; then
        success "Volumes Docker locaux (compatible Ubuntu)"
    else
        warning "Pilotes de volumes non spécifiés"
    fi
    
    # Vérification des chemins Unix
    if grep -q "/var/run/docker.sock" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null; then
        success "Socket Docker Unix configuré"
    else
        error "Socket Docker Unix non trouvé"
    fi
    
    # Vérification de l'exposition des ports
    if grep -q "ports:" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null; then
        success "Ports exposés définis"
        
        # Vérifier qu'on n'expose que les ports nécessaires
        local exposed_ports=$(grep -A 2 "ports:" "$PROJECT_DIR/docker-compose.prod.yml" | grep -o '"[0-9]*:[0-9]*"' | wc -l)
        if [[ $exposed_ports -gt 10 ]]; then
            warning "Beaucoup de ports exposés ($exposed_ports), vérifiez la sécurité"
        else
            success "Nombre de ports exposés raisonnable ($exposed_ports)"
        fi
    fi
}

# Vérification des ressources système
check_system_resources() {
    info "Vérification des exigences de ressources..."
    
    # Analyse du docker-compose pour les limites de ressources
    if grep -q "deploy:" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null; then
        if grep -q "limits:" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null; then
            success "Limites de ressources définies"
        else
            warning "Aucune limite de ressources définie"
        fi
    else
        warning "Section deploy non trouvée (limites de ressources)"
    fi
    
    # Estimation de la RAM requise
    local services_count=$(grep -c "container_name:" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null || echo "0")
    local estimated_ram=$((services_count * 512)) # 512 MB par service en moyenne
    
    info "Services détectés: $services_count"
    info "RAM estimée requise: ${estimated_ram} MB"
    
    if [[ $estimated_ram -gt 8192 ]]; then
        warning "RAM requise élevée (${estimated_ram} MB). Serveur 8GB+ recommandé."
    elif [[ $estimated_ram -gt 4096 ]]; then
        info "RAM requise modérée (${estimated_ram} MB). Serveur 4GB+ recommandé."
    else
        success "RAM requise acceptable (${estimated_ram} MB)."
    fi
}

# Vérifications de sécurité
check_security() {
    info "Vérification de la configuration de sécurité..."
    
    # Vérifier qu'aucun mot de passe n'est en dur
    if grep -r "password.*=" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null | grep -v "\${" | grep -v "#"; then
        error "Mots de passe en dur détectés dans docker-compose.prod.yml"
    else
        success "Aucun mot de passe en dur dans la configuration"
    fi
    
    # Vérifier l'utilisation de variables d'environnement
    local env_vars_count=$(grep -c "\${" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null || echo "0")
    if [[ $env_vars_count -gt 5 ]]; then
        success "Variables d'environnement utilisées ($env_vars_count)"
    else
        warning "Peu de variables d'environnement utilisées ($env_vars_count)"
    fi
    
    # Vérifier les health checks
    if grep -q "healthcheck:" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null; then
        success "Health checks configurés"
    else
        warning "Aucun health check configuré"
    fi
    
    # Vérifier le restart policy
    if grep -q "restart: unless-stopped" "$PROJECT_DIR/docker-compose.prod.yml" 2>/dev/null; then
        success "Politique de redémarrage sécurisée"
    else
        warning "Politique de redémarrage non optimale"
    fi
}

# Recommandations d'optimisation Ubuntu
show_ubuntu_optimizations() {
    echo ""
    info "Recommandations d'optimisation Ubuntu Server:"
    echo ""
    
    echo -e "${BLUE}📋 Optimisations Système:${NC}"
    echo "• Augmenter les limites de fichiers : echo '* soft nofile 65536' >> /etc/security/limits.conf"
    echo "• Configurer swappiness : echo 'vm.swappiness=10' >> /etc/sysctl.conf" 
    echo "• Activer IP forwarding : echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf"
    echo ""
    
    echo -e "${BLUE}🔒 Sécurité Ubuntu:${NC}"
    echo "• Configurer UFW : sudo ufw enable && sudo ufw default deny"
    echo "• Installer Fail2Ban : sudo apt install fail2ban"
    echo "• Mettre à jour régulièrement : sudo apt update && sudo apt upgrade"
    echo ""
    
    echo -e "${BLUE}📊 Monitoring Ubuntu:${NC}"
    echo "• Surveiller : htop, docker stats, df -h"
    echo "• Logs système : journalctl -f"
    echo "• Logs Docker : docker-compose logs -f"
}

# Génération du rapport
generate_report() {
    echo ""
    echo -e "${BLUE}📊 RAPPORT DE VALIDATION${NC}"
    echo "=========================="
    
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}🎉 Configuration parfaite ! Prête pour le déploiement Ubuntu.${NC}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}⚠️  Configuration fonctionnelle avec $WARNINGS avertissement(s).${NC}"
        echo -e "${YELLOW}   Le déploiement peut procéder mais des optimisations sont recommandées.${NC}"
    else
        echo -e "${RED}❌ Configuration incomplète : $ERRORS erreur(s), $WARNINGS avertissement(s).${NC}"
        echo -e "${RED}   Corrigez les erreurs avant de déployer sur Ubuntu.${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📈 Statistiques:${NC}"
    echo "• Erreurs critiques : $ERRORS"
    echo "• Avertissements : $WARNINGS"
    echo "• Répertoire projet : $PROJECT_DIR"
    echo ""
    
    if [[ $ERRORS -gt 0 ]]; then
        echo -e "${RED}🔧 Actions requises:${NC}"
        echo "1. Corrigez les erreurs listées ci-dessus"
        echo "2. Relancez la validation : ./validate-docker-config.sh"
        echo "3. Procédez au déploiement : ./ubuntu-setup.sh"
    else
        echo -e "${GREEN}✅ Prochaines étapes:${NC}"
        echo "1. Transférez les fichiers vers Ubuntu : ./deploy-to-ubuntu.ps1"
        echo "2. Installez l'environnement : ./ubuntu-setup.sh --full"
        echo "3. Déployez avec Coolify : ./deploy-coolify.sh"
    fi
}

# Exécution des vérifications
main() {
    echo -e "${BLUE}🏁 Début de la validation...${NC}"
    echo ""
    
    check_docker_files
    echo ""
    
    check_directory_structure  
    echo ""
    
    check_config_files
    echo ""
    
    check_service_dockerfiles
    echo ""
    
    check_unix_permissions
    echo ""
    
    check_ubuntu_compatibility
    echo ""
    
    check_system_resources
    echo ""
    
    check_security
    echo ""
    
    show_ubuntu_optimizations
    
    generate_report
}

# Point d'entrée
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi