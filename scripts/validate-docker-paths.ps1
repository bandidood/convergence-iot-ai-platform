# ================================================================
# SCRIPT DE VALIDATION DES CHEMINS DOCKER COMPOSE
# Station Traffeyère IoT/AI Platform
# ================================================================

param(
    [switch]$Fix = $false
)

# Couleurs pour output
$Global:GREEN = "`e[32m"
$Global:RED = "`e[31m"
$Global:YELLOW = "`e[33m"
$Global:BLUE = "`e[34m"
$Global:NC = "`e[0m"  # No Color

function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Color = $Global:NC
    )
    Write-Host "$Color$Message$Global:NC"
}

function Test-DockerComposePaths {
    Write-ColoredOutput "🔍 Validation des chemins Docker Compose..." $Global:BLUE
    Write-ColoredOutput ""
    
    # Fichiers Docker Compose à vérifier
    $dockerComposeFiles = @(
        "docker-compose.yml",
        "docker-compose.production.yml",
        "docker-compose.security.yml",
        "docker-compose.monitoring.yml",
        "docker-compose.override.yml"
    )
    
    $allValid = $true
    $pathIssues = @()
    
    foreach ($file in $dockerComposeFiles) {
        if (Test-Path $file) {
            Write-ColoredOutput "📄 Vérification: $file" $Global:BLUE
            
            # Lecture du contenu
            $content = Get-Content $file -Raw
            
            # Patterns de chemins à vérifier
            $pathChecks = @{
                "./config/" = "./configurations/"
                "./database/init:" = "./database/init-scripts:"
                "./monitoring/prometheus/" = "./configurations/prometheus/"
                "./monitoring/grafana/" = "./configurations/grafana/"
                "./secrets/" = "./security/secrets/"
                "./certs/" = "./configurations/certificates/"
            }
            
            $fileValid = $true
            
            foreach ($oldPath in $pathChecks.Keys) {
                $newPath = $pathChecks[$oldPath]
                
                if ($content -match [regex]::Escape($oldPath)) {
                    Write-ColoredOutput "  ❌ Ancien chemin trouvé: $oldPath" $Global:RED
                    Write-ColoredOutput "     → Devrait être: $newPath" $Global:YELLOW
                    
                    $pathIssues += @{
                        File = $file
                        OldPath = $oldPath
                        NewPath = $newPath
                    }
                    $fileValid = $false
                    $allValid = $false
                }
            }
            
            if ($fileValid) {
                Write-ColoredOutput "  ✅ Tous les chemins sont corrects" $Global:GREEN
            }
            
            Write-ColoredOutput ""
        } else {
            Write-ColoredOutput "⚠️ Fichier non trouvé: $file" $Global:YELLOW
        }
    }
    
    return @{
        Valid = $allValid
        Issues = $pathIssues
    }
}

function Test-DirectoryStructure {
    Write-ColoredOutput "🏗️ Vérification de la structure des répertoires..." $Global:BLUE
    
    # Répertoires requis
    $requiredDirs = @(
        "configurations",
        "configurations/nginx",
        "configurations/prometheus", 
        "configurations/grafana",
        "configurations/mosquitto",
        "configurations/redis",
        "configurations/vault",
        "configurations/certificates",
        "database/init-scripts",
        "environments",
        "security/secrets",
        "scripts",
        "interfaces/soc-dashboard"
    )
    
    $allExist = $true
    
    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir -PathType Container) {
            Write-ColoredOutput "  ✅ $dir" $Global:GREEN
        } else {
            Write-ColoredOutput "  ❌ Manquant: $dir" $Global:RED
            $allExist = $false
            
            if ($Fix) {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
                Write-ColoredOutput "     → Créé automatiquement" $Global:YELLOW
            }
        }
    }
    
    return $allExist
}

function Test-ConfigurationFiles {
    Write-ColoredOutput "📋 Vérification des fichiers de configuration..." $Global:BLUE
    
    # Fichiers de configuration requis
    $configFiles = @{
        "configurations/mosquitto/mosquitto.conf" = "Configuration MQTT"
        "configurations/prometheus/prometheus.yml" = "Configuration Prometheus"
        "configurations/grafana/grafana.ini" = "Configuration Grafana"
        "configurations/redis/redis.conf" = "Configuration Redis"
        ".env" = "Variables d'environnement principales"
        "environments/.env.example" = "Template variables d'environnement"
    }
    
    $allExist = $true
    
    foreach ($file in $configFiles.Keys) {
        $description = $configFiles[$file]
        
        if (Test-Path $file) {
            Write-ColoredOutput "  ✅ $file ($description)" $Global:GREEN
        } else {
            Write-ColoredOutput "  ⚠️ Manquant: $file ($description)" $Global:YELLOW
            $allExist = $false
        }
    }
    
    return $allExist
}

function Show-Summary {
    param(
        [hashtable]$ValidationResult,
        [bool]$DirectoryStructureValid,
        [bool]$ConfigFilesValid
    )
    
    Write-ColoredOutput "📊 RÉSUMÉ DE LA VALIDATION" $Global:BLUE
    Write-ColoredOutput "=========================" $Global:BLUE
    
    if ($ValidationResult.Valid) {
        Write-ColoredOutput "✅ Chemins Docker Compose: VALIDES" $Global:GREEN
    } else {
        Write-ColoredOutput "❌ Chemins Docker Compose: ERREURS DÉTECTÉES" $Global:RED
        Write-ColoredOutput "   Nombre d'issues: $($ValidationResult.Issues.Count)" $Global:YELLOW
    }
    
    if ($DirectoryStructureValid) {
        Write-ColoredOutput "✅ Structure des répertoires: VALIDE" $Global:GREEN
    } else {
        Write-ColoredOutput "❌ Structure des répertoires: INCOMPLÈTE" $Global:RED
    }
    
    if ($ConfigFilesValid) {
        Write-ColoredOutput "✅ Fichiers de configuration: PRÉSENTS" $Global:GREEN
    } else {
        Write-ColoredOutput "⚠️ Fichiers de configuration: PARTIELS" $Global:YELLOW
    }
    
    Write-ColoredOutput ""
    
    if ($ValidationResult.Valid -and $DirectoryStructureValid) {
        Write-ColoredOutput "🎉 VALIDATION RÉUSSIE - Prêt pour le déploiement!" $Global:GREEN
        return 0
    } else {
        Write-ColoredOutput "🔧 ACTIONS REQUISES - Voir les détails ci-dessus" $Global:YELLOW
        return 1
    }
}

# Script principal
Write-ColoredOutput "🔍 VALIDATION ARCHITECTURE DOCKER COMPOSE" $Global:BLUE
Write-ColoredOutput "Station Traffeyère IoT/AI Platform - RNCP 39394" $Global:BLUE
Write-ColoredOutput "=" * 50 $Global:BLUE
Write-ColoredOutput ""

# Test 1: Validation des chemins Docker Compose
$pathValidation = Test-DockerComposePaths

# Test 2: Structure des répertoires
$dirStructureValid = Test-DirectoryStructure

# Test 3: Fichiers de configuration
$configFilesValid = Test-ConfigurationFiles

# Résumé final
$exitCode = Show-Summary -ValidationResult $pathValidation -DirectoryStructureValid $dirStructureValid -ConfigFilesValid $configFilesValid

if ($Fix -and -not $pathValidation.Valid) {
    Write-ColoredOutput ""
    Write-ColoredOutput "💡 Pour corriger les chemins Docker Compose automatiquement:" $Global:BLUE
    Write-ColoredOutput "   Utilisez un editeur de texte pour remplacer les chemins obsoletes" $Global:YELLOW
}

exit $exitCode