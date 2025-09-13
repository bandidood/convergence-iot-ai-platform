# =============================================================================
# SCRIPT DE TRANSFERT - Station Traffeyère IoT/AI Platform
# Transfert des fichiers de configuration depuis Windows vers Ubuntu Server
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$KeyPath = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "/home/$Username/station-traffeyere",
    
    [Parameter(Mandatory=$false)]
    [switch]$CreateEnv
)

Write-Host "🚀 Déploiement Station Traffeyère vers Ubuntu Server" -ForegroundColor Blue
Write-Host "=====================================================" -ForegroundColor Blue
Write-Host ""

# Vérification des prérequis
$scpPath = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scpPath) {
    Write-Host "❌ SCP n'est pas installé. Installez OpenSSH ou Git Bash." -ForegroundColor Red
    Write-Host "💡 Vous pouvez installer OpenSSH avec: Add-WindowsCapability -Online -Name OpenSSH.Client" -ForegroundColor Yellow
    exit 1
}

# Configuration SSH
$sshOptions = @()
if ($KeyPath) {
    if (Test-Path $KeyPath) {
        $sshOptions += "-i `"$KeyPath`""
    } else {
        Write-Host "❌ Fichier de clé SSH introuvable: $KeyPath" -ForegroundColor Red
        exit 1
    }
}

$sshString = if ($KeyPath) { "$($sshOptions -join ' ') $Username@$ServerIP" } else { "$Username@$ServerIP" }

Write-Host "🔧 Configuration:" -ForegroundColor Cyan
Write-Host "   Serveur: $Username@$ServerIP" -ForegroundColor Gray
Write-Host "   Chemin projet: $ProjectPath" -ForegroundColor Gray
if ($KeyPath) { Write-Host "   Clé SSH: $KeyPath" -ForegroundColor Gray }
Write-Host ""

# Test de connexion SSH
Write-Host "🔍 Test de connexion SSH..." -ForegroundColor Yellow
$testConnection = if ($KeyPath) {
    ssh $sshOptions.Split(' ') $Username@$ServerIP "echo 'Connexion réussie'"
} else {
    ssh $Username@$ServerIP "echo 'Connexion réussie'"
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Impossible de se connecter au serveur Ubuntu" -ForegroundColor Red
    Write-Host "💡 Vérifiez:" -ForegroundColor Yellow
    Write-Host "   - L'adresse IP du serveur" -ForegroundColor Gray
    Write-Host "   - Le nom d'utilisateur" -ForegroundColor Gray
    Write-Host "   - La clé SSH (si utilisée)" -ForegroundColor Gray
    Write-Host "   - Que le service SSH est actif sur Ubuntu" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ Connexion SSH établie" -ForegroundColor Green
Write-Host ""

# Création du répertoire projet sur Ubuntu
Write-Host "📁 Création du répertoire projet..." -ForegroundColor Yellow
if ($KeyPath) {
    ssh $sshOptions.Split(' ') $Username@$ServerIP "mkdir -p $ProjectPath && cd $ProjectPath"
} else {
    ssh $Username@$ServerIP "mkdir -p $ProjectPath && cd $ProjectPath"
}

# Liste des fichiers à transférer
$filesToTransfer = @(
    @{Local=".env.production"; Remote=".env.production"},
    @{Local="generate-secrets.sh"; Remote="generate-secrets.sh"},
    @{Local="deploy-coolify.sh"; Remote="deploy-coolify.sh"},
    @{Local="docker-compose.prod.yml"; Remote="docker-compose.prod.yml"},
    @{Local="DEPLOYMENT_GUIDE.md"; Remote="DEPLOYMENT_GUIDE.md"},
    @{Local="README-DEPLOYMENT.md"; Remote="README-DEPLOYMENT.md"}
)

# Répertoires à transférer
$dirsToTransfer = @(
    "config",
    "backend",
    "frontend"
)

Write-Host "📦 Transfert des fichiers de configuration..." -ForegroundColor Yellow

# Transfert des fichiers individuels
foreach ($file in $filesToTransfer) {
    if (Test-Path $file.Local) {
        Write-Host "   Transfert: $($file.Local)" -ForegroundColor Gray
        if ($KeyPath) {
            scp $sshOptions.Split(' ') $file.Local "$Username@$ServerIP`:$ProjectPath/$($file.Remote)"
        } else {
            scp $file.Local "$Username@$ServerIP`:$ProjectPath/$($file.Remote)"
        }
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Erreur lors du transfert de $($file.Local)" -ForegroundColor Red
        } else {
            Write-Host "   ✅ $($file.Local) transféré" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️  Fichier non trouvé: $($file.Local)" -ForegroundColor Yellow
    }
}

# Transfert des répertoires
foreach ($dir in $dirsToTransfer) {
    if (Test-Path $dir) {
        Write-Host "   Transfert du répertoire: $dir" -ForegroundColor Gray
        if ($KeyPath) {
            scp -r $sshOptions.Split(' ') $dir "$Username@$ServerIP`:$ProjectPath/"
        } else {
            scp -r $dir "$Username@$ServerIP`:$ProjectPath/"
        }
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Erreur lors du transfert du répertoire $dir" -ForegroundColor Red
        } else {
            Write-Host "   ✅ Répertoire $dir transféré" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️  Répertoire non trouvé: $dir" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🔧 Configuration des permissions sur Ubuntu..." -ForegroundColor Yellow

# Commandes à exécuter sur Ubuntu
$ubuntuCommands = @(
    "cd $ProjectPath",
    "chmod +x *.sh",
    "chmod -R 755 config/",
    "find . -name '*.yml' -exec chmod 644 {} \;",
    "find . -name '*.json' -exec chmod 644 {} \;",
    "find . -name '*.conf' -exec chmod 644 {} \;"
)

foreach ($cmd in $ubuntuCommands) {
    Write-Host "   Exécution: $cmd" -ForegroundColor Gray
    if ($KeyPath) {
        ssh $sshOptions.Split(' ') $Username@$ServerIP $cmd
    } else {
        ssh $Username@$ServerIP $cmd
    }
}

Write-Host "✅ Permissions configurées" -ForegroundColor Green
Write-Host ""

# Installation des prérequis Ubuntu
Write-Host "📋 Installation des prérequis Ubuntu..." -ForegroundColor Yellow
$prerequisites = @(
    "sudo apt update",
    "sudo apt install -y curl wget git openssl pwgen docker.io docker-compose",
    "sudo systemctl enable docker",
    "sudo systemctl start docker",
    "sudo usermod -aG docker $Username",
    "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash"
)

Write-Host "💡 Commandes à exécuter sur votre serveur Ubuntu:" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
foreach ($cmd in $prerequisites) {
    Write-Host "   $cmd" -ForegroundColor Gray
}
Write-Host ""

# Génération des secrets si demandé
if ($CreateEnv) {
    Write-Host "🔐 Génération du fichier .env sur Ubuntu..." -ForegroundColor Yellow
    if ($KeyPath) {
        ssh $sshOptions.Split(' ') $Username@$ServerIP "cd $ProjectPath && ./generate-secrets.sh"
    } else {
        ssh $Username@$ServerIP "cd $ProjectPath && ./generate-secrets.sh"
    }
}

Write-Host ""
Write-Host "🎉 TRANSFERT TERMINÉ AVEC SUCCÈS!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 PROCHAINES ÉTAPES SUR UBUNTU SERVER:" -ForegroundColor Cyan
Write-Host "1. Connectez-vous à votre serveur:" -ForegroundColor White
Write-Host "   ssh $Username@$ServerIP" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Allez dans le répertoire projet:" -ForegroundColor White
Write-Host "   cd $ProjectPath" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Générez les secrets (si pas fait):" -ForegroundColor White
Write-Host "   ./generate-secrets.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Configurez votre domaine dans .env" -ForegroundColor White
Write-Host ""
Write-Host "5. Lancez le déploiement:" -ForegroundColor White
Write-Host "   ./deploy-coolify.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 Consultez DEPLOYMENT_GUIDE.md pour les détails" -ForegroundColor Yellow
Write-Host ""

# Affichage des URLs d'accès prévues
Write-Host "🌐 URLs D'ACCÈS APRÈS DÉPLOIEMENT:" -ForegroundColor Magenta
Write-Host "===================================" -ForegroundColor Magenta
Write-Host "Frontend:    https://app.votre-domaine.com" -ForegroundColor White
Write-Host "API:         https://api.votre-domaine.com" -ForegroundColor White
Write-Host "Grafana:     https://grafana.votre-domaine.com" -ForegroundColor White
Write-Host "Coolify:     https://coolify.votre-domaine.com" -ForegroundColor White
Write-Host ""