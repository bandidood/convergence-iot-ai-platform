# =====================================================================================
# Script de lancement - Station Traffeyere IoT AI Platform Simulation
# =====================================================================================

param(
    [switch]$CleanStart = $false,
    [switch]$SkipBuild = $false
)

Write-Host "Station Traffeyere - Lancement simulation complete" -ForegroundColor Cyan

# Verification Docker
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "OK Docker: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "ERREUR: Docker requis" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERREUR Docker: $_" -ForegroundColor Red
    exit 1
}

# Verification Docker Compose
try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "OK $composeVersion" -ForegroundColor Green
    } else {
        Write-Host "ERREUR: Docker Compose requis" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERREUR Docker Compose" -ForegroundColor Red
    exit 1
}

# Nettoyage si demande
if ($CleanStart) {
    Write-Host "Nettoyage environnement..." -ForegroundColor Yellow
    docker-compose -f docker-compose.iot-complete.yml down -v --remove-orphans 2>$null
    Write-Host "Nettoyage termine" -ForegroundColor Green
}

# Creation repertoires necessaires
Write-Host "Preparation repertoires..." -ForegroundColor Yellow
$directories = @(
    "logs",
    "mqtt/data", 
    "mqtt/log",
    "models",
    "core/iot-data-generator",
    "core/edge-ai-engine",
    "interfaces/voice-assistant-xia"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Cree: $dir" -ForegroundColor Green
    }
}

# Configuration MQTT
if (!(Test-Path "mqtt/mosquitto.conf")) {
    Write-Host "Copie de la configuration MQTT..." -ForegroundColor Yellow
    if (Test-Path "mosquitto.conf") {
        Copy-Item "mosquitto.conf" "mqtt/mosquitto.conf"
        Write-Host "Configuration MQTT copiee" -ForegroundColor Green
    }
}

# Demarrage des services
Write-Host "Demarrage stack IoT complete..." -ForegroundColor Yellow

try {
    if (!$SkipBuild) {
        Write-Host "Build des images Docker..." -ForegroundColor Blue
        docker-compose -f docker-compose.iot-complete.yml build --parallel
    }
    
    Write-Host "Lancement des services..." -ForegroundColor Blue
    docker-compose -f docker-compose.iot-complete.yml up -d
    
    Write-Host "Services lances avec succes" -ForegroundColor Green
} catch {
    Write-Host "Erreur lancement: $_" -ForegroundColor Red
    exit 1
}

# Attente demarrage
Write-Host "Attente demarrage services (30 secondes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verification statut
Write-Host "Verification statut services..." -ForegroundColor Yellow
docker-compose -f docker-compose.iot-complete.yml ps

Write-Host "`nURLs d'acces:" -ForegroundColor Cyan
Write-Host "  • MQTT Broker:            mqtt://localhost:1883" -ForegroundColor White
Write-Host "  • Dashboard IoT:          http://localhost:3000" -ForegroundColor White
Write-Host "  • Edge AI Engine:         http://localhost:8091" -ForegroundColor White
Write-Host "  • Assistant XAI:          http://localhost:5000" -ForegroundColor White
Write-Host "  • Digital Twin Unity:     http://localhost:8080" -ForegroundColor White

Write-Host "`nCommandes utiles:" -ForegroundColor Cyan
Write-Host "  • Logs temps reel:        docker-compose -f docker-compose.iot-complete.yml logs -f" -ForegroundColor White
Write-Host "  • Arret services:         docker-compose -f docker-compose.iot-complete.yml down" -ForegroundColor White

Write-Host "`nSimulation IoT AI Platform lancee avec succes!" -ForegroundColor Green