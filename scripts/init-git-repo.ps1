# =============================================================================
# INITIALISATION REPOSITORY GIT - Station Traffeyère IoT/AI Platform
# Prépare le repository pour le déploiement sur Coolify
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$RemoteURL = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$CreateMain,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

Write-Host "🔧 Initialisation Repository Git - Station Traffeyère" -ForegroundColor Blue
Write-Host "====================================================" -ForegroundColor Blue
Write-Host ""

# Vérifier l'état actuel du repository
Write-Host "🔍 Vérification de l'état Git..." -ForegroundColor Yellow

$gitStatus = git status --porcelain 2>$null
$currentBranch = git branch --show-current 2>$null
$hasRemote = git remote -v 2>$null

Write-Host "   Branche actuelle: $currentBranch" -ForegroundColor Gray
Write-Host "   Fichiers modifiés: $(if($gitStatus) { ($gitStatus | Measure-Object).Count } else { '0' })" -ForegroundColor Gray

if ($hasRemote) {
    Write-Host "   Remote configuré: ✅" -ForegroundColor Green
    git remote -v | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
} else {
    Write-Host "   Remote configuré: ❌" -ForegroundColor Red
}

Write-Host ""

# Option 1: Créer une branche main si demandé
if ($CreateMain) {
    Write-Host "🌿 Création de la branche main..." -ForegroundColor Yellow
    
    try {
        # S'assurer qu'on est sur master
        git checkout master
        
        # Créer et checkout la branche main
        git checkout -b main
        
        # Push la nouvelle branche
        if ($hasRemote) {
            git push -u origin main
            Write-Host "✅ Branche main créée et poussée vers le remote" -ForegroundColor Green
        } else {
            Write-Host "✅ Branche main créée localement" -ForegroundColor Green
            Write-Host "⚠️  Configurez un remote pour pousser la branche" -ForegroundColor Yellow
        }
        
        $currentBranch = "main"
    } catch {
        Write-Host "❌ Erreur lors de la création de la branche main: $($_.Exception.Message)" -ForegroundColor Red
        if (-not $Force) { exit 1 }
    }
}

# Ajouter un remote si fourni
if ($RemoteURL) {
    Write-Host "🔗 Configuration du remote..." -ForegroundColor Yellow
    
    try {
        # Supprimer le remote existant si nécessaire
        if ($hasRemote) {
            git remote remove origin
        }
        
        # Ajouter le nouveau remote
        git remote add origin $RemoteURL
        
        # Vérifier la connexion
        git ls-remote origin > $null
        
        Write-Host "✅ Remote configuré: $RemoteURL" -ForegroundColor Green
        
        # Push la branche actuelle
        git push -u origin $currentBranch
        Write-Host "✅ Branche $currentBranch poussée vers le remote" -ForegroundColor Green
        
    } catch {
        Write-Host "❌ Erreur lors de la configuration du remote: $($_.Exception.Message)" -ForegroundColor Red
        if (-not $Force) { exit 1 }
    }
}

# Commit les changements si nécessaire
if ($gitStatus) {
    Write-Host "📝 Commit des modifications en attente..." -ForegroundColor Yellow
    
    $commitMessage = "feat: Configuration déploiement Coolify Ubuntu Server

- Scripts de déploiement automatisé
- Configuration Docker adaptée
- Support Coolify API
- Documentation complète
- Variables d'environnement sécurisées

Prêt pour déploiement production sur Ubuntu + Coolify"

    try {
        git add .
        git commit -m $commitMessage
        
        Write-Host "✅ Modifications commitées" -ForegroundColor Green
        Write-Host "   Message: Configuration déploiement Coolify Ubuntu Server" -ForegroundColor Gray
        
        # Push si remote configuré
        if (git remote -v 2>$null) {
            git push
            Write-Host "✅ Changements poussés vers le remote" -ForegroundColor Green
        }
        
    } catch {
        Write-Host "❌ Erreur lors du commit: $($_.Exception.Message)" -ForegroundColor Red
        if (-not $Force) { exit 1 }
    }
} else {
    Write-Host "✅ Aucune modification à committer" -ForegroundColor Green
}

# Afficher l'état final
Write-Host ""
Write-Host "📊 État final du repository:" -ForegroundColor Cyan

$finalBranch = git branch --show-current
$finalRemote = git remote -v 2>$null
$lastCommit = git log --oneline -1 2>$null

Write-Host "   Branche active: $finalBranch" -ForegroundColor White
if ($finalRemote) {
    Write-Host "   Remote:" -ForegroundColor White
    $finalRemote | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
} else {
    Write-Host "   Remote: Non configuré" -ForegroundColor Yellow
}
Write-Host "   Dernier commit: $lastCommit" -ForegroundColor Gray

Write-Host ""

# Recommandations basées sur la configuration
Write-Host "💡 RECOMMANDATIONS:" -ForegroundColor Magenta

if ($finalBranch -eq "master") {
    Write-Host "✅ Vous êtes sur la branche 'master'" -ForegroundColor Green
    Write-Host "   Vos scripts Coolify sont configurés pour utiliser 'master'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Pour créer une branche 'main' (optionnel):" -ForegroundColor Yellow
    Write-Host "   .\init-git-repo.ps1 -CreateMain" -ForegroundColor Gray
} elseif ($finalBranch -eq "main") {
    Write-Host "✅ Vous êtes sur la branche 'main'" -ForegroundColor Green
    Write-Host "   Vos scripts Coolify utilisent maintenant 'master'" -ForegroundColor Yellow
    Write-Host "   Vous pouvez:" -ForegroundColor Yellow
    Write-Host "   1. Rester sur 'main' et modifier les scripts pour utiliser 'main'" -ForegroundColor Gray
    Write-Host "   2. Ou revenir sur 'master': git checkout master" -ForegroundColor Gray
}

if (-not $finalRemote) {
    Write-Host ""
    Write-Host "⚠️  Remote Git non configuré" -ForegroundColor Yellow
    Write-Host "   Pour déployer via Git avec Coolify:" -ForegroundColor Gray
    Write-Host "   .\init-git-repo.ps1 -RemoteURL 'https://github.com/username/repo.git'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Ou déployez via fichiers locaux (sans Git)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🚀 PROCHAINES ÉTAPES:" -ForegroundColor Cyan

if ($finalRemote) {
    Write-Host "1. Votre repository est prêt pour le déploiement Git!" -ForegroundColor White
    Write-Host "2. Utilisez l'URL du repository dans le déploiement Coolify:" -ForegroundColor White
    
    $repoURL = (git remote get-url origin 2>$null)
    if ($repoURL) {
        Write-Host "   Repository URL: $repoURL" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "3. Commande de déploiement avec Git:" -ForegroundColor White
    Write-Host "   .\deploy-to-coolify.ps1 -CoolifyURL 'your-coolify' -CoolifyToken 'token' -ServerIP 'ip' -Username 'ubuntu' -GitRepository '$repoURL'" -ForegroundColor Gray
} else {
    Write-Host "1. Repository prêt pour déploiement local (sans Git)" -ForegroundColor White
    Write-Host "2. Commande de déploiement local:" -ForegroundColor White
    Write-Host "   .\deploy-to-coolify.ps1 -CoolifyURL 'your-coolify' -CoolifyToken 'token' -ServerIP 'ip' -Username 'ubuntu'" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Repository Git initialisé avec succès!" -ForegroundColor Green