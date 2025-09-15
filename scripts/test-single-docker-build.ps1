# ================================================================
# TEST D'UN BUILD DOCKER UNIQUE
# Station Traffeyere IoT/AI Platform - RNCP 39394
# Script simple pour tester un build Docker individuel
# ================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,
    [string]$Context = ".",
    [string]$Dockerfile = "Dockerfile",
    [switch]$ShowOutput = $false,
    [int]$TimeoutSeconds = 300
)

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  DOCKER BUILD SINGLE TEST" -ForegroundColor Cyan
Write-Host "  Station Traffeyere IoT/AI Platform - RNCP 39394" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Service: $ServiceName" -ForegroundColor Yellow
Write-Host "Context: $Context" -ForegroundColor Yellow
Write-Host "Dockerfile: $Dockerfile" -ForegroundColor Yellow
Write-Host ""

function Write-TestLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "ERROR"   { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "INFO"    { Write-Host $logEntry -ForegroundColor White }
        default   { Write-Host $logEntry }
    }
}

# Test des prérequis
function Test-BuildPrerequisites {
    Write-TestLog "Vérification des prérequis..." "INFO"
    
    # Vérifier Docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-TestLog "Docker non disponible" "ERROR"
        return $false
    }
    
    # Vérifier le contexte
    if (-not (Test-Path $Context)) {
        Write-TestLog "Contexte non trouvé: $Context" "ERROR"
        return $false
    }
    
    # Vérifier le Dockerfile
    $dockerfilePath = Join-Path $Context $Dockerfile
    if (-not (Test-Path $dockerfilePath)) {
        Write-TestLog "Dockerfile non trouvé: $dockerfilePath" "ERROR"
        return $false
    }
    
    Write-TestLog "Prérequis validés" "SUCCESS"
    return $true
}

# Exécution du build
function Start-DockerBuild {
    Write-TestLog "Démarrage du build Docker..." "INFO"
    
    $imageName = "station-traffeyere-test:$ServiceName"
    $startTime = Get-Date
    
    try {
        # Construction de la commande
        $buildArgs = @(
            "build",
            "-t", $imageName,
            "-f", (Join-Path $Context $Dockerfile),
            $Context
        )
        
        Write-TestLog "Commande: docker $($buildArgs -join ' ')" "INFO"
        
        # Exécution avec capture de sortie
        if ($ShowOutput) {
            $output = & docker @buildArgs
            $success = $LASTEXITCODE -eq 0
        } else {
            $output = & docker @buildArgs 2>&1
            $success = $LASTEXITCODE -eq 0
        }
        
        $buildTime = (Get-Date) - $startTime
        
        if ($success) {
            Write-TestLog "Build réussi en $($buildTime.TotalSeconds.ToString('F2'))s" "SUCCESS"
            
            # Informations sur l'image créée
            $imageInfo = docker inspect $imageName | ConvertFrom-Json
            $imageSize = [math]::Round($imageInfo[0].Size / 1MB, 2)
            $imageLayers = $imageInfo[0].RootFS.Layers.Count
            
            Write-TestLog "Image créée: $imageName" "SUCCESS"
            Write-TestLog "Taille: ${imageSize}MB" "INFO"
            Write-TestLog "Layers: $imageLayers" "INFO"
            
            return @{
                Success = $true
                BuildTime = $buildTime.TotalSeconds
                ImageName = $imageName
                Size = $imageSize
                Layers = $imageLayers
                Output = $output -join "`n"
            }
        } else {
            Write-TestLog "Build échoué après $($buildTime.TotalSeconds.ToString('F2'))s" "ERROR"
            if ($ShowOutput) {
                Write-TestLog "Sortie d'erreur:" "ERROR"
                Write-Host ($output -join "`n") -ForegroundColor Red
            }
            
            return @{
                Success = $false
                BuildTime = $buildTime.TotalSeconds
                Error = $output -join "`n"
            }
        }
        
    } catch {
        $buildTime = (Get-Date) - $startTime
        Write-TestLog "Exception: $($_.Exception.Message)" "ERROR"
        
        return @{
            Success = $false
            BuildTime = $buildTime.TotalSeconds
            Error = $_.Exception.Message
        }
    }
}

# Test de démarrage rapide de l'image
function Test-ImageStartup {
    param([string]$ImageName)
    
    Write-TestLog "Test démarrage de l'image..." "INFO"
    
    try {
        # Essai de démarrage rapide
        $containerName = "$ServiceName-test-$(Get-Random)"
        
        $startResult = docker run -d --name $containerName --rm $ImageName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Start-Sleep 3  # Attendre 3 secondes
            
            $containerStatus = docker ps -f "name=$containerName" --format "{{.Status}}" 2>$null
            
            if ($containerStatus) {
                Write-TestLog "Conteneur démarré avec succès: $containerStatus" "SUCCESS"
                docker stop $containerName 2>$null | Out-Null
                return $true
            } else {
                Write-TestLog "Conteneur n'a pas survécu au démarrage" "WARNING"
                return $false
            }
        } else {
            Write-TestLog "Échec démarrage conteneur: $startResult" "WARNING"
            return $false
        }
        
    } catch {
        Write-TestLog "Erreur test démarrage: $($_.Exception.Message)" "WARNING"
        return $false
    }
}

# === SCRIPT PRINCIPAL ===

Write-TestLog "Début test build pour service: $ServiceName" "INFO"

# Étape 1: Prérequis
if (-not (Test-BuildPrerequisites)) {
    Write-TestLog "Prérequis non satisfaits - Arrêt" "ERROR"
    exit 1
}

# Étape 2: Build
$buildResult = Start-DockerBuild

if ($buildResult.Success) {
    Write-TestLog "========================================" "SUCCESS"
    Write-TestLog "BUILD RÉUSSI !" "SUCCESS" 
    Write-TestLog "Service: $ServiceName" "INFO"
    Write-TestLog "Temps: $($buildResult.BuildTime.ToString('F2'))s" "INFO"
    Write-TestLog "Taille: $($buildResult.Size)MB" "INFO"
    Write-TestLog "Layers: $($buildResult.Layers)" "INFO"
    Write-TestLog "========================================" "SUCCESS"
    
    # Étape 3: Test démarrage
    $startupSuccess = Test-ImageStartup -ImageName $buildResult.ImageName
    
    if ($startupSuccess) {
        Write-TestLog "✅ Test complet réussi - Image opérationnelle" "SUCCESS"
        exit 0
    } else {
        Write-TestLog "⚠️ Build OK mais problème de démarrage" "WARNING"
        exit 2
    }
    
} else {
    Write-TestLog "========================================" "ERROR"
    Write-TestLog "BUILD ÉCHOUÉ !" "ERROR"
    Write-TestLog "Service: $ServiceName" "ERROR"
    Write-TestLog "Temps: $($buildResult.BuildTime.ToString('F2'))s" "ERROR"
    Write-TestLog "========================================" "ERROR"
    
    if ($ShowOutput -and $buildResult.Error) {
        Write-TestLog "Détails de l'erreur:" "ERROR"
        Write-Host $buildResult.Error -ForegroundColor Red
    }
    
    exit 1
}