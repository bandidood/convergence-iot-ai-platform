# ================================================================
# TEST DES SERVICES DOCKER AVEC DEPENDANCES
# Station Traffeyere IoT/AI Platform - RNCP 39394
# Test des builds nécessitant des contextes/dépendances spécifiques
# ================================================================

param(
    [switch]$TestProdServices = $true,
    [switch]$TestSecurityServices = $true,
    [switch]$TestMonitoringServices = $true,
    [switch]$SkipDependencies = $false,
    [switch]$Verbose = $false
)

# Configuration des services avec dépendances
$ServiceDependencies = @{
    'backend' = @{
        Context = './services/backend'
        Dockerfile = 'Dockerfile'
        Dependencies = @('postgres', 'redis')
        RequiredFiles = @('requirements.txt', 'app/')
        BuildArgs = @()
        HealthCheck = 'http://localhost:8000/health'
    }
    
    'frontend' = @{
        Context = './services/frontend' 
        Dockerfile = 'Dockerfile'
        Dependencies = @('backend')
        RequiredFiles = @('package.json', 'src/')
        BuildArgs = @()
        HealthCheck = 'http://localhost:3000'
    }
    
    'edge-ai-engine' = @{
        Context = './core/edge-ai-engine'
        Dockerfile = 'Dockerfile'
        Dependencies = @()
        RequiredFiles = @('src/', 'requirements.txt')
        BuildArgs = @()
        HealthCheck = 'http://localhost:8080/health'
    }
    
    'iot-data-generator' = @{
        Context = './core/iot-data-generator'
        Dockerfile = 'Dockerfile' 
        Dependencies = @('mosquitto', 'redis')
        RequiredFiles = @('src/', 'requirements.txt')
        BuildArgs = @()
        HealthCheck = 'http://localhost:8081/health'
    }
    
    'digital-twin' = @{
        Context = './core/digital-twin'
        Dockerfile = 'Dockerfile.headless'
        Dependencies = @('backend', 'redis')
        RequiredFiles = @('Assets/', 'Scripts/')
        BuildArgs = @()
        HealthCheck = 'http://localhost:8094/health'
    }
    
    'unity-digital-twin' = @{
        Context = './digital-twin-unity'
        Dockerfile = 'Dockerfile.headless'
        Dependencies = @('backend', 'redis')
        RequiredFiles = @('Assets/', 'Scripts/', 'ProjectSettings/')
        BuildArgs = @()
        HealthCheck = 'http://localhost:8095/health'
    }
    
    'voice-assistant-backend' = @{
        Context = './interfaces/voice-assistant-xia'
        Dockerfile = 'Dockerfile.backend'
        Dependencies = @('backend', 'redis')
        RequiredFiles = @('src/', 'requirements.txt')
        BuildArgs = @()
        HealthCheck = 'http://localhost:8092/health'
    }
    
    'voice-assistant-frontend' = @{
        Context = './interfaces/voice-assistant-xia'
        Dockerfile = 'Dockerfile.frontend'
        Dependencies = @('voice-assistant-backend')
        RequiredFiles = @('frontend/', 'package.json')
        BuildArgs = @()
        HealthCheck = 'http://localhost:3002'
    }
    
    'monitoring-dashboard' = @{
        Context = './monitoring/dashboard'
        Dockerfile = 'Dockerfile'
        Dependencies = @('prometheus', 'grafana')
        RequiredFiles = @('src/', 'package.json')
        BuildArgs = @()
        HealthCheck = 'http://localhost:3003'
    }
    
    'soar-engine' = @{
        Context = './core/soar-engine'
        Dockerfile = 'Dockerfile'
        Dependencies = @('vault', 'elasticsearch')
        RequiredFiles = @('src/', 'requirements.txt')
        BuildArgs = @()
        HealthCheck = 'http://localhost:8090/health'
    }
    
    'security-dashboard' = @{
        Context = './interfaces/soc-dashboard'
        Dockerfile = 'Dockerfile'
        Dependencies = @('elasticsearch', 'kibana', 'vault')
        RequiredFiles = @('src/', 'package.json')
        BuildArgs = @()
        HealthCheck = 'http://localhost:3001'
    }
    
    'custom-metrics-collector' = @{
        Context = './monitoring/custom-collector'
        Dockerfile = 'Dockerfile'
        Dependencies = @('prometheus')
        RequiredFiles = @('src/', 'requirements.txt')
        BuildArgs = @()
        HealthCheck = 'http://localhost:8000'
    }
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  DOCKER DEPENDENCY TESTING SUITE" -ForegroundColor Cyan
Write-Host "  Station Traffeyere IoT/AI Platform - RNCP 39394" -ForegroundColor Cyan  
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Testing Production Services: $TestProdServices" -ForegroundColor Yellow
Write-Host "Testing Security Services: $TestSecurityServices" -ForegroundColor Yellow  
Write-Host "Testing Monitoring Services: $TestMonitoringServices" -ForegroundColor Yellow
Write-Host ""

# Résultats des tests
$Global:TestResults = @()
$Global:DependencyIssues = @()

function Write-DependencyLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Service = "GENERAL"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] [$Service] $Message"
    
    switch ($Level) {
        "ERROR"   { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "INFO"    { Write-Host $logEntry -ForegroundColor White }
        default   { Write-Host $logEntry }
    }
    
    if ($Verbose) {
        Add-Content -Path "dependency-test-$(Get-Date -Format 'yyyyMMdd').log" -Value $logEntry
    }
}

# Vérifier les prérequis d'un service
function Test-ServicePrerequisites {
    param(
        [string]$ServiceName,
        [hashtable]$ServiceConfig
    )
    
    Write-DependencyLog "Vérification prérequis pour $ServiceName..." "INFO" $ServiceName
    
    $issues = @()
    
    # Vérifier que le contexte existe
    if (-not (Test-Path $ServiceConfig.Context)) {
        $issues += "Context directory not found: $($ServiceConfig.Context)"
        Write-DependencyLog "Context manquant: $($ServiceConfig.Context)" "ERROR" $ServiceName
    }
    
    # Vérifier le Dockerfile
    $dockerfilePath = Join-Path $ServiceConfig.Context $ServiceConfig.Dockerfile
    if (-not (Test-Path $dockerfilePath)) {
        $issues += "Dockerfile not found: $dockerfilePath"
        Write-DependencyLog "Dockerfile manquant: $dockerfilePath" "ERROR" $ServiceName
    }
    
    # Vérifier les fichiers requis
    foreach ($requiredFile in $ServiceConfig.RequiredFiles) {
        $filePath = Join-Path $ServiceConfig.Context $requiredFile
        if (-not (Test-Path $filePath)) {
            $issues += "Required file/directory missing: $filePath"
            Write-DependencyLog "Fichier requis manquant: $filePath" "WARNING" $ServiceName
        }
    }
    
    if ($issues.Count -eq 0) {
        Write-DependencyLog "Tous les prérequis sont satisfaits" "SUCCESS" $ServiceName
        return $true
    } else {
        $Global:DependencyIssues += @{
            Service = $ServiceName
            Issues = $issues
        }
        Write-DependencyLog "$($issues.Count) prérequis manquants" "ERROR" $ServiceName
        return $false
    }
}

# Créer les fichiers manquants nécessaires pour les tests
function New-MissingTestFiles {
    param(
        [string]$ServiceName,
        [hashtable]$ServiceConfig
    )
    
    Write-DependencyLog "Création fichiers de test manquants pour $ServiceName..." "INFO" $ServiceName
    
    $contextPath = $ServiceConfig.Context
    
    # Créer le répertoire de contexte s'il n'existe pas
    if (-not (Test-Path $contextPath)) {
        New-Item -ItemType Directory -Path $contextPath -Force | Out-Null
        Write-DependencyLog "Créé context directory: $contextPath" "INFO" $ServiceName
    }
    
    $dockerfilePath = Join-Path $contextPath $ServiceConfig.Dockerfile
    
    # Créer un Dockerfile de test basique s'il n'existe pas
    if (-not (Test-Path $dockerfilePath)) {
        $dockerfileContent = @"
# Dockerfile de test généré automatiquement pour $ServiceName
# Station Traffeyere IoT/AI Platform - RNCP 39394

FROM alpine:latest

# Métadonnées
LABEL maintainer="Station Traffeyere Team"
LABEL service="$ServiceName"
LABEL version="1.0.0-test"
LABEL description="Test container for $ServiceName"

# Installation outils de base
RUN apk add --no-cache curl wget

# Répertoire de travail
WORKDIR /app

# Port d'exposition par défaut
EXPOSE 8080

# Point de santé par défaut
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Commande par défaut
CMD ["echo", "Test container for $ServiceName is running"]
"@
        
        $dockerfileContent | Out-File -FilePath $dockerfilePath -Encoding UTF8
        Write-DependencyLog "Créé Dockerfile de test: $dockerfilePath" "SUCCESS" $ServiceName
    }
    
    # Créer fichiers requis manquants avec contenu minimal
    foreach ($requiredFile in $ServiceConfig.RequiredFiles) {
        $filePath = Join-Path $contextPath $requiredFile
        $fileDir = Split-Path $filePath -Parent
        
        if (-not (Test-Path $fileDir)) {
            New-Item -ItemType Directory -Path $fileDir -Force | Out-Null
        }
        
        if (-not (Test-Path $filePath)) {
            if ($requiredFile -like "*.json") {
                # Fichier package.json basique
                $content = @"
{
  "name": "$ServiceName-test",
  "version": "1.0.0-test",
  "description": "Test package for $ServiceName",
  "main": "index.js",
  "scripts": {
    "start": "echo 'Test service $ServiceName started'",
    "test": "echo 'Test passed for $ServiceName'"
  },
  "dependencies": {}
}
"@
            } elseif ($requiredFile -like "*.txt") {
                # Fichier requirements.txt basique  
                $content = @"
# Requirements de test pour $ServiceName
# Station Traffeyere IoT/AI Platform - RNCP 39394

# Dépendances minimales pour test
requests>=2.25.0
flask>=2.0.0
pytest>=6.0.0
"@
            } else {
                # Fichier générique
                $content = "# Test file for $ServiceName - Generated automatically"
            }
            
            if (Test-Path $filePath -PathType Container) {
                # C'est un répertoire, créer un fichier index
                $indexPath = Join-Path $filePath "index.py"
                "# Test index file for $ServiceName" | Out-File -FilePath $indexPath -Encoding UTF8
            } else {
                $content | Out-File -FilePath $filePath -Encoding UTF8
            }
            
            Write-DependencyLog "Créé fichier requis: $filePath" "INFO" $ServiceName
        }
    }
}

# Test de build d'un service avec ses dépendances
function Test-ServiceWithDependencies {
    param(
        [string]$ServiceName,
        [hashtable]$ServiceConfig
    )
    
    Write-DependencyLog "========================================" "INFO" $ServiceName
    Write-DependencyLog "Test du service: $ServiceName" "INFO" $ServiceName
    
    $startTime = Get-Date
    
    # Étape 1: Vérifier les prérequis
    if (-not (Test-ServicePrerequisites -ServiceName $ServiceName -ServiceConfig $ServiceConfig)) {
        if (-not $SkipDependencies) {
            Write-DependencyLog "Création des fichiers manquants..." "INFO" $ServiceName
            New-MissingTestFiles -ServiceName $ServiceName -ServiceConfig $ServiceConfig
        } else {
            Write-DependencyLog "Prérequis manquants - Service ignoré" "WARNING" $ServiceName
            return @{
                Service = $ServiceName
                Success = $false
                Reason = "Prerequisites missing"
                BuildTime = 0
            }
        }
    }
    
    # Étape 2: Build du service
    try {
        $imageName = "station-traffeyere:$ServiceName-dependency-test"
        $contextPath = $ServiceConfig.Context
        $dockerfilePath = $ServiceConfig.Dockerfile
        
        Write-DependencyLog "Build de l'image: $imageName" "INFO" $ServiceName
        Write-DependencyLog "Context: $contextPath" "INFO" $ServiceName
        Write-DependencyLog "Dockerfile: $dockerfilePath" "INFO" $ServiceName
        
        # Construction de la commande docker build
        $buildCommand = @(
            "build",
            "-t", $imageName,
            "-f", (Join-Path $contextPath $dockerfilePath),
            $contextPath
        )
        
        Write-DependencyLog "Commande: docker $($buildCommand -join ' ')" "INFO" $ServiceName
        
        # Exécution du build
        $buildOutput = docker @buildCommand 2>&1
        $buildSuccess = $LASTEXITCODE -eq 0
        
        $buildTime = (Get-Date) - $startTime
        
        if ($buildSuccess) {
            Write-DependencyLog "Build réussi en $($buildTime.TotalSeconds.ToString('F2'))s" "SUCCESS" $ServiceName
            
            # Test rapide de l'image
            Test-ImageBasicFunctionality -ImageName $imageName -ServiceName $ServiceName
            
        } else {
            Write-DependencyLog "Build échoué" "ERROR" $ServiceName
            Write-DependencyLog "Output: $($buildOutput -join '; ')" "ERROR" $ServiceName
        }
        
        return @{
            Service = $ServiceName
            Success = $buildSuccess
            BuildTime = $buildTime.TotalSeconds
            Output = $buildOutput -join "`n"
            ImageName = $imageName
            Context = $contextPath
            Dockerfile = $dockerfilePath
        }
        
    } catch {
        $buildTime = (Get-Date) - $startTime
        Write-DependencyLog "Exception durant le build: $($_.Exception.Message)" "ERROR" $ServiceName
        
        return @{
            Service = $ServiceName
            Success = $false
            BuildTime = $buildTime.TotalSeconds
            Output = $_.Exception.Message
            Error = $_.Exception
        }
    }
}

# Test basique de fonctionnalité d'une image
function Test-ImageBasicFunctionality {
    param(
        [string]$ImageName,
        [string]$ServiceName
    )
    
    Write-DependencyLog "Test de fonctionnalité basique..." "INFO" $ServiceName
    
    try {
        # Informations de l'image
        $imageInfo = docker inspect $ImageName 2>$null | ConvertFrom-Json
        
        if ($imageInfo) {
            $size = [math]::Round($imageInfo[0].Size / 1MB, 2)
            Write-DependencyLog "Taille image: ${size}MB" "INFO" $ServiceName
            
            $layers = $imageInfo[0].RootFS.Layers.Count
            Write-DependencyLog "Layers: $layers" "INFO" $ServiceName
        }
        
        # Test de démarrage rapide
        Write-DependencyLog "Test démarrage conteneur..." "INFO" $ServiceName
        
        $containerId = docker run -d --name "$ServiceName-test-container" $ImageName 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Start-Sleep 2
            
            $containerStatus = docker ps -f "name=$ServiceName-test-container" --format "{{.Status}}" 2>$null
            
            if ($containerStatus) {
                Write-DependencyLog "Container démarré: $containerStatus" "SUCCESS" $ServiceName
            }
            
            # Nettoyage
            docker stop "$ServiceName-test-container" 2>$null | Out-Null
            docker rm "$ServiceName-test-container" 2>$null | Out-Null
            
        } else {
            Write-DependencyLog "Échec démarrage container" "WARNING" $ServiceName
        }
        
    } catch {
        Write-DependencyLog "Erreur test fonctionnalité: $($_.Exception.Message)" "WARNING" $ServiceName
    }
}

# Génération du rapport de dépendances
function New-DependencyReport {
    Write-DependencyLog "Génération rapport de dépendances..." "INFO" "REPORT"
    
    $reportPath = "dependency-test-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').md"
    
    $report = @"
# 🔗 RAPPORT DE TEST DES DÉPENDANCES DOCKER

**Station Traffeyere IoT/AI Platform - RNCP 39394**  
**Date**: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")

## 📊 Résumé Exécutif

- **Services testés**: $($Global:TestResults.Count)
- **Builds réussis**: $($Global:TestResults | Where-Object {$_.Success} | Measure-Object | Select-Object -ExpandProperty Count)
- **Builds échoués**: $($Global:TestResults | Where-Object {-not $_.Success} | Measure-Object | Select-Object -ExpandProperty Count)
- **Issues de dépendances**: $($Global:DependencyIssues.Count)

## 🏗️ Résultats des Builds

| Service | Status | Temps Build | Context | Issues |
|---------|--------|-------------|---------|--------|
"@

    foreach ($result in $Global:TestResults) {
        $status = if ($result.Success) { "✅ Réussi" } else { "❌ Échoué" }
        $issues = ($Global:DependencyIssues | Where-Object {$_.Service -eq $result.Service}).Issues.Count
        $issuesText = if ($issues -gt 0) { "$issues issues" } else { "Aucune" }
        
        $report += "| $($result.Service) | $status | $($result.BuildTime.ToString('F2'))s | $($result.Context) | $issuesText |`n"
    }

    if ($Global:DependencyIssues.Count -gt 0) {
        $report += @"

## ⚠️ Issues de Dépendances Détectées

"@
        foreach ($issue in $Global:DependencyIssues) {
            $report += "### $($issue.Service)`n`n"
            foreach ($problemDescription in $issue.Issues) {
                $report += "- $problemDescription`n"
            }
            $report += "`n"
        }
    }

    $report += @"

## 📈 Recommandations

### Optimisations Immédiates
- 🔧 Corriger les dépendances manquantes avant déploiement production
- 📦 Standardiser la structure des contextes Docker
- 🐳 Implémenter des healthchecks pour tous les services

### Bonnes Pratiques
- 🎯 Utiliser des builds multi-stage pour réduire la taille des images
- 🔒 Intégrer les scans de sécurité dans les builds
- 📋 Documenter les dépendances inter-services
- ⚡ Optimiser l'ordre des layers Docker pour le cache

### Architecture
- 🌐 Considérer l'utilisation d'un registry Docker privé
- 🔄 Mettre en place un système de versioning des images
- 📊 Surveiller les métriques de build et de déploiement

---

**Rapport généré par Station Traffeyere Docker Dependency Testing Suite**
"@

    $report | Out-File -FilePath $reportPath -Encoding UTF8
    Write-DependencyLog "Rapport généré: $reportPath" "SUCCESS" "REPORT"
}

# === SCRIPT PRINCIPAL ===

Write-DependencyLog "Démarrage des tests de dépendances Docker" "INFO" "MAIN"

# Filtrer les services selon les paramètres
$servicesToTest = @()

foreach ($serviceName in $ServiceDependencies.Keys) {
    $include = $false
    
    # Services de production
    if ($TestProdServices -and $serviceName -in @('backend', 'frontend', 'edge-ai-engine', 'iot-data-generator', 'digital-twin', 'unity-digital-twin')) {
        $include = $true
    }
    
    # Services de sécurité
    if ($TestSecurityServices -and $serviceName -in @('soar-engine', 'security-dashboard', 'voice-assistant-backend', 'voice-assistant-frontend')) {
        $include = $true
    }
    
    # Services de monitoring
    if ($TestMonitoringServices -and $serviceName -in @('monitoring-dashboard', 'custom-metrics-collector')) {
        $include = $true
    }
    
    if ($include) {
        $servicesToTest += $serviceName
    }
}

Write-DependencyLog "$($servicesToTest.Count) services sélectionnés pour les tests" "INFO" "MAIN"

# Exécution des tests
foreach ($serviceName in $servicesToTest) {
    $serviceConfig = $ServiceDependencies[$serviceName]
    $result = Test-ServiceWithDependencies -ServiceName $serviceName -ServiceConfig $serviceConfig
    $Global:TestResults += $result
}

# Analyse des résultats
$successCount = ($Global:TestResults | Where-Object {$_.Success}).Count
$failCount = ($Global:TestResults | Where-Object {-not $_.Success}).Count

Write-DependencyLog "========================================" "INFO" "FINAL"
Write-DependencyLog "RÉSULTATS FINAUX" "INFO" "FINAL"
Write-DependencyLog "========================================" "INFO" "FINAL"
Write-DependencyLog "Services testés: $($Global:TestResults.Count)" "INFO" "FINAL"
Write-DependencyLog "Builds réussis: $successCount" "SUCCESS" "FINAL"
Write-DependencyLog "Builds échoués: $failCount" "ERROR" "FINAL"
Write-DependencyLog "Issues dépendances: $($Global:DependencyIssues.Count)" "WARNING" "FINAL"

# Génération du rapport
New-DependencyReport

# Nettoyage des images de test
Write-DependencyLog "Nettoyage des images de test..." "INFO" "CLEANUP"
docker images --filter "reference=station-traffeyere:*-dependency-test" -q | ForEach-Object { docker rmi $_ --force 2>$null }

if ($failCount -eq 0 -and $Global:DependencyIssues.Count -eq 0) {
    Write-DependencyLog "🎉 TOUS LES TESTS DE DÉPENDANCES RÉUSSIS!" "SUCCESS" "FINAL"
    exit 0
} else {
    Write-DependencyLog "⚠️ Actions requises - Voir rapport détaillé" "WARNING" "FINAL"
    exit 1
}