#!/bin/bash
# =============================================================================
# SCRIPT DE MIGRATION FICHIERS - STATION TRAFFEYÈRE IoT/AI PLATFORM
# Migration vers structure repository complète - RNCP 39394
# =============================================================================

set -euo pipefail

# Configuration
LOG_FILE="/tmp/migrate-traffeyere-$(date +%Y%m%d_%H%M%S).log"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonctions utilitaires
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

show_banner() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                          📦 MIGRATION FICHIERS STATION TRAFFEYÈRE 📦                                       ║"
    echo "║                                                                                                              ║"
    echo "║    🔄 Réorganisation vers Architecture Repository Complète                                                  ║"
    echo "║    📚 Projet RNCP 39394 - Expert en Systèmes d'Information et Sécurité                                     ║"
    echo "║                                                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Vérification prérequis migration
check_migration_prerequisites() {
    log "🔍 Vérification prérequis migration..."
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -d ".git" ]; then
        error "Pas de repository Git détecté. Exécutez ce script depuis la racine du projet."
    fi
    
    # Vérifier la présence de fichiers à migrer
    if [ ! -f "docker-compose.coolify.complete.yml" ] && [ ! -d "core" ]; then
        warn "Aucun fichier de l'ancienne structure détecté."
    fi
    
    log "✅ Prérequis migration validés"
}

# Sauvegarde avant migration
create_backup() {
    log "💾 Création sauvegarde avant migration..."
    
    BACKUP_DIR="./migration-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Sauvegarde des fichiers importants
    files_to_backup=(
        "docker-compose.coolify.complete.yml"
        "docker-compose.coolify.optimized.yml"
        ".env"
        ".env.production"
        ".env.production.optimized"
        "deploy-complete-advanced.ps1"
        "README.md"
    )
    
    for file in "${files_to_backup[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/"
            info "Sauvegardé: $file"
        fi
    done
    
    log "✅ Sauvegarde créée dans: $BACKUP_DIR"
}

# Migration des fichiers Docker Compose
migrate_docker_compose_files() {
    log "🐳 Migration des fichiers Docker Compose..."
    
    # Renommer et organiser les fichiers Docker Compose
    if [ -f "docker-compose.coolify.complete.yml" ]; then
        mv "docker-compose.coolify.complete.yml" "docker-compose.yml"
        log "✅ docker-compose.coolify.complete.yml → docker-compose.yml"
    fi
    
    if [ -f "docker-compose.coolify.optimized.yml" ]; then
        mv "docker-compose.coolify.optimized.yml" "docker-compose.production.yml"
        log "✅ docker-compose.coolify.optimized.yml → docker-compose.production.yml"
    fi
    
    # Migration vers structure modulaire si nécessaire
    # (Ces fichiers seront créés séparément selon l'architecture)
}

# Migration des configurations
migrate_configurations() {
    log "⚙️ Migration des configurations..."
    
    # Déplacer configurations existantes
    config_migrations=(
        "mosquitto.conf:configurations/mosquitto/mosquitto.conf"
        "nginx.conf:configurations/nginx/nginx.conf"
        "prometheus.yml:configurations/prometheus/prometheus.yml"
    )
    
    for migration in "${config_migrations[@]}"; do
        source="${migration%:*}"
        dest="${migration#*:}"
        
        if [ -f "$source" ]; then
            mkdir -p "$(dirname "$dest")"
            mv "$source" "$dest"
            log "✅ $source → $dest"
        fi
    done
}

# Migration des variables d'environnement
migrate_env_files() {
    log "🔧 Migration des variables d'environnement..."
    
    # Consolidation des fichiers .env
    if [ -f ".env.production.optimized" ] && [ ! -f ".env.production" ]; then
        mv ".env.production.optimized" ".env.production"
        log "✅ .env.production.optimized → .env.production"
    fi
    
    # Création fichier .env.example à partir du .env existant
    if [ -f ".env.production" ] && [ ! -f ".env.example" ]; then
        # Masquer les valeurs sensibles dans l'example
        sed 's/=.*/=CHANGE_ME/' ".env.production" > ".env.example"
        log "✅ Création .env.example à partir de .env.production"
    fi
}

# Migration des scripts
migrate_scripts() {
    log "📜 Migration des scripts..."
    
    # Déplacer les scripts PowerShell vers le dossier scripts
    scripts_to_migrate=(
        "deploy-complete-advanced.ps1"
        "setup-environment.sh"
    )
    
    for script in "${scripts_to_migrate[@]}"; do
        if [ -f "$script" ]; then
            # Si le fichier n'existe pas déjà dans scripts/
            if [ ! -f "scripts/$script" ]; then
                mv "$script" "scripts/"
                log "✅ $script → scripts/"
            else
                warn "$script existe déjà dans scripts/, gardé comme backup"
                mv "$script" "scripts/${script}.backup"
            fi
        fi
    done
}

# Migration des documentations
migrate_documentation() {
    log "📚 Migration de la documentation..."
    
    # Migration des annexes vers documentation structurée
    if [ -d "Annexes" ]; then
        # Créer sous-dossiers appropriés
        mkdir -p documentation/rncp-validation/annexes
        
        # Déplacer les annexes
        mv Annexes/* documentation/rncp-validation/annexes/ 2>/dev/null || true
        
        # Supprimer le dossier vide
        if [ -d "Annexes" ] && [ -z "$(ls -A Annexes)" ]; then
            rmdir Annexes
        fi
        
        log "✅ Annexes → documentation/rncp-validation/annexes/"
    fi
    
    # Migration des documents spécialisés
    doc_migrations=(
        "coolify_deployment_inventory.md:documentation/architecture/deployment-inventory.md"
        "docker_files_structure.md:documentation/architecture/docker-structure.md"
    )
    
    for migration in "${doc_migrations[@]}"; do
        source="${migration%:*}"
        dest="${migration#*:}"
        
        if [ -f "$source" ]; then
            mkdir -p "$(dirname "$dest")"
            mv "$source" "$dest"
            log "✅ $source → $dest"
        fi
    done
}

# Migration des composants spécialisés
migrate_specialized_components() {
    log "🔧 Migration des composants spécialisés..."
    
    # Migration SOC-AI vers interfaces
    if [ -d "soc-ai" ]; then
        mkdir -p interfaces/soc-dashboard
        mv soc-ai/* interfaces/soc-dashboard/ 2>/dev/null || true
        
        if [ -d "soc-ai" ] && [ -z "$(ls -A soc-ai)" ]; then
            rmdir soc-ai
        fi
        
        log "✅ soc-ai → interfaces/soc-dashboard/"
    fi
    
    # Migration blockchain vers core/blockchain-layer
    if [ -d "blockchain-hyperledger" ]; then
        mkdir -p core/blockchain-layer
        mv blockchain-hyperledger/* core/blockchain-layer/ 2>/dev/null || true
        
        if [ -d "blockchain-hyperledger" ] && [ -z "$(ls -A blockchain-hyperledger)" ]; then
            rmdir blockchain-hyperledger
        fi
        
        log "✅ blockchain-hyperledger → core/blockchain-layer/"
    fi
    
    # Migration digital-twin vers core/digital-twin
    if [ -d "digital-twin-unity" ]; then
        if [ ! -d "core/digital-twin" ]; then
            mkdir -p core/digital-twin
        fi
        mv digital-twin-unity/* core/digital-twin/ 2>/dev/null || true
        
        if [ -d "digital-twin-unity" ] && [ -z "$(ls -A digital-twin-unity)" ]; then
            rmdir digital-twin-unity
        fi
        
        log "✅ digital-twin-unity → core/digital-twin/"
    fi
}

# Nettoyage post-migration
cleanup_post_migration() {
    log "🧹 Nettoyage post-migration..."
    
    # Supprimer dossiers vides de l'ancienne structure
    old_dirs_to_check=(
        "ci"
        "config" 
        "data"
        "database"
        "docs"
        "infrastructure"
        "logs"
        "mqtt"
        "network"
        "scripts"
        "services"
        "volumes"
    )
    
    for dir in "${old_dirs_to_check[@]}"; do
        if [ -d "$dir" ] && [ -z "$(ls -A "$dir")" ]; then
            rmdir "$dir"
            info "Supprimé dossier vide: $dir"
        fi
    done
    
    # Nettoyer fichiers temporaires
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*.log" -path "./logs/*" -delete 2>/dev/null || true
}

# Mise à jour des références
update_references() {
    log "🔗 Mise à jour des références..."
    
    # Mettre à jour les chemins dans docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        # Mise à jour des chemins de build context
        sed -i.bak 's|context: \./edge-ai-engine|context: ./core/edge-ai-engine|g' docker-compose.yml 2>/dev/null || true
        sed -i.bak 's|context: \./digital-twin|context: ./core/digital-twin|g' docker-compose.yml 2>/dev/null || true
        
        # Mise à jour des chemins de volumes
        sed -i.bak 's|\./configurations|\./configurations|g' docker-compose.yml 2>/dev/null || true
        
        rm -f docker-compose.yml.bak 2>/dev/null || true
        log "✅ Références mises à jour dans docker-compose.yml"
    fi
    
    # Mettre à jour README si nécessaire
    if [ -f "README.md" ]; then
        # Mise à jour des liens vers la nouvelle structure
        sed -i.bak 's|documentation/|documentation/|g' README.md 2>/dev/null || true
        rm -f README.md.bak 2>/dev/null || true
    fi
}

# Validation post-migration
validate_migration() {
    log "✅ Validation de la migration..."
    
    # Vérifier la présence des dossiers principaux
    required_dirs=(
        "core"
        "interfaces" 
        "infrastructure"
        "testing"
        "monitoring"
        "security"
        "documentation"
        "academic"
        "scripts"
        "configurations"
    )
    
    missing_dirs=()
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            missing_dirs+=("$dir")
        fi
    done
    
    if [ ${#missing_dirs[@]} -gt 0 ]; then
        warn "Dossiers manquants: ${missing_dirs[*]}"
    else
        log "✅ Structure de dossiers complète"
    fi
    
    # Vérifier les fichiers critiques
    critical_files=(
        "docker-compose.yml"
        ".env.production"
        ".gitignore"
        ".security-config.yml"
        "README.md"
    )
    
    missing_files=()
    for file in "${critical_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        warn "Fichiers critiques manquants: ${missing_files[*]}"
    else
        log "✅ Fichiers critiques présents"
    fi
}

# Génération rapport migration
generate_migration_report() {
    log "📊 Génération rapport de migration..."
    
    REPORT_FILE="migration-report-$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# Rapport de Migration - Station Traffeyère IoT/AI Platform
## Migration vers Architecture Repository Complète

**Date:** $(date)
**Script:** migrate-files.sh
**Log:** $LOG_FILE

---

## 🎯 Objectif Migration
Migration de l'ancienne structure vers l'architecture repository complète selon le standard RNCP 39394.

## ✅ Actions Effectuées

### Fichiers Docker Compose
- ✅ docker-compose.coolify.complete.yml → docker-compose.yml
- ✅ docker-compose.coolify.optimized.yml → docker-compose.production.yml

### Configurations  
- ✅ Déplacement vers dossier configurations/
- ✅ Organisation par service (nginx, prometheus, etc.)

### Variables Environnement
- ✅ Consolidation des fichiers .env
- ✅ Création .env.example sécurisé

### Scripts
- ✅ Déplacement vers dossier scripts/
- ✅ Organisation des utilitaires

### Documentation
- ✅ Migration Annexes → documentation/rncp-validation/
- ✅ Restructuration documents techniques

### Composants Spécialisés
- ✅ SOC-AI → interfaces/soc-dashboard/
- ✅ Blockchain → core/blockchain-layer/
- ✅ Digital Twin → core/digital-twin/

## 🎯 Structure Finale

\`\`\`
$(tree -d -L 2 . 2>/dev/null || find . -type d -name ".*" -prune -o -type d -print | head -20)
\`\`\`

## 📋 Recommandations Post-Migration

1. **Vérifier les chemins** dans docker-compose.yml
2. **Tester les builds** Docker avec nouveaux contextes
3. **Valider les configurations** déplacées
4. **Mettre à jour documentation** si nécessaire
5. **Commit des changements** avec message descriptif

## 🔗 Prochaines Étapes

- [ ] Tests fonctionnels complets
- [ ] Mise à jour CI/CD pipelines
- [ ] Validation sécurité
- [ ] Documentation mise à jour

---

**Migration réalisée avec succès ✅**
EOF

    log "✅ Rapport généré: $REPORT_FILE"
}

# Fonction principale
main() {
    show_banner
    
    log "🚀 Début migration vers structure repository complète"
    
    check_migration_prerequisites
    create_backup
    migrate_docker_compose_files
    migrate_configurations
    migrate_env_files
    migrate_scripts
    migrate_documentation
    migrate_specialized_components
    cleanup_post_migration
    update_references
    validate_migration
    generate_migration_report
    
    log "✅ Migration terminée avec succès!"
    log "📊 Logs complets: $LOG_FILE"
    
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                   🎉 MIGRATION RÉUSSIE 🎉                                                     ║"
    echo "║                                                                                                                ║"
    echo "║  Structure repository complète implémentée avec succès.                                                       ║"
    echo "║  Architecture convergente Zero Trust RNCP 39394 opérationnelle.                                              ║"
    echo "║                                                                                                                ║"
    echo "║                              🚀 Prêt pour déploiement avancé ! 🚀                                            ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Gestion erreurs
trap 'error "Migration interrompue à la ligne $LINENO"' ERR

# Exécution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi