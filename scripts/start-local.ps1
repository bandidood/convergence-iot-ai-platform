# =============================================================================
# SCRIPT DE LANCEMENT LOCAL - Station Traffeyère IoT/AI Platform
# Tests Windows avant déploiement Linux - RNCP 39394
# =============================================================================

Write-Host "🚀 Station Traffeyère IoT/AI Platform - Test Local Windows" -ForegroundColor Cyan
Write-Host "RNCP 39394 - Expert en Systèmes d'Information et Sécurité" -ForegroundColor Yellow
Write-Host ""

# Vérifier Docker
Write-Host "🔍 Vérification de l'environnement..." -ForegroundColor Green
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
    
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker non disponible. Veuillez installer Docker Desktop." -ForegroundColor Red
    exit 1
}

# Nettoyer les anciens conteneurs (optionnel)
Write-Host ""
$cleanup = Read-Host "Nettoyer les anciens conteneurs ? (y/N)"
if ($cleanup -eq "y" -or $cleanup -eq "Y") {
    Write-Host "🧹 Nettoyage des anciens conteneurs..." -ForegroundColor Yellow
    docker-compose -f docker-compose.local.yml down -v --remove-orphans
}

# Construction des images
Write-Host ""
Write-Host "🔨 Construction des images personnalisées..." -ForegroundColor Blue
docker-compose -f docker-compose.local.yml build --parallel

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la construction des images" -ForegroundColor Red
    exit 1
}

# Démarrage des services
Write-Host ""
Write-Host "⚡ Démarrage de tous les services..." -ForegroundColor Blue
docker-compose -f docker-compose.local.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du démarrage des services" -ForegroundColor Red
    exit 1
}

# Attendre que les services démarrent
Write-Host ""
Write-Host "⏳ Attente du démarrage des services (30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Vérification des services
Write-Host ""
Write-Host "🔍 Vérification des services..." -ForegroundColor Green

# Vérifier PostgreSQL
try {
    docker exec station-traffeyere-iot-ai-platform-postgres-1 pg_isready -U postgres
    Write-Host "✅ PostgreSQL opérationnel" -ForegroundColor Green
} catch {
    Write-Host "⚠️ PostgreSQL non prêt" -ForegroundColor Yellow
}

# Vérifier Redis
try {
    $redisTest = docker exec station-traffeyere-iot-ai-platform-redis-1 redis-cli ping
    if ($redisTest -eq "PONG") {
        Write-Host "✅ Redis opérationnel" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Redis non prêt" -ForegroundColor Yellow
}

# Vérifier Backend
try {
    $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ Backend FastAPI opérationnel" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Backend non prêt (normal si encore en démarrage)" -ForegroundColor Yellow
}

# Vérifier Frontend
try {
    $frontendHealth = Invoke-RestMethod -Uri "http://localhost:3000/healthz" -TimeoutSec 5
    Write-Host "✅ Frontend React opérationnel" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Frontend non prêt (normal si encore en démarrage)" -ForegroundColor Yellow
}

# Statut des conteneurs
Write-Host ""
Write-Host "📊 Statut des conteneurs:" -ForegroundColor Cyan
docker-compose -f docker-compose.local.yml ps

# URLs d'accès
Write-Host ""
Write-Host "🌐 URLs d'accès:" -ForegroundColor Cyan
Write-Host "Frontend:      http://localhost:3000" -ForegroundColor White
Write-Host "Backend API:   http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "InfluxDB:      http://localhost:8086" -ForegroundColor White
Write-Host "Grafana:       http://localhost:3001 (admin/admin)" -ForegroundColor White
Write-Host "Prometheus:    http://localhost:9090" -ForegroundColor White

# Options post-démarrage
Write-Host ""
Write-Host "📋 Actions disponibles:" -ForegroundColor Magenta
Write-Host "1. Ouvrir le frontend dans le navigateur" -ForegroundColor White
Write-Host "2. Voir les logs en temps réel" -ForegroundColor White
Write-Host "3. Lancer les tests de validation" -ForegroundColor White
Write-Host "4. Arrêter tous les services" -ForegroundColor White

$action = Read-Host "Votre choix (1-4)"

switch ($action) {
    "1" {
        Write-Host "🌐 Ouverture du frontend..." -ForegroundColor Green
        Start-Process "http://localhost:3000"
        Start-Process "http://localhost:8000/api/docs"
    }
    "2" {
        Write-Host "📋 Logs en temps réel (Ctrl+C pour arrêter)..." -ForegroundColor Green
        docker-compose -f docker-compose.local.yml logs -f
    }
    "3" {
        Write-Host "🧪 Tests de validation..." -ForegroundColor Green
        Write-Host "Voir le fichier TEST-LOCAL-WINDOWS.md pour les tests complets" -ForegroundColor Yellow
    }
    "4" {
        Write-Host "🛑 Arrêt des services..." -ForegroundColor Red
        docker-compose -f docker-compose.local.yml down
        Write-Host "✅ Services arrêtés" -ForegroundColor Green
    }
    default {
        Write-Host "✅ Services démarrés. Consultez TEST-LOCAL-WINDOWS.md pour les tests." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🎯 Plateforme Station Traffeyère prête pour tests locaux!" -ForegroundColor Green
Write-Host "📚 Consultez TEST-LOCAL-WINDOWS.md pour les tests complets" -ForegroundColor Cyan