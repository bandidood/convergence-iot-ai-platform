# ============================================================================
# Script de correction déploiement docker-compose.light.yml
# Station Traffeyère IoT/AI Platform - RNCP 39394
# ============================================================================

Write-Host "🔧 Correction du déploiement docker-compose.light.yml" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. Arrêt complet des services
Write-Host "`n📛 Arrêt des services en cours..." -ForegroundColor Yellow
docker compose -f docker-compose.light.yml down

# 2. Suppression des volumes problématiques
Write-Host "`n🗑️ Suppression des volumes potentiellement corrompus..." -ForegroundColor Yellow
docker volume rm -f station-traffeyere-iot-ai-platform_postgres_data
docker volume rm -f station-traffeyere-iot-ai-platform_redis_data

# 3. Nettoyage des conteneurs et images inutiles
Write-Host "`n🧹 Nettoyage Docker..." -ForegroundColor Yellow
docker system prune -f

# 4. Vérification des variables d'environnement
Write-Host "`n🔍 Vérification du fichier .env..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ Fichier .env présent" -ForegroundColor Green
    Get-Content ".env" | Select-String "POSTGRES_PASSWORD|REDIS_PASSWORD" | ForEach-Object { 
        Write-Host "  $_" -ForegroundColor Gray 
    }
} else {
    Write-Host "❌ Fichier .env manquant!" -ForegroundColor Red
    exit 1
}

# 5. Démarrage avec rebuild des images
Write-Host "`n🚀 Démarrage des services avec rebuild..." -ForegroundColor Green
docker compose -f docker-compose.light.yml up -d --build --force-recreate

# 6. Attendre que les services soient prêts
Write-Host "`n⏳ Attente de la stabilisation des services..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 7. Vérification du statut
Write-Host "`n📊 Statut des services:" -ForegroundColor Cyan
docker compose -f docker-compose.light.yml ps

# 8. Vérification des logs en cas de problème
Write-Host "`n📋 Logs des services critiques:" -ForegroundColor Cyan
Write-Host "--- PostgreSQL ---" -ForegroundColor Gray
docker compose -f docker-compose.light.yml logs --tail=10 postgres
Write-Host "`n--- Redis ---" -ForegroundColor Gray  
docker compose -f docker-compose.light.yml logs --tail=10 redis

Write-Host "`n✅ Script terminé!" -ForegroundColor Green
Write-Host "Utilisez 'docker compose -f docker-compose.light.yml logs [service]' pour plus de détails." -ForegroundColor Gray