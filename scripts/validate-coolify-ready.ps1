# ================================================================
# VALIDATION COOLIFY READY - Station Traffeyère
# Vérification finale avant déploiement Coolify
# ================================================================

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  VALIDATION COOLIFY DEPLOYMENT READY" -ForegroundColor Cyan
Write-Host "  Station Traffeyère IoT/AI Platform - RNCP 39394" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0
$warnings = 0

# 1. Validation syntax docker-compose.yml
Write-Host "🔍 Validation syntaxe docker-compose.yml..." -ForegroundColor Yellow
try {
    $composeResult = docker-compose -f docker-compose.yml config --quiet 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Syntaxe docker-compose valide" -ForegroundColor Green
    } else {
        Write-Host "❌ Erreur syntaxe docker-compose" -ForegroundColor Red
        $composeResult | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        $errors++
    }
} catch {
    Write-Host "❌ Docker Compose non disponible" -ForegroundColor Red
    $errors++
}

# 2. Vérification absence variables problématiques
Write-Host "🔍 Vérification variables d'environnement..." -ForegroundColor Yellow
$composeContent = Get-Content docker-compose.yml -Raw

if ($composeContent -match '\$SYS' -or $composeContent -match 'SYS=') {
    Write-Host "⚠️ Variables SYS détectées (peuvent causer problèmes Coolify)" -ForegroundColor Yellow
    $warnings++
} else {
    Write-Host "✅ Pas de variables problématiques SYS" -ForegroundColor Green
}

# 3. Vérification structure services
Write-Host "🔍 Vérification services requis..." -ForegroundColor Yellow
$requiredServices = @("postgres", "redis", "backend", "frontend", "mosquitto", "keycloak")
$foundServices = 0

foreach ($service in $requiredServices) {
    $pattern = "^\s*${service}:\s*$"
    if ($composeContent -match $pattern) {
        Write-Host "  ✅ Service $service trouvé" -ForegroundColor Green
        $foundServices++
    } else {
        Write-Host "  ❌ Service $service manquant" -ForegroundColor Red
        $errors++
    }
}

Write-Host "📊 Services trouvés: $foundServices/$($requiredServices.Count)" -ForegroundColor Cyan

# 4. Vérification conflits Coolify (replicas/container_name)
Write-Host "🔍 Vérification conflits Coolify..." -ForegroundColor Yellow
if ($composeContent -match 'container_name:' -and $composeContent -match 'replicas:') {
    Write-Host "⚠️ Conflit container_name/replicas détecté" -ForegroundColor Yellow
    $warnings++
} else {
    Write-Host "✅ Pas de conflits container_name/replicas" -ForegroundColor Green
}

# 5. Vérification Dockerfiles
Write-Host "🔍 Vérification Dockerfiles..." -ForegroundColor Yellow
$dockerfiles = @("services/backend/Dockerfile", "services/frontend/Dockerfile")
foreach ($dockerfile in $dockerfiles) {
    if (Test-Path $dockerfile) {
        Write-Host "  ✅ $dockerfile trouvé" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ $dockerfile manquant" -ForegroundColor Yellow
        $warnings++
    }
}

# Résumé final
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "RÉSUMÉ VALIDATION" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host "🎉 PARFAIT! Prêt pour déploiement Coolify" -ForegroundColor Green -BackgroundColor DarkGreen
    Write-Host ""
    Write-Host "✅ Aucune erreur critique" -ForegroundColor Green
    Write-Host "✅ Aucun warning" -ForegroundColor Green
    Write-Host "✅ Architecture complète validée" -ForegroundColor Green
} elseif ($errors -eq 0) {
    Write-Host "✅ PRÊT avec warnings mineurs" -ForegroundColor Yellow -BackgroundColor DarkYellow
    Write-Host ""
    Write-Host "✅ Aucune erreur critique" -ForegroundColor Green
    Write-Host "⚠️  $warnings warnings (non bloquants)" -ForegroundColor Yellow
} else {
    Write-Host "❌ ERREURS À CORRIGER" -ForegroundColor Red -BackgroundColor DarkRed
    Write-Host ""
    Write-Host "❌ $errors erreurs critiques" -ForegroundColor Red
    Write-Host "⚠️  $warnings warnings" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 INSTRUCTIONS DÉPLOIEMENT COOLIFY:" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "1. Dans Coolify, créer nouveau projet Docker Compose" -ForegroundColor White
Write-Host "2. Repository: bandidood/convergence-iot-ai-platform" -ForegroundColor White
Write-Host "3. Branch: master" -ForegroundColor White
Write-Host "4. Configurer variables d'environnement depuis .env.coolify.example" -ForegroundColor White
Write-Host "5. Variables critiques à définir:" -ForegroundColor White
Write-Host "   - POSTGRES_PASSWORD" -ForegroundColor Yellow
Write-Host "   - REDIS_PASSWORD" -ForegroundColor Yellow
Write-Host "   - SECRET_KEY" -ForegroundColor Yellow
Write-Host "   - JWT_SECRET" -ForegroundColor Yellow
Write-Host "6. Lancer déploiement" -ForegroundColor White
Write-Host ""
Write-Host "📋 Services déployés:" -ForegroundColor Cyan
Write-Host "   - PostgreSQL (TimescaleDB)" -ForegroundColor Gray
Write-Host "   - Redis (Cache)" -ForegroundColor Gray
Write-Host "   - InfluxDB (Métriques IoT)" -ForegroundColor Gray
Write-Host "   - MinIO (Stockage S3)" -ForegroundColor Gray
Write-Host "   - Keycloak (Identity Management)" -ForegroundColor Gray
Write-Host "   - Mosquitto (MQTT Broker)" -ForegroundColor Gray
Write-Host "   - Backend (API FastAPI)" -ForegroundColor Gray
Write-Host "   - Frontend (React Dashboard)" -ForegroundColor Gray
Write-Host ""

exit $errors