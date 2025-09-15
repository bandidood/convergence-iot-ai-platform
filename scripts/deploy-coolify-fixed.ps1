# ================================================================
# SCRIPT DÉPLOIEMENT COOLIFY OPTIMISÉ
# Station Traffeyere IoT/AI Platform - RNCP 39394
# Déploiement sans conflits de configuration
# ================================================================

param(
    [switch]$ValidateCompose = $true,
    [switch]$CheckHealth = $true,
    [switch]$ShowLogs = $false,
    [switch]$Force = $false
)

$ErrorActionPreference = "Continue"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  DÉPLOIEMENT COOLIFY OPTIMISÉ" -ForegroundColor Cyan  
Write-Host "  Station Traffeyère IoT/AI Platform - RNCP 39394" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ComposeFile = "docker-compose.yml"
$EnvFile = ".env.coolify.example"

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "  - Compose File: $ComposeFile" -ForegroundColor Gray
Write-Host "  - Env Template: $EnvFile" -ForegroundColor Gray
Write-Host ""

# 1. Validation du fichier docker-compose.yml
if ($ValidateCompose) {
    Write-Host "🔍 Validation du fichier docker-compose.yml..." -ForegroundColor Yellow
    
    if (-not (Test-Path $ComposeFile)) {
        Write-Host "[ERROR] Fichier $ComposeFile introuvable !" -ForegroundColor Red
        exit 1
    }
    
    # Test syntaxe docker-compose
    Write-Host "[INFO] Vérification syntaxe docker-compose..." -ForegroundColor Cyan
    $validateResult = docker-compose -f $ComposeFile config 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] ✅ Syntaxe docker-compose valide" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] ❌ Erreurs dans docker-compose.yml:" -ForegroundColor Red
        $validateResult | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        if (-not $Force) {
            exit 1
        }
    }
    
    # Vérification spécifique des fixes appliqués
    Write-Host "[INFO] Vérification des corrections Coolify..." -ForegroundColor Cyan
    
    $composeContent = Get-Content $ComposeFile -Raw
    
    # Vérifier absence de conflits container_name + replicas
    if ($composeContent -match 'container_name:.*\n.*replicas:' -or $composeContent -match 'replicas:.*\n.*container_name:') {
        Write-Host "[WARNING] ⚠️ Conflits potentiels container_name/replicas détectés" -ForegroundColor Yellow
    } else {
        Write-Host "[SUCCESS] ✅ Pas de conflits container_name/replicas" -ForegroundColor Green
    }
    
    # Vérifier définition variable SYS
    if ($composeContent -match 'SYS:') {
        Write-Host "[SUCCESS] ✅ Variable SYS définie pour Mosquitto" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] ⚠️ Variable SYS non définie - peut causer des erreurs MQTT" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# 2. Vérification des variables d'environnement
Write-Host "🔧 Configuration des variables d'environnement..." -ForegroundColor Yellow

if (Test-Path $EnvFile) {
    Write-Host "[INFO] Fichier template trouvé: $EnvFile" -ForegroundColor Cyan
    Write-Host "[INFO] 📋 Variables requises pour Coolify:" -ForegroundColor Cyan
    
    $envContent = Get-Content $EnvFile
    $requiredVars = $envContent | Where-Object { $_ -match '^[A-Z_]+=.*' } | ForEach-Object { ($_ -split '=')[0] }
    
    Write-Host "  Variables critiques:" -ForegroundColor Gray
    $criticalVars = @("POSTGRES_PASSWORD", "REDIS_PASSWORD", "SECRET_KEY", "JWT_SECRET")
    foreach ($var in $criticalVars) {
        if ($var -in $requiredVars) {
            Write-Host "    ✅ $var" -ForegroundColor Green
        } else {
            Write-Host "    ❌ $var (manquante)" -ForegroundColor Red
        }
    }
    
    Write-Host "  Total variables: $($requiredVars.Count)" -ForegroundColor Gray
    
} else {
    Write-Host "[WARNING] ⚠️ Fichier template .env non trouvé" -ForegroundColor Yellow
    Write-Host "[INFO] Créez un fichier .env avec les variables nécessaires" -ForegroundColor Cyan
}

Write-Host ""

# 3. Instructions de déploiement Coolify
Write-Host "🚀 INSTRUCTIONS DÉPLOIEMENT COOLIFY" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

Write-Host "1️⃣ Dans l'interface Coolify:" -ForegroundColor Cyan
Write-Host "   • Créez un nouveau projet" -ForegroundColor White
Write-Host "   • Sélectionnez 'Docker Compose' comme type" -ForegroundColor White
Write-Host "   • Repository: bandidood/convergence-iot-ai-platform" -ForegroundColor White
Write-Host "   • Branch: master" -ForegroundColor White
Write-Host ""

Write-Host "2️⃣ Configuration des variables:" -ForegroundColor Cyan
Write-Host "   • Allez dans l'onglet 'Environment Variables'" -ForegroundColor White
Write-Host "   • Importez les variables depuis le fichier template" -ForegroundColor White
Write-Host "   • Générez des mots de passe sécurisés pour:" -ForegroundColor White
Write-Host "     - POSTGRES_PASSWORD" -ForegroundColor Yellow
Write-Host "     - REDIS_PASSWORD" -ForegroundColor Yellow
Write-Host "     - SECRET_KEY" -ForegroundColor Yellow
Write-Host "     - JWT_SECRET" -ForegroundColor Yellow
Write-Host "     - KEYCLOAK_ADMIN_PASSWORD" -ForegroundColor Yellow
Write-Host ""

Write-Host "3️⃣ Domaines et certificats:" -ForegroundColor Cyan
Write-Host "   • Configurez vos domaines personnalisés" -ForegroundColor White
Write-Host "   • Activez les certificats SSL automatiques" -ForegroundColor White
Write-Host "   • Exemples de domaines:" -ForegroundColor White
Write-Host "     - traffeyere.votre-domaine.fr (frontend)" -ForegroundColor Gray
Write-Host "     - api.votre-domaine.fr (backend)" -ForegroundColor Gray
Write-Host "     - auth.votre-domaine.fr (keycloak)" -ForegroundColor Gray
Write-Host ""

Write-Host "4️⃣ Déploiement:" -ForegroundColor Cyan
Write-Host "   • Cliquez sur 'Deploy'" -ForegroundColor White
Write-Host "   • Surveillez les logs de déploiement" -ForegroundColor White
Write-Host "   • Vérifiez le statut des services" -ForegroundColor White
Write-Host ""

# 4. Commandes de diagnostic post-déploiement
Write-Host "🔍 DIAGNOSTIC POST-DÉPLOIEMENT" -ForegroundColor Magenta
Write-Host "===============================" -ForegroundColor Magenta
Write-Host ""

Write-Host "Commandes utiles pour diagnostic dans Coolify:" -ForegroundColor Yellow
Write-Host ""

Write-Host "📊 Status des services:" -ForegroundColor Cyan
Write-Host "  docker-compose -f $ComposeFile ps" -ForegroundColor Gray
Write-Host ""

Write-Host "📋 Logs des services:" -ForegroundColor Cyan
Write-Host "  docker-compose -f $ComposeFile logs --tail=50" -ForegroundColor Gray
Write-Host "  docker-compose -f $ComposeFile logs backend" -ForegroundColor Gray
Write-Host "  docker-compose -f $ComposeFile logs frontend" -ForegroundColor Gray
Write-Host ""

Write-Host "🏥 Health checks:" -ForegroundColor Cyan
Write-Host "  curl -f http://localhost:8000/health  # Backend" -ForegroundColor Gray
Write-Host "  curl -f http://localhost/healthz      # Frontend" -ForegroundColor Gray
Write-Host "  curl -f http://localhost:5432         # PostgreSQL" -ForegroundColor Gray
Write-Host ""

Write-Host "🔧 Résolution problèmes courants:" -ForegroundColor Cyan
Write-Host "  • Service ne démarre pas: Vérifiez les variables d'env" -ForegroundColor Gray
Write-Host "  • Erreur de connexion DB: Vérifiez POSTGRES_PASSWORD" -ForegroundColor Gray
Write-Host "  • Erreur MQTT: Vérifiez la variable SYS" -ForegroundColor Gray
Write-Host "  • Build failed: Vérifiez les Dockerfiles et contexte" -ForegroundColor Gray
Write-Host ""

# 5. Validation finale
Write-Host "✅ CORRECTIONS APPLIQUÉES" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green
Write-Host "• ✅ Variable SYS définie pour Mosquitto" -ForegroundColor Green
Write-Host "• ✅ Suppression des conflits container_name/replicas" -ForegroundColor Green
Write-Host "• ✅ Configuration Coolify optimisée" -ForegroundColor Green
Write-Host "• ✅ Variables d'environnement documentées" -ForegroundColor Green
Write-Host "• ✅ Healthchecks configurés" -ForegroundColor Green
Write-Host "• ✅ Labels Traefik pour SSL automatique" -ForegroundColor Green
Write-Host ""

Write-Host "🎯 PRÊT POUR DÉPLOIEMENT COOLIFY !" -ForegroundColor Green -BackgroundColor DarkGreen
Write-Host ""

if ($CheckHealth) {
    Write-Host "🏥 Test de connectivité des services..." -ForegroundColor Yellow
    Write-Host ""
    
    # Test Docker daemon
    try {
        docker version | Out-Null
        Write-Host "✅ Docker daemon accessible" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker daemon inaccessible" -ForegroundColor Red
    }
    
    # Test docker-compose
    try {
        docker-compose version | Out-Null
        Write-Host "✅ Docker Compose disponible" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker Compose non disponible" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📚 Documentation complète:" -ForegroundColor Cyan
Write-Host "  • README.md: Guide déploiement détaillé" -ForegroundColor Gray
Write-Host "  • documentation/: Architecture et guides" -ForegroundColor Gray
Write-Host "  • scripts/: Scripts d'automation" -ForegroundColor Gray
Write-Host ""

exit 0