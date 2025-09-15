# =============================================================================
# SCRIPT DE MIGRATION FICHIERS - STATION TRAFFEYÈRE IoT/AI PLATFORM
# Migration vers structure repository complète - RNCP 39394
# Version PowerShell pour Windows
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$CreateBackup = $true
)

# Configuration
$ErrorActionPreference = "Stop"
$LogFile = "migration-log-$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

# Fonctions utilitaires
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $coloredMessage = switch ($Level) {
        "INFO" { Write-Host "[$timestamp] [INFO] $Message" -ForegroundColor Blue }
        "SUCCESS" { Write-Host "[$timestamp] [SUCCESS] $Message" -ForegroundColor Green }
        "WARNING" { Write-Host "[$timestamp] [WARNING] $Message" -ForegroundColor Yellow }
        "ERROR" { Write-Host "[$timestamp] [ERROR] $Message" -ForegroundColor Red }
    }
    "[$timestamp] [$Level] $Message" | Out-File -FilePath $LogFile -Append
}

function Show-Banner {
    Write-Host @"
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                          📦 MIGRATION FICHIERS STATION TRAFFEYÈRE 📦                                       ║
║                                                                                                              ║
║    🔄 Réorganisation vers Architecture Repository Complète                                                  ║
║    📚 Projet RNCP 39394 - Expert en Systèmes d'Information et Sécurité                                     ║
║                                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Green
}

# Vérification prérequis migration
function Test-MigrationPrerequisites {
    Write-Log "🔍 Vérification prérequis migration..." "INFO"
    
    # Vérifier que nous sommes dans le bon répertoire
    if (-not (Test-Path ".git")) {
        Write-Log "Pas de repository Git détecté. Exécutez ce script depuis la racine du projet." "ERROR"
        exit 1
    }
    
    # Vérifier la présence de fichiers à migrer
    if (-not (Test-Path "docker-compose.coolify.complete.yml") -and -not (Test-Path "core")) {
        Write-Log "Aucun fichier de l'ancienne structure détecté." "WARNING"
    }
    
    Write-Log "✅ Prérequis migration validés" "SUCCESS"
}

# Sauvegarde avant migration
function New-Backup {
    if (-not $CreateBackup) {
        Write-Log "Sauvegarde ignorée (paramètre -CreateBackup:$false)" "WARNING"
        return
    }
    
    Write-Log "💾 Création sauvegarde avant migration..." "INFO"
    
    $BackupDir = "migration-backup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    
    # Sauvegarde des fichiers importants
    $FilesToBackup = @(
        "docker-compose.coolify.complete.yml",
        "docker-compose.coolify.optimized.yml",
        ".env",
        ".env.production",
        ".env.production.optimized",
        "deploy-complete-advanced.ps1",
        "README.md"
    )
    
    foreach ($file in $FilesToBackup) {
        if (Test-Path $file) {
            Copy-Item $file $BackupDir -Force
            Write-Log "Sauvegardé: $file" "INFO"
        }
    }
    
    Write-Log "✅ Sauvegarde créée dans: $BackupDir" "SUCCESS"
    return $BackupDir
}

# Migration des fichiers Docker Compose
function Move-DockerComposeFiles {
    Write-Log "🐳 Migration des fichiers Docker Compose..." "INFO"
    
    # Renommer et organiser les fichiers Docker Compose
    if (Test-Path "docker-compose.coolify.complete.yml") {
        if ($DryRun) {
            Write-Log "[DRY RUN] docker-compose.coolify.complete.yml → docker-compose.yml" "INFO"
        } else {
            if (Test-Path "docker-compose.yml") {
                Write-Log "docker-compose.yml existe déjà, renommage en docker-compose.yml.backup" "WARNING"
                Move-Item "docker-compose.yml" "docker-compose.yml.backup" -Force
            }
            Move-Item "docker-compose.coolify.complete.yml" "docker-compose.yml" -Force
            Write-Log "✅ docker-compose.coolify.complete.yml → docker-compose.yml" "SUCCESS"
        }
    }
    
    if (Test-Path "docker-compose.coolify.optimized.yml") {
        if ($DryRun) {
            Write-Log "[DRY RUN] docker-compose.coolify.optimized.yml → docker-compose.production.yml" "INFO"
        } else {
            Move-Item "docker-compose.coolify.optimized.yml" "docker-compose.production.yml" -Force
            Write-Log "✅ docker-compose.coolify.optimized.yml → docker-compose.production.yml" "SUCCESS"
        }
    }
}

# Migration des configurations
function Move-Configurations {
    Write-Log "⚙️ Migration des configurations..." "INFO"
    
    # Déplacer configurations existantes
    $ConfigMigrations = @{
        "mosquitto.conf" = "configurations/mosquitto/mosquitto.conf"
        "nginx.conf" = "configurations/nginx/nginx.conf"
        "prometheus.yml" = "configurations/prometheus/prometheus.yml"
    }
    
    foreach ($migration in $ConfigMigrations.GetEnumerator()) {
        $source = $migration.Key
        $dest = $migration.Value
        
        if (Test-Path $source) {
            $destDir = Split-Path $dest -Parent
            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            
            if ($DryRun) {
                Write-Log "[DRY RUN] $source → $dest" "INFO"
            } else {
                Move-Item $source $dest -Force
                Write-Log "✅ $source → $dest" "SUCCESS"
            }
        }
    }
}

# Migration des variables d'environnement
function Move-EnvFiles {
    Write-Log "🔧 Migration des variables d'environnement..." "INFO"
    
    # Consolidation des fichiers .env
    if ((Test-Path ".env.production.optimized") -and -not (Test-Path ".env.production")) {
        if ($DryRun) {
            Write-Log "[DRY RUN] .env.production.optimized → .env.production" "INFO"
        } else {
            Move-Item ".env.production.optimized" ".env.production" -Force
            Write-Log "✅ .env.production.optimized → .env.production" "SUCCESS"
        }
    }
    
    # Création fichier .env.example à partir du .env existant
    if ((Test-Path ".env.production") -and -not (Test-Path ".env.example")) {
        if ($DryRun) {
            Write-Log "[DRY RUN] Création .env.example à partir de .env.production" "INFO"
        } else {
            $envContent = Get-Content ".env.production"
            $exampleContent = $envContent -replace "=.*", "=CHANGE_ME"
            $exampleContent | Out-File ".env.example" -Encoding UTF8
            Write-Log "✅ Création .env.example à partir de .env.production" "SUCCESS"
        }
    }
}

# Migration des scripts
function Move-Scripts {
    Write-Log "📜 Migration des scripts..." "INFO"
    
    # Déplacer les scripts vers le dossier scripts
    $ScriptsToMigrate = @(
        "deploy-complete-advanced.ps1",
        "setup-environment.sh"
    )
    
    foreach ($script in $ScriptsToMigrate) {
        if (Test-Path $script) {
            $destPath = "scripts/$script"
            
            if ($DryRun) {
                Write-Log "[DRY RUN] $script → scripts/" "INFO"
            } else {
                # Si le fichier n'existe pas déjà dans scripts/
                if (-not (Test-Path $destPath)) {
                    Move-Item $script "scripts/" -Force
                    Write-Log "✅ $script → scripts/" "SUCCESS"
                } else {
                    Write-Log "$script existe déjà dans scripts/, gardé comme backup" "WARNING"
                    Move-Item $script "scripts/$script.backup" -Force
                }
            }
        }
    }
}

# Migration des documentations
function Move-Documentation {
    Write-Log "📚 Migration de la documentation..." "INFO"
    
    # Migration des annexes vers documentation structurée
    if (Test-Path "Annexes") {
        $destDir = "documentation/rncp-validation/annexes"
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        if ($DryRun) {
            Write-Log "[DRY RUN] Annexes → documentation/rncp-validation/annexes/" "INFO"
        } else {
            Get-ChildItem "Annexes" | Move-Item -Destination $destDir -Force
            
            # Supprimer le dossier vide
            if ((Get-ChildItem "Annexes" -Force | Measure-Object).Count -eq 0) {
                Remove-Item "Annexes" -Force
            }
            
            Write-Log "✅ Annexes → documentation/rncp-validation/annexes/" "SUCCESS"
        }
    }
    
    # Migration des documents spécialisés
    $DocMigrations = @{
        "coolify_deployment_inventory.md" = "documentation/architecture/deployment-inventory.md"
        "docker_files_structure.md" = "documentation/architecture/docker-structure.md"
    }
    
    foreach ($migration in $DocMigrations.GetEnumerator()) {
        $source = $migration.Key
        $dest = $migration.Value
        
        if (Test-Path $source) {
            $destDir = Split-Path $dest -Parent
            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            
            if ($DryRun) {
                Write-Log "[DRY RUN] $source → $dest" "INFO"
            } else {
                Move-Item $source $dest -Force
                Write-Log "✅ $source → $dest" "SUCCESS"
            }
        }
    }
}

# Migration des composants spécialisés
function Move-SpecializedComponents {
    Write-Log "🔧 Migration des composants spécialisés..." "INFO"
    
    # Migration SOC-AI vers interfaces
    if (Test-Path "soc-ai") {
        $destDir = "interfaces/soc-dashboard"
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        if ($DryRun) {
            Write-Log "[DRY RUN] soc-ai → interfaces/soc-dashboard/" "INFO"
        } else {
            Get-ChildItem "soc-ai" | Move-Item -Destination $destDir -Force
            
            if ((Get-ChildItem "soc-ai" -Force | Measure-Object).Count -eq 0) {
                Remove-Item "soc-ai" -Force
            }
            
            Write-Log "✅ soc-ai → interfaces/soc-dashboard/" "SUCCESS"
        }
    }
    
    # Migration blockchain vers core/blockchain-layer
    if (Test-Path "blockchain-hyperledger") {
        $destDir = "core/blockchain-layer"
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        if ($DryRun) {
            Write-Log "[DRY RUN] blockchain-hyperledger → core/blockchain-layer/" "INFO"
        } else {
            Get-ChildItem "blockchain-hyperledger" | Move-Item -Destination $destDir -Force
            
            if ((Get-ChildItem "blockchain-hyperledger" -Force | Measure-Object).Count -eq 0) {
                Remove-Item "blockchain-hyperledger" -Force
            }
            
            Write-Log "✅ blockchain-hyperledger → core/blockchain-layer/" "SUCCESS"
        }
    }
    
    # Migration digital-twin vers core/digital-twin
    if (Test-Path "digital-twin-unity") {
        $destDir = "core/digital-twin"
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        if ($DryRun) {
            Write-Log "[DRY RUN] digital-twin-unity → core/digital-twin/" "INFO"
        } else {
            Get-ChildItem "digital-twin-unity" | Move-Item -Destination $destDir -Force
            
            if ((Get-ChildItem "digital-twin-unity" -Force | Measure-Object).Count -eq 0) {
                Remove-Item "digital-twin-unity" -Force
            }
            
            Write-Log "✅ digital-twin-unity → core/digital-twin/" "SUCCESS"
        }
    }
}

# Nettoyage post-migration
function Clear-PostMigration {
    Write-Log "🧹 Nettoyage post-migration..." "INFO"
    
    # Supprimer dossiers vides de l'ancienne structure
    $OldDirsToCheck = @(
        "ci",
        "config", 
        "data",
        "database",
        "docs",
        "logs",
        "mqtt",
        "network",
        "services",
        "volumes"
    )
    
    foreach ($dir in $OldDirsToCheck) {
        if (Test-Path $dir) {
            $itemCount = (Get-ChildItem $dir -Force | Measure-Object).Count
            if ($itemCount -eq 0) {
                if ($DryRun) {
                    Write-Log "[DRY RUN] Suppression dossier vide: $dir" "INFO"
                } else {
                    Remove-Item $dir -Force
                    Write-Log "Supprimé dossier vide: $dir" "INFO"
                }
            }
        }
    }
    
    # Nettoyer fichiers temporaires
    if (-not $DryRun) {
        Get-ChildItem -Filter "*.tmp" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path "logs" -Filter "*.log" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

# Mise à jour des références
function Update-References {
    Write-Log "🔗 Mise à jour des références..." "INFO"
    
    # Mettre à jour les chemins dans docker-compose.yml
    if (Test-Path "docker-compose.yml") {
        if ($DryRun) {
            Write-Log "[DRY RUN] Mise à jour des références dans docker-compose.yml" "INFO"
        } else {
            $content = Get-Content "docker-compose.yml" -Raw
            $content = $content -replace "context: \./edge-ai-engine", "context: ./core/edge-ai-engine"
            $content = $content -replace "context: \./digital-twin", "context: ./core/digital-twin"
            $content | Out-File "docker-compose.yml" -Encoding UTF8
            
            Write-Log "✅ Références mises à jour dans docker-compose.yml" "SUCCESS"
        }
    }
}

# Validation post-migration
function Test-Migration {
    Write-Log "✅ Validation de la migration..." "INFO"
    
    # Vérifier la présence des dossiers principaux
    $RequiredDirs = @(
        "core",
        "interfaces", 
        "infrastructure",
        "testing",
        "monitoring",
        "security",
        "documentation",
        "academic",
        "scripts",
        "configurations"
    )
    
    $missingDirs = @()
    foreach ($dir in $RequiredDirs) {
        if (-not (Test-Path $dir)) {
            $missingDirs += $dir
        }
    }
    
    if ($missingDirs.Count -gt 0) {
        Write-Log "Dossiers manquants: $($missingDirs -join ', ')" "WARNING"
    } else {
        Write-Log "✅ Structure de dossiers complète" "SUCCESS"
    }
    
    # Vérifier les fichiers critiques
    $CriticalFiles = @(
        "docker-compose.yml",
        ".env.production",
        ".gitignore",
        ".security-config.yml",
        "README.md"
    )
    
    $missingFiles = @()
    foreach ($file in $CriticalFiles) {
        if (-not (Test-Path $file)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Log "Fichiers critiques manquants: $($missingFiles -join ', ')" "WARNING"
    } else {
        Write-Log "✅ Fichiers critiques présents" "SUCCESS"
    }
}

# Génération rapport migration
function New-MigrationReport {
    Write-Log "📊 Génération rapport de migration..." "INFO"
    
    $ReportFile = "migration-report-$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
    
    $reportContent = @"
# Rapport de Migration - Station Traffeyère IoT/AI Platform
## Migration vers Architecture Repository Complète

**Date:** $(Get-Date)
**Script:** migrate-files.ps1 (PowerShell Windows)
**Log:** $LogFile
**Mode:** $(if ($DryRun) { "DRY RUN (Simulation)" } else { "EXECUTION RÉELLE" })

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

``````
$(Get-ChildItem -Directory | Select-Object Name | Format-Table -HideTableHeaders | Out-String)
``````

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
"@

    $reportContent | Out-File $ReportFile -Encoding UTF8
    Write-Log "✅ Rapport généré: $ReportFile" "SUCCESS"
}

# Fonction principale
function Invoke-Migration {
    Show-Banner
    
    Write-Log "🚀 Début migration vers structure repository complète" "INFO"
    if ($DryRun) {
        Write-Log "⚠️ MODE DRY RUN ACTIVÉ - Aucune modification réelle" "WARNING"
    }
    
    Test-MigrationPrerequisites
    $backupDir = New-Backup
    Move-DockerComposeFiles
    Move-Configurations
    Move-EnvFiles
    Move-Scripts
    Move-Documentation
    Move-SpecializedComponents
    Clear-PostMigration
    Update-References
    Test-Migration
    New-MigrationReport
    
    Write-Log "✅ Migration terminée avec succès!" "SUCCESS"
    Write-Log "📊 Logs complets: $LogFile" "INFO"
    
    if ($backupDir) {
        Write-Log "💾 Sauvegarde disponible: $backupDir" "INFO"
    }
    
    Write-Host @"

╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                   🎉 MIGRATION RÉUSSIE 🎉                                                     ║
║                                                                                                                ║
║  Structure repository complète implémentée avec succès.                                                       ║
║  Architecture convergente Zero Trust RNCP 39394 opérationnelle.                                              ║
║                                                                                                                ║
║                              🚀 Prêt pour déploiement avancé ! 🚀                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
}

# Gestion erreurs
trap {
    Write-Log "Migration interrompue: $($_.Exception.Message)" "ERROR"
    exit 1
}

# Exécution principale
Invoke-Migration
