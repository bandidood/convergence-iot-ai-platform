# ================================================================
# SCRIPT DE MIGRATION - ARCHITECTURE REPOSITORY COMPLETE
# Station Traffeyere IoT/AI Platform
# ================================================================

param(
    [switch]$DryRun = $false
)

# Variables globales
$LogFile = "migration-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$ReportFile = "MIGRATION-REPORT-$(Get-Date -Format 'yyyyMMdd').md"
$BackupDir = "migration-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Fonction de logging
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logEntry
    
    switch ($Level) {
        "ERROR"   { Write-Host $Message -ForegroundColor Red }
        "WARNING" { Write-Host $Message -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $Message -ForegroundColor Green }
        default   { Write-Host $Message }
    }
}

# Affichage de la bannière
function Show-Banner {
    Clear-Host
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "   MIGRATION ARCHITECTURE REPOSITORY COMPLETE" -ForegroundColor Cyan
    Write-Host "   Station Traffeyere IoT/AI Platform" -ForegroundColor Cyan
    Write-Host "   Architecture Zero Trust RNCP 39394" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    $mode = if ($DryRun) { "SIMULATION (DRY RUN)" } else { "EXECUTION REELLE" }
    Write-Host "Mode: $mode" -ForegroundColor Yellow
    Write-Host ""
}

# Test des prérequis
function Test-MigrationPrerequisites {
    Write-Log "Vérification des prérequis migration" "INFO"
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Log "Docker non disponible - optionnel" "WARNING"
    }
    
    if (-not (Test-Path ".git")) {
        Write-Log "Dépôt Git non détecté - optionnel" "WARNING"
    }
    
    Write-Log "Prérequis vérifiés" "SUCCESS"
}

# Création sauvegarde
function New-Backup {
    if ($DryRun) {
        Write-Log "[DRY RUN] Création sauvegarde: $BackupDir" "INFO"
        return $null
    }
    
    Write-Log "Création sauvegarde: $BackupDir" "INFO"
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    
    # Sauvegarder fichiers importants
    $filesToBackup = @(
        "docker-compose*.yml",
        "*.env",
        "configurations/*",
        "scripts/*"
    )
    
    foreach ($pattern in $filesToBackup) {
        $files = Get-ChildItem $pattern -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            if (Test-Path $file.FullName) {
                $destPath = Join-Path $BackupDir $file.Name
                Copy-Item $file.FullName $destPath -Force
                Write-Log "Sauvegarde: $($file.Name)" "SUCCESS"
            }
        }
    }
    
    return $BackupDir
}

# Migration fichiers Docker Compose
function Move-DockerComposeFiles {
    Write-Log "Migration fichiers Docker Compose" "INFO"
    
    $mapping = @{
        "docker-compose.coolify.complete.yml" = "docker-compose.yml"
        "docker-compose.coolify.optimized.yml" = "docker-compose.production.yml"
    }
    
    foreach ($source in $mapping.Keys) {
        $target = $mapping[$source]
        
        if (Test-Path $source) {
            if ($DryRun) {
                Write-Log "[DRY RUN] $source -> $target" "INFO"
            } else {
                Move-Item $source $target -Force
                Write-Log "Déplacé: $source -> $target" "SUCCESS"
            }
        } else {
            Write-Log "Fichier non trouvé: $source" "WARNING"
        }
    }
}

# Migration configurations
function Move-Configurations {
    Write-Log "Migration configurations" "INFO"
    
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path "configurations" -Force | Out-Null
    }
    
    $configFiles = Get-ChildItem "*.conf", "*.config", "*-config.yml" -ErrorAction SilentlyContinue
    
    foreach ($file in $configFiles) {
        $destPath = "configurations/$($file.Name)"
        if ($DryRun) {
            Write-Log "[DRY RUN] $($file.Name) -> $destPath" "INFO"
        } else {
            Move-Item $file.FullName $destPath -Force
            Write-Log "Configuration déplacée: $destPath" "SUCCESS"
        }
    }
}

# Migration variables environnement
function Move-EnvFiles {
    Write-Log "Migration fichiers environnement" "INFO"
    
    $envFiles = Get-ChildItem ".env*" -ErrorAction SilentlyContinue
    $targetDir = "environments"
    
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    
    foreach ($file in $envFiles) {
        if ($file.Name -eq ".env") {
            continue # Garder .env à la racine
        }
        
        $destPath = "$targetDir/$($file.Name)"
        if ($DryRun) {
            Write-Log "[DRY RUN] $($file.Name) -> $destPath" "INFO"
        } else {
            Move-Item $file.FullName $destPath -Force
            Write-Log "Fichier env déplacé: $destPath" "SUCCESS"
        }
    }
}

# Migration scripts
function Move-Scripts {
    Write-Log "Migration scripts" "INFO"
    
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path "scripts/utilities" -Force | Out-Null
    }
    
    $scriptFiles = Get-ChildItem "*.sh", "*.ps1", "*.py" -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne "migrate-files-clean.ps1" }
    
    foreach ($file in $scriptFiles) {
        $destPath = "scripts/$($file.Name)"
        if ($DryRun) {
            Write-Log "[DRY RUN] $($file.Name) -> $destPath" "INFO"
        } else {
            if (-not (Test-Path $destPath)) {
                Move-Item $file.FullName $destPath -Force
                Write-Log "Script déplacé: $destPath" "SUCCESS"
            }
        }
    }
}

# Migration documentation
function Move-Documentation {
    Write-Log "Migration documentation" "INFO"
    
    $docDirs = @{
        "Annexes" = "documentation/rncp-validation"
        "docs" = "documentation/technical"
    }
    
    foreach ($source in $docDirs.Keys) {
        $target = $docDirs[$source]
        
        if (Test-Path $source) {
            if ($DryRun) {
                Write-Log "[DRY RUN] $source -> $target" "INFO"
            } else {
                New-Item -ItemType Directory -Path $target -Force | Out-Null
                Get-ChildItem $source -Recurse | ForEach-Object {
                    $relativePath = $_.FullName.Replace((Get-Item $source).FullName, "")
                    $destPath = Join-Path $target $relativePath.TrimStart("\")
                    $destDir = Split-Path $destPath -Parent
                    
                    if (-not (Test-Path $destDir)) {
                        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                    }
                    
                    Copy-Item $_.FullName $destPath -Force
                }
                Remove-Item $source -Recurse -Force
                Write-Log "Documentation déplacée: $source -> $target" "SUCCESS"
            }
        }
    }
}

# Migration composants spécialisés
function Move-SpecializedComponents {
    Write-Log "Migration composants spécialisés" "INFO"
    
    $mapping = @{
        "SOC-AI" = "interfaces/soc-dashboard"
        "blockchain" = "core/blockchain-layer"
        "digital-twin" = "core/digital-twin"
    }
    
    foreach ($source in $mapping.Keys) {
        $target = $mapping[$source]
        
        if (Test-Path $source) {
            if ($DryRun) {
                Write-Log "[DRY RUN] $source -> $target" "INFO"
            } else {
                New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
                Move-Item $source $target -Force
                Write-Log "Composant déplacé: $source -> $target" "SUCCESS"
            }
        }
    }
}

# Nettoyage post-migration
function Clear-PostMigration {
    Write-Log "Nettoyage post-migration" "INFO"
    
    $filesToRemove = @(
        "*.old",
        "*.bak",
        "temp*",
        "*.tmp"
    )
    
    foreach ($pattern in $filesToRemove) {
        $files = Get-ChildItem $pattern -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            if ($DryRun) {
                Write-Log "[DRY RUN] Suppression: $($file.Name)" "INFO"
            } else {
                Remove-Item $file.FullName -Force
                Write-Log "Supprimé: $($file.Name)" "SUCCESS"
            }
        }
    }
}

# Génération rapport
function New-MigrationReport {
    Write-Log "Génération rapport migration" "INFO"
    
    $reportContent = @"
# RAPPORT DE MIGRATION

**Date:** $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")
**Script:** migrate-files-clean.ps1
**Log:** $LogFile
**Mode:** $(if ($DryRun) { "DRY RUN (Simulation)" } else { "EXECUTION REELLE" })

## Objectif
Migration vers architecture repository complète selon RNCP 39394.

## Actions Effectuées
- Migration fichiers Docker Compose
- Réorganisation configurations
- Déplacement scripts et documentation
- Migration composants spécialisés
- Nettoyage post-migration

## Structure Finale
$(Get-ChildItem -Directory | Select-Object Name | Format-Table -HideTableHeaders | Out-String)

## Recommandations Post-Migration
1. Vérifier les chemins dans docker-compose.yml
2. Tester les builds Docker
3. Valider les configurations
4. Mettre à jour la documentation
5. Commit des changements

**Migration terminée avec succès**
"@

    if (-not $DryRun) {
        $reportContent | Out-File $ReportFile -Encoding UTF8
    }
    Write-Log "Rapport généré: $ReportFile" "SUCCESS"
}

# Fonction principale
function Invoke-Migration {
    Show-Banner
    
    Write-Log "Début migration vers structure repository complète" "INFO"
    if ($DryRun) {
        Write-Log "MODE DRY RUN ACTIVÉ - Aucune modification réelle" "WARNING"
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
    New-MigrationReport
    
    Write-Log "Migration terminée avec succès!" "SUCCESS"
    Write-Log "Logs complets: $LogFile" "INFO"
    
    if ($backupDir) {
        Write-Log "Sauvegarde disponible: $backupDir" "INFO"
    }
    
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "           MIGRATION REUSSIE" -ForegroundColor Green
    Write-Host "   Structure repository complète implémentée" -ForegroundColor Green
    Write-Host "   Prêt pour déploiement avancé!" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
}

# Gestion erreurs
trap {
    Write-Log "Migration interrompue: $($_.Exception.Message)" "ERROR"
    exit 1
}

# Exécution
Invoke-Migration