# =============================================================================
# DÉPLOIEMENT COOLIFY - Station Traffeyère IoT/AI Platform
# Script pour déployer sur instance Coolify existante Ubuntu Server
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$CoolifyURL,
    
    [Parameter(Mandatory=$true)]
    [string]$CoolifyToken,
    
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$KeyPath = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "/home/$Username/station-traffeyere",
    
    [Parameter(Mandatory=$false)]
    [string]$GitRepository = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTransfer,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

Write-Host "🚀 Déploiement Station Traffeyère vers Coolify Ubuntu Server" -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue
Write-Host ""

# Configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Validation des paramètres
if (-not $CoolifyURL.StartsWith("http")) {
    $CoolifyURL = "https://$CoolifyURL"
}

Write-Host "🔧 Configuration de déploiement:" -ForegroundColor Cyan
Write-Host "   Coolify URL: $CoolifyURL" -ForegroundColor Gray
Write-Host "   Serveur Ubuntu: $Username@$ServerIP" -ForegroundColor Gray
Write-Host "   Chemin projet: $ProjectPath" -ForegroundColor Gray
if ($GitRepository) { Write-Host "   Dépôt Git: $GitRepository" -ForegroundColor Gray }
Write-Host ""

# Vérification des prérequis
Write-Host "🔍 Vérification des prérequis..." -ForegroundColor Yellow

# Vérifier curl ou Invoke-RestMethod
try {
    $null = Get-Command curl -ErrorAction Stop
    $useCurl = $true
} catch {
    $useCurl = $false
    Write-Host "   curl non trouvé, utilisation de PowerShell natif" -ForegroundColor Gray
}

# Vérifier SSH/SCP si transfert nécessaire
if (-not $SkipTransfer) {
    try {
        $null = Get-Command scp -ErrorAction Stop
        $null = Get-Command ssh -ErrorAction Stop
        Write-Host "✅ SSH/SCP disponibles" -ForegroundColor Green
    } catch {
        Write-Host "❌ SSH/SCP non disponibles. Installez OpenSSH ou utilisez -SkipTransfer" -ForegroundColor Red
        exit 1
    }
}

# Fonction pour appeler l'API Coolify
function Invoke-CoolifyAPI {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [hashtable]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    $headers = @{
        "Authorization" = "Bearer $CoolifyToken"
        "Accept" = "application/json"
    }
    
    $url = "$CoolifyURL/api/v1/$Endpoint"
    
    try {
        if ($useCurl) {
            # Utiliser curl
            $curlArgs = @(
                "-s"
                "-H", "Authorization: Bearer $CoolifyToken"
                "-H", "Accept: application/json"
            )
            
            if ($Body) {
                $curlArgs += "-H", "Content-Type: $ContentType"
                $curlArgs += "-X", $Method.ToUpper()
                $curlArgs += "-d", ($Body | ConvertTo-Json -Compress)
            }
            
            $curlArgs += $url
            
            $response = & curl @curlArgs
            return $response | ConvertFrom-Json
        } else {
            # Utiliser PowerShell natif
            $params = @{
                Uri = $url
                Method = $Method
                Headers = $headers
            }
            
            if ($Body) {
                $params.Body = ($Body | ConvertTo-Json -Depth 10)
                $params.ContentType = $ContentType
            }
            
            return Invoke-RestMethod @params
        }
    } catch {
        Write-Host "❌ Erreur API Coolify: $($_.Exception.Message)" -ForegroundColor Red
        throw
    }
}

# Test de connexion Coolify
Write-Host "🔗 Test de connexion Coolify..." -ForegroundColor Yellow
try {
    $coolifyInfo = Invoke-CoolifyAPI -Endpoint "version"
    Write-Host "✅ Coolify connecté - Version: $($coolifyInfo.version)" -ForegroundColor Green
} catch {
    Write-Host "❌ Impossible de se connecter à Coolify ($CoolifyURL)" -ForegroundColor Red
    Write-Host "   Vérifiez l'URL et le token d'authentification" -ForegroundColor Gray
    exit 1
}

# Transfert des fichiers vers Ubuntu (si nécessaire)
if (-not $SkipTransfer) {
    Write-Host "📦 Transfert des fichiers vers Ubuntu Server..." -ForegroundColor Yellow
    
    $transferArgs = @{
        ServerIP = $ServerIP
        Username = $Username
        ProjectPath = $ProjectPath
    }
    
    if ($KeyPath) {
        $transferArgs.KeyPath = $KeyPath
    }
    
    try {
        & ".\deploy-to-ubuntu.ps1" @transferArgs
        Write-Host "✅ Transfert terminé" -ForegroundColor Green
    } catch {
        Write-Host "❌ Erreur lors du transfert: $($_.Exception.Message)" -ForegroundColor Red
        if (-not $Force) {
            exit 1
        }
    }
} else {
    Write-Host "⏭️  Transfert ignoré (-SkipTransfer)" -ForegroundColor Yellow
}

# Configuration SSH pour commandes distantes
$sshOptions = @()
if ($KeyPath) {
    $sshOptions += "-i", $KeyPath
}
$sshTarget = "$Username@$ServerIP"

# Fonction pour exécuter des commandes SSH
function Invoke-SSHCommand {
    param([string]$Command)
    
    if ($sshOptions) {
        return & ssh @sshOptions $sshTarget $Command
    } else {
        return & ssh $sshTarget $Command
    }
}

# Vérification de l'environnement Ubuntu
Write-Host "🔍 Vérification de l'environnement Ubuntu..." -ForegroundColor Yellow

try {
    $ubuntuVersion = Invoke-SSHCommand "lsb_release -ds 2>/dev/null || echo 'Ubuntu version inconnue'"
    Write-Host "   OS: $ubuntuVersion" -ForegroundColor Gray
    
    $dockerVersion = Invoke-SSHCommand "docker --version 2>/dev/null || echo 'Docker non installé'"
    Write-Host "   Docker: $dockerVersion" -ForegroundColor Gray
    
    # Vérifier si le projet existe
    $projectExists = Invoke-SSHCommand "test -d $ProjectPath && echo 'exists' || echo 'missing'"
    if ($projectExists -eq "missing") {
        Write-Host "❌ Projet non trouvé à $ProjectPath" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Environnement Ubuntu validé" -ForegroundColor Green
} catch {
    Write-Host "❌ Impossible de se connecter au serveur Ubuntu" -ForegroundColor Red
    exit 1
}

# Génération/vérification des secrets sur Ubuntu
Write-Host "🔐 Configuration des secrets..." -ForegroundColor Yellow

try {
    $envExists = Invoke-SSHCommand "test -f $ProjectPath/.env && echo 'exists' || echo 'missing'"
    
    if ($envExists -eq "missing") {
        Write-Host "   Génération des secrets..." -ForegroundColor Gray
        Invoke-SSHCommand "cd $ProjectPath && ./generate-secrets.sh --env"
        Write-Host "✅ Secrets générés" -ForegroundColor Green
    } else {
        Write-Host "✅ Fichier .env existant trouvé" -ForegroundColor Green
    }
    
    # Vérifier les variables critiques
    $domainSet = Invoke-SSHCommand "cd $ProjectPath && grep -q 'DOMAIN_ROOT=' .env && echo 'set' || echo 'missing'"
    if ($domainSet -eq "missing") {
        Write-Host "⚠️  Variable DOMAIN_ROOT non configurée dans .env" -ForegroundColor Yellow
        Write-Host "   Configurez manuellement ou relancez generate-secrets.sh" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Erreur lors de la configuration des secrets" -ForegroundColor Red
    if (-not $Force) { exit 1 }
}

# Création du projet Coolify
Write-Host "🏗️  Configuration du projet Coolify..." -ForegroundColor Yellow

$projectName = "station-traffeyere-iot"
$projectData = @{
    name = $projectName
    description = "Station Traffeyère IoT/AI Platform - Production"
}

try {
    # Vérifier si le projet existe
    $existingProjects = Invoke-CoolifyAPI -Endpoint "projects"
    $existingProject = $existingProjects | Where-Object { $_.name -eq $projectName }
    
    if ($existingProject) {
        Write-Host "✅ Projet '$projectName' existe déjà (ID: $($existingProject.uuid))" -ForegroundColor Green
        $projectId = $existingProject.uuid
    } else {
        Write-Host "   Création du nouveau projet '$projectName'..." -ForegroundColor Gray
        $newProject = Invoke-CoolifyAPI -Endpoint "projects" -Method "POST" -Body $projectData
        $projectId = $newProject.uuid
        Write-Host "✅ Projet créé avec l'ID: $projectId" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Erreur lors de la création/récupération du projet Coolify" -ForegroundColor Red
    throw
}

# Déploiement des services via Coolify API
Write-Host "🚀 Déploiement des services..." -ForegroundColor Yellow

# Services à déployer dans l'ordre
$services = @(
    @{
        name = "postgres"
        type = "postgresql"
        image = "postgres:15-alpine"
        env = @{
            POSTGRES_DB = "`${POSTGRES_DB}"
            POSTGRES_USER = "`${POSTGRES_USER}"
            POSTGRES_PASSWORD = "`${POSTGRES_PASSWORD}"
        }
        memory = 512
        domains = @()
    },
    @{
        name = "redis" 
        type = "redis"
        image = "redis:7-alpine"
        env = @{
            REDIS_PASSWORD = "`${REDIS_PASSWORD}"
        }
        memory = 256
        domains = @()
    },
    @{
        name = "backend"
        type = "application"
        source = if ($GitRepository) { @{ type = "git"; repository = $GitRepository; branch = "master" } } else { @{ type = "dockerfile"; path = "./backend" } }
        env = @{
            DATABASE_URL = "postgresql://`${POSTGRES_USER}:`${POSTGRES_PASSWORD}@postgres:5432/`${POSTGRES_DB}"
            REDIS_URL = "redis://:`${REDIS_PASSWORD}@redis:6379/0"
            SECRET_KEY = "`${SECRET_KEY}"
            JWT_SECRET = "`${JWT_SECRET}"
            ENVIRONMENT = "production"
        }
        memory = 1024
        domains = @("api.`${DOMAIN_ROOT}")
    },
    @{
        name = "frontend"
        type = "application"
        source = if ($GitRepository) { @{ type = "git"; repository = $GitRepository; branch = "master" } } else { @{ type = "dockerfile"; path = "./frontend" } }
        env = @{
            NODE_ENV = "production"
            NEXT_PUBLIC_API_URL = "https://api.`${DOMAIN_ROOT}"
        }
        memory = 512
        domains = @("`${DOMAIN_ROOT}", "www.`${DOMAIN_ROOT}", "app.`${DOMAIN_ROOT}")
    }
)

foreach ($service in $services) {
    Write-Host "   Déploiement: $($service.name)" -ForegroundColor Gray
    
    try {
        # Créer le service dans Coolify
        $serviceData = @{
            project_uuid = $projectId
            name = $service.name
            type = $service.type
            image = $service.image
            environment_variables = $service.env
            memory_limit = $service.memory
            domains = $service.domains -join ","
        }
        
        if ($service.source) {
            $serviceData.source = $service.source
        }
        
        $createdService = Invoke-CoolifyAPI -Endpoint "applications" -Method "POST" -Body $serviceData
        Write-Host "     ✅ Service $($service.name) créé" -ForegroundColor Green
        
        # Démarrer le déploiement
        Start-Sleep 2
        Invoke-CoolifyAPI -Endpoint "applications/$($createdService.uuid)/deploy" -Method "POST"
        Write-Host "     🚀 Déploiement lancé pour $($service.name)" -ForegroundColor Blue
        
    } catch {
        Write-Host "     ❌ Erreur avec le service $($service.name): $($_.Exception.Message)" -ForegroundColor Red
        if (-not $Force) { 
            throw 
        }
    }
    
    Start-Sleep 3
}

Write-Host ""
Write-Host "🎉 DÉPLOIEMENT COOLIFY TERMINÉ !" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

Write-Host "🌐 ACCÈS AUX SERVICES:" -ForegroundColor Magenta
Write-Host "• Coolify Dashboard: $CoolifyURL" -ForegroundColor White
Write-Host "• Frontend: https://app.votre-domaine.com" -ForegroundColor White  
Write-Host "• API Backend: https://api.votre-domaine.com" -ForegroundColor White
Write-Host "• Monitoring: https://grafana.votre-domaine.com" -ForegroundColor White
Write-Host ""

Write-Host "📋 PROCHAINES ÉTAPES:" -ForegroundColor Cyan
Write-Host "1. Connectez-vous au dashboard Coolify: $CoolifyURL" -ForegroundColor White
Write-Host "2. Vérifiez le statut des déploiements dans le projet '$projectName'" -ForegroundColor White
Write-Host "3. Configurez vos DNS pour pointer vers $ServerIP" -ForegroundColor White
Write-Host "4. Attendez que les certificats SSL soient générés" -ForegroundColor White
Write-Host "5. Testez vos applications via les URLs ci-dessus" -ForegroundColor White
Write-Host ""

Write-Host "🔧 COMMANDES UTILES:" -ForegroundColor Yellow
Write-Host "# Surveiller les logs sur Ubuntu:" -ForegroundColor Gray
Write-Host "ssh $sshTarget 'docker logs -f container_name'" -ForegroundColor Gray
Write-Host ""
Write-Host "# Redémarrer un service via API:" -ForegroundColor Gray
Write-Host "curl -H 'Authorization: Bearer $CoolifyToken' -X POST $CoolifyURL/api/v1/applications/SERVICE_ID/restart" -ForegroundColor Gray
Write-Host ""

# Surveillance du déploiement (optionnel)
$monitor = Read-Host "Voulez-vous surveiller le déploiement en temps réel ? (y/N)"
if ($monitor -eq "y" -or $monitor -eq "Y") {
    Write-Host "📊 Surveillance du déploiement..." -ForegroundColor Blue
    Write-Host "Appuyez sur Ctrl+C pour arrêter la surveillance" -ForegroundColor Gray
    Write-Host ""
    
    do {
        try {
            $deployments = Invoke-CoolifyAPI -Endpoint "projects/$projectId/deployments"
            $runningDeployments = $deployments | Where-Object { $_.status -eq "running" }
            
            if ($runningDeployments) {
                Write-Host "🔄 Déploiements en cours: $($runningDeployments.Count)" -ForegroundColor Yellow
                foreach ($deployment in $runningDeployments) {
                    Write-Host "   • $($deployment.application_name): $($deployment.status)" -ForegroundColor Gray
                }
            } else {
                Write-Host "✅ Tous les déploiements terminés !" -ForegroundColor Green
                break
            }
            
            Start-Sleep 10
        } catch {
            Write-Host "⚠️  Erreur lors de la surveillance: $($_.Exception.Message)" -ForegroundColor Yellow
            break
        }
    } while ($true)
}

Write-Host ""
Write-Host "🏁 Déploiement Coolify terminé avec succès !" -ForegroundColor Green