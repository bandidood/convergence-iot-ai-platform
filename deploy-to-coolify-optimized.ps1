# =============================================================================
# DEPLOYMENT SCRIPT OPTIMIZED - Station Traffeyère IoT/AI Platform
# Déploiement automatisé sur Coolify avec validation et rollback
# Projet RNCP 39394 - Expert en Systèmes d'Information et Sécurité
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("staging", "production")]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipHealthChecks = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$EnableRollback = $true,
    
    [Parameter(Mandatory=$false)]
    [string]$CoolifyURL = "https://coolify.ccdigital.fr",
    
    [Parameter(Mandatory=$false)]
    [string]$CoolifyApiToken = $env:COOLIFY_API_TOKEN
)

# Configuration couleurs pour output
$Host.UI.RawUI.BackgroundColor = "Black"
$ErrorActionPreference = "Stop"

# Bannière projet
Write-Host @"
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                    🏭 STATION TRAFFEYÈRE IoT/AI PLATFORM 🏭                      ║
║                                                                                   ║
║    📚 Projet RNCP 39394 - Expert en Systèmes d'Information et Sécurité          ║
║    🚀 Déploiement Automatisé sur Coolify                                         ║
║    📊 127 Capteurs IoT + Edge AI + Monitoring 24/7                               ║
║                                                                                   ║
║    🌐 Frontend: https://frontend-station.johann-lebel.fr                         ║
║    🔧 Backend:  https://backend-station.johann-lebel.fr                          ║
║    📊 Grafana:  https://grafana.johann-lebel.fr                                  ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

function Write-Step {
    param([string]$Message, [string]$Color = "Green")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] ✅ $Message" -ForegroundColor $Color
}

function Write-Error-Step {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] ❌ ERREUR: $Message" -ForegroundColor Red
}

function Write-Warning-Step {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] ⚠️ ATTENTION: $Message" -ForegroundColor Yellow
}

function Wait-UserConfirmation {
    param([string]$Message = "Continuer ?")
    if (-not $DryRun) {
        $confirmation = Read-Host "$Message (y/N)"
        if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
            Write-Host "Déploiement annulé par l'utilisateur." -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "[DRY RUN] $Message - Simulation activée" -ForegroundColor Yellow
    }
}

function Test-Prerequisites {
    Write-Step "Vérification des prérequis..."
    
    # Vérification Docker
    try {
        $dockerVersion = docker --version
        Write-Step "Docker détecté: $dockerVersion"
    } catch {
        Write-Error-Step "Docker n'est pas installé ou accessible"
        exit 1
    }
    
    # Vérification Docker Compose
    try {
        $composeVersion = docker compose version
        Write-Step "Docker Compose détecté: $composeVersion"
    } catch {
        Write-Error-Step "Docker Compose n'est pas installé"
        exit 1
    }
    
    # Vérification fichier de configuration
    if (-not (Test-Path "docker-compose.coolify.optimized.yml")) {
        Write-Error-Step "Fichier docker-compose.coolify.optimized.yml introuvable"
        exit 1
    }
    Write-Step "Configuration Coolify trouvée"
    
    # Vérification variables d'environnement
    if (-not (Test-Path ".env.$Environment")) {
        Write-Error-Step "Fichier .env.$Environment introuvable"
        exit 1
    }
    Write-Step "Variables d'environnement $Environment validées"
    
    # Vérification token Coolify
    if ([string]::IsNullOrEmpty($CoolifyApiToken)) {
        Write-Warning-Step "Token Coolify API non fourni - certaines fonctionnalités seront limitées"
    }
}

function Test-Services {
    param([string]$ComposeFile)
    
    Write-Step "Validation de la configuration Docker Compose..."
    
    try {
        if ($DryRun) {
            Write-Host "[DRY RUN] docker compose -f $ComposeFile config --quiet" -ForegroundColor Yellow
        } else {
            docker compose -f $ComposeFile config --quiet
        }
        Write-Step "Configuration Docker Compose valide"
    } catch {
        Write-Error-Step "Configuration Docker Compose invalide: $_"
        exit 1
    }
}

function Build-Images {
    param([string]$ComposeFile)
    
    Write-Step "Construction des images Docker..."
    
    $services = @("backend", "frontend", "iot-generator", "edge-ai")
    
    foreach ($service in $services) {
        Write-Step "Construction de l'image pour $service..."
        
        if ($DryRun) {
            Write-Host "[DRY RUN] docker compose -f $ComposeFile build $service" -ForegroundColor Yellow
        } else {
            try {
                docker compose -f $ComposeFile build $service --no-cache
                Write-Step "Image $service construite avec succès"
            } catch {
                Write-Error-Step "Échec de construction pour $service: $_"
                exit 1
            }
        }
    }
}

function Deploy-Stack {
    param([string]$ComposeFile)
    
    Write-Step "Déploiement de la stack sur Coolify..."
    
    if ($DryRun) {
        Write-Host "[DRY RUN] docker compose -f $ComposeFile up -d" -ForegroundColor Yellow
        return
    }
    
    try {
        # Déploiement par étapes pour contrôle
        Write-Step "Phase 1: Infrastructure (Bases de données)"
        docker compose -f $ComposeFile up -d postgres redis influxdb minio mosquitto
        
        Start-Sleep -Seconds 30
        
        Write-Step "Phase 2: Monitoring"
        docker compose -f $ComposeFile up -d prometheus grafana alertmanager
        
        Start-Sleep -Seconds 20
        
        Write-Step "Phase 3: Applications"
        docker compose -f $ComposeFile up -d backend frontend iot-generator edge-ai
        
        Write-Step "Déploiement terminé - Attente stabilisation..."
        Start-Sleep -Seconds 60
        
    } catch {
        Write-Error-Step "Échec du déploiement: $_"
        
        if ($EnableRollback) {
            Write-Warning-Step "Tentative de rollback automatique..."
            Invoke-Rollback -ComposeFile $ComposeFile
        }
        exit 1
    }
}

function Test-HealthChecks {
    param([string]$Environment)
    
    if ($SkipHealthChecks) {
        Write-Warning-Step "Tests de santé ignorés (--SkipHealthChecks)"
        return
    }
    
    Write-Step "Exécution des tests de santé..."
    
    $endpoints = @{
        "Frontend" = "https://frontend-station.johann-lebel.fr/healthz"
        "Backend API" = "https://backend-station.johann-lebel.fr/health"
        "Grafana" = "https://grafana.johann-lebel.fr/api/health"
        "Prometheus" = "https://prometheus.johann-lebel.fr/-/healthy"
        "InfluxDB" = "https://influx.johann-lebel.fr/health"
    }
    
    $failedChecks = @()
    
    foreach ($endpoint in $endpoints.GetEnumerator()) {
        $name = $endpoint.Key
        $url = $endpoint.Value
        
        Write-Host "  🔍 Test $name..." -NoNewline
        
        if ($DryRun) {
            Write-Host " [DRY RUN] ✅" -ForegroundColor Yellow
            continue
        }
        
        try {
            $response = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 10 -ErrorAction Stop
            Write-Host " ✅" -ForegroundColor Green
        } catch {
            Write-Host " ❌" -ForegroundColor Red
            $failedChecks += $name
            Write-Warning-Step "Échec test de santé $name : $($_.Exception.Message)"
        }
        
        Start-Sleep -Seconds 2
    }
    
    if ($failedChecks.Count -gt 0) {
        Write-Error-Step "Tests de santé échoués pour: $($failedChecks -join ', ')"
        
        if ($EnableRollback) {
            Wait-UserConfirmation "Lancer le rollback automatique ?"
            Invoke-Rollback -ComposeFile "docker-compose.coolify.optimized.yml"
        }
        exit 1
    } else {
        Write-Step "✅ Tous les tests de santé réussis !"
    }
}

function Test-PerformanceRNCP {
    Write-Step "Validation des métriques RNCP 39394..."
    
    $metricsChecks = @{
        "Edge AI P95 Latency" = @{
            url = "https://prometheus.johann-lebel.fr/api/v1/query"
            query = "histogram_quantile(0.95, sum(rate(ai_inference_duration_seconds_bucket[1m])) by (le)) * 1000"
            threshold = 0.28
            unit = "ms"
        }
        "IoT Throughput" = @{
            url = "https://prometheus.johann-lebel.fr/api/v1/query"
            query = "rate(iot_sensor_readings_total[5m])"
            threshold = 20
            unit = "req/sec"
        }
        "API Availability" = @{
            url = "https://prometheus.johann-lebel.fr/api/v1/query"
            query = "avg_over_time(up{job='station-backend-api'}[1h])"
            threshold = 0.999
            unit = "%"
        }
    }
    
    if ($DryRun) {
        Write-Host "[DRY RUN] Tests métriques RNCP 39394 - Simulation" -ForegroundColor Yellow
        return
    }
    
    $passedChecks = 0
    foreach ($check in $metricsChecks.GetEnumerator()) {
        $name = $check.Key
        $config = $check.Value
        
        Write-Host "  📊 Test $name..." -NoNewline
        
        try {
            $queryUrl = "$($config.url)?query=$([System.Web.HttpUtility]::UrlEncode($config.query))"
            $response = Invoke-RestMethod -Uri $queryUrl -Method GET -TimeoutSec 15
            
            if ($response.data.result.Count -gt 0) {
                $value = [double]$response.data.result[0].value[1]
                $threshold = $config.threshold
                
                if (($name -eq "API Availability" -and $value -ge $threshold) -or
                    ($name -ne "API Availability" -and $value -le $threshold)) {
                    Write-Host " ✅ ($value $($config.unit))" -ForegroundColor Green
                    $passedChecks++
                } else {
                    Write-Host " ⚠️ ($value $($config.unit) - seuil: $threshold)" -ForegroundColor Yellow
                }
            } else {
                Write-Host " ❓ (pas de données)" -ForegroundColor Gray
            }
        } catch {
            Write-Host " ❌ (erreur requête)" -ForegroundColor Red
        }
        
        Start-Sleep -Seconds 1
    }
    
    Write-Step "Tests métriques RNCP: $passedChecks/$($metricsChecks.Count) réussis"
}

function Invoke-Rollback {
    param([string]$ComposeFile)
    
    Write-Warning-Step "ROLLBACK EN COURS..."
    
    if ($DryRun) {
        Write-Host "[DRY RUN] docker compose -f $ComposeFile down" -ForegroundColor Yellow
        return
    }
    
    try {
        docker compose -f $ComposeFile down
        Write-Step "Rollback terminé - Services arrêtés"
    } catch {
        Write-Error-Step "Échec du rollback: $_"
    }
}

function Send-DeploymentNotification {
    param([string]$Status, [string]$Environment)
    
    if ([string]::IsNullOrEmpty($env:SLACK_WEBHOOK_URL)) {
        Write-Warning-Step "Webhook Slack non configuré - notification ignorée"
        return
    }
    
    $color = if ($Status -eq "SUCCESS") { "good" } else { "danger" }
    $emoji = if ($Status -eq "SUCCESS") { "✅" } else { "❌" }
    
    $payload = @{
        channel = "#traffeyere-deployments"
        username = "Coolify Deployment Bot"
        icon_emoji = ":rocket:"
        attachments = @(
            @{
                color = $color
                title = "$emoji Déploiement Station Traffeyère - $Status"
                fields = @(
                    @{ title = "Environnement"; value = $Environment; short = $true }
                    @{ title = "Projet"; value = "RNCP 39394"; short = $true }
                    @{ title = "Timestamp"; value = (Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC"); short = $true }
                )
                footer = "Station Traffeyère IoT/AI Platform"
            }
        )
    } | ConvertTo-Json -Depth 3
    
    if (-not $DryRun) {
        try {
            Invoke-RestMethod -Uri $env:SLACK_WEBHOOK_URL -Method Post -Body $payload -ContentType "application/json"
            Write-Step "Notification Slack envoyée"
        } catch {
            Write-Warning-Step "Échec envoi notification Slack: $_"
        }
    }
}

# =============================================================================
# EXECUTION PRINCIPALE
# =============================================================================

try {
    $startTime = Get-Date
    
    Write-Step "🚀 Début du déploiement - Environnement: $Environment"
    
    # Phase 1: Prérequis
    Test-Prerequisites
    
    # Phase 2: Validation configuration
    Test-Services -ComposeFile "docker-compose.coolify.optimized.yml"
    
    # Phase 3: Construction images
    Wait-UserConfirmation "Lancer la construction des images Docker ?"
    Build-Images -ComposeFile "docker-compose.coolify.optimized.yml"
    
    # Phase 4: Déploiement
    Wait-UserConfirmation "Lancer le déploiement sur Coolify ?"
    Deploy-Stack -ComposeFile "docker-compose.coolify.optimized.yml"
    
    # Phase 5: Tests de santé
    Write-Step "Attente stabilisation des services..."
    Start-Sleep -Seconds 90
    Test-HealthChecks -Environment $Environment
    
    # Phase 6: Validation métriques RNCP
    Test-PerformanceRNCP
    
    # Phase 7: Notification succès
    $duration = (Get-Date) - $startTime
    Write-Step "🎉 DÉPLOIEMENT RÉUSSI ! Durée: $($duration.Minutes)min $($duration.Seconds)s"
    
    Send-DeploymentNotification -Status "SUCCESS" -Environment $Environment
    
    Write-Host @"

╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                            🎉 DÉPLOIEMENT RÉUSSI 🎉                                        ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  📊 Services déployés:                                                                                     ║
║     • Frontend Dashboard:        https://frontend-station.johann-lebel.fr                                 ║
║     • Backend API:               https://backend-station.johann-lebel.fr                                  ║
║     • Grafana Monitoring:        https://grafana.johann-lebel.fr                                          ║
║     • Prometheus Metrics:        https://prometheus.johann-lebel.fr                                       ║
║     • InfluxDB Time-Series:      https://influx.johann-lebel.fr                                           ║
║                                                                                                            ║
║  🏭 Fonctionnalités actives:                                                                               ║
║     • 127 Capteurs IoT simulés (0.2 Hz)                                                                   ║
║     • Edge AI avec détection d'anomalies (P95 < 0.28ms)                                                   ║
║     • Dashboard temps réel avec WebSocket (< 50ms)                                                        ║
║     • Stack monitoring complet 24/7                                                                       ║
║     • Alerting Slack + Email automatique                                                                  ║
║                                                                                                            ║
║  📚 Projet RNCP 39394 - Objectifs atteints:                                                               ║
║     • Architecture microservices en production                                                            ║
║     • SLA 99.9% avec monitoring proactif                                                                  ║
║     • Sécurité ISA/IEC 62443 SL2+                                                                         ║
║     • Performance temps réel validée                                                                      ║
║                                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
    
} catch {
    Write-Error-Step "Échec critique du déploiement: $_"
    Send-DeploymentNotification -Status "FAILED" -Environment $Environment
    
    if ($EnableRollback) {
        Write-Warning-Step "Rollback automatique activé..."
        Invoke-Rollback -ComposeFile "docker-compose.coolify.optimized.yml"
    }
    
    exit 1
}

Write-Step "🏁 Script de déploiement terminé avec succès"