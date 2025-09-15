# =====================================================================================
# Station Traffeyère Digital Twin - Script de Build Unity
# RNCP 39394 - Automatisation construction et déploiement
# =====================================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("Development", "Staging", "Production")]
    [string]$Environment = "Development",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("StandaloneLinux64", "StandaloneWindows64", "WebGL")]
    [string]$BuildTarget = "StandaloneLinux64",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDockerBuild = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$RunAfterBuild = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false
)

# Configuration
$ErrorActionPreference = "Stop"
$ProjectPath = Get-Location
$UnityProjectPath = Join-Path $ProjectPath "StationTraffeyereUnity"
$BuildOutputPath = Join-Path $ProjectPath "builds"
$DockerImageName = "station-traffeyere/unity-digital-twin"
$DockerImageTag = "latest"

# Logging avec couleurs
function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("INFO", "SUCCESS", "WARNING", "ERROR")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO"    { "Cyan" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR"   { "Red" }
    }
    
    Write-Host "[$Level] $timestamp - $Message" -ForegroundColor $color
}

function Test-UnityInstallation {
    Write-Log "🔍 Vérification installation Unity..." -Level "INFO"
    
    # Chemins Unity courants
    $unityPaths = @(
        "${env:ProgramFiles}\Unity\Hub\Editor\*\Editor\Unity.exe",
        "${env:ProgramFiles(x86)}\Unity\Hub\Editor\*\Editor\Unity.exe",
        "C:\Program Files\Unity\Hub\Editor\*\Editor\Unity.exe"
    )
    
    foreach ($path in $unityPaths) {
        $unityExe = Get-ChildItem $path -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($unityExe) {
            Write-Log "✅ Unity trouvé: $($unityExe.FullName)" -Level "SUCCESS"
            return $unityExe.FullName
        }
    }
    
    Write-Log "❌ Unity non trouvé! Veuillez installer Unity Hub et Unity Editor 2022.3+" -Level "ERROR"
    return $null
}

function Test-DockerInstallation {
    Write-Log "🐳 Vérification installation Docker..." -Level "INFO"
    
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Log "✅ Docker disponible: $dockerVersion" -Level "SUCCESS"
            return $true
        }
    } catch {
        Write-Log "❌ Docker non disponible!" -Level "ERROR"
        return $false
    }
    
    return $false
}

function New-UnityProject {
    param([string]$UnityPath)
    
    Write-Log "🎮 Création projet Unity Digital Twin..." -Level "INFO"
    
    if (-not (Test-Path $UnityProjectPath)) {
        Write-Log "📁 Création structure projet: $UnityProjectPath" -Level "INFO"
        New-Item -ItemType Directory -Path $UnityProjectPath -Force
        
        # Structure projet Unity basique
        $directories = @(
            "Assets",
            "Assets\Scripts",
            "Assets\Scripts\DigitalTwin",
            "Assets\Scenes",
            "Assets\Prefabs",
            "Assets\Materials",
            "Assets\Textures",
            "ProjectSettings"
        )
        
        foreach ($dir in $directories) {
            $fullPath = Join-Path $UnityProjectPath $dir
            New-Item -ItemType Directory -Path $fullPath -Force
        }
        
        Write-Log "✅ Structure projet Unity créée" -Level "SUCCESS"
    } else {
        Write-Log "✅ Projet Unity existant: $UnityProjectPath" -Level "SUCCESS"
    }
}

function Copy-UnityScripts {
    Write-Log "📋 Copie scripts Unity vers projet..." -Level "INFO"
    
    $scriptsSource = Join-Path $ProjectPath "unity-scripts"
    $scriptsTarget = Join-Path $UnityProjectPath "Assets\Scripts\DigitalTwin"
    
    if (Test-Path $scriptsSource) {
        try {
            Copy-Item "$scriptsSource\*" $scriptsTarget -Recurse -Force
            Write-Log "✅ Scripts Unity copiés vers le projet" -Level "SUCCESS"
        } catch {
            Write-Log "⚠️ Erreur copie scripts: $($_.Exception.Message)" -Level "WARNING"
        }
    } else {
        Write-Log "⚠️ Répertoire scripts Unity introuvable: $scriptsSource" -Level "WARNING"
    }
}

function Start-UnityBuild {
    param(
        [string]$UnityPath,
        [string]$Target,
        [string]$Env
    )
    
    Write-Log "🔨 Démarrage build Unity ($Target - $Env)..." -Level "INFO"
    
    # Configuration build selon environnement
    $buildConfig = switch ($Env) {
        "Development" { 
            @{
                DefineSymbols = "DEVELOPMENT_BUILD;UNITY_ASSERTIONS"
                Optimize = $false
                DebugSymbols = $true
            }
        }
        "Staging" { 
            @{
                DefineSymbols = "STAGING_BUILD"
                Optimize = $true
                DebugSymbols = $true
            }
        }
        "Production" { 
            @{
                DefineSymbols = "PRODUCTION_BUILD"
                Optimize = $true
                DebugSymbols = $false
            }
        }
    }
    
    # Préparation build output
    $buildName = "StationTraffeyere_$($Target)_$Env"
    $buildPath = Join-Path $BuildOutputPath $buildName
    
    if (Test-Path $buildPath) {
        Write-Log "🗑️ Nettoyage build précédent: $buildPath" -Level "INFO"
        Remove-Item $buildPath -Recurse -Force
    }
    
    New-Item -ItemType Directory -Path $buildPath -Force
    
    # Arguments Unity
    $unityArgs = @(
        "-batchmode"
        "-quit"
        "-projectPath", "`"$UnityProjectPath`""
        "-buildTarget", $Target
        "-logFile", "`"$(Join-Path $buildPath 'unity-build.log')`""
    )
    
    if ($buildConfig.DefineSymbols) {
        $unityArgs += @("-defineSymbols", $buildConfig.DefineSymbols)
    }
    
    # Script de build personnalisé (si disponible)
    $buildScript = Join-Path $UnityProjectPath "Assets\Scripts\Editor\BuildScript.cs"
    if (Test-Path $buildScript) {
        $unityArgs += @("-executeMethod", "BuildScript.Build$Target")
    }
    
    Write-Log "🚀 Exécution build Unity..." -Level "INFO"
    Write-Log "   Commande: `"$UnityPath`" $($unityArgs -join ' ')" -Level "INFO"
    
    try {
        $process = Start-Process -FilePath $UnityPath -ArgumentList $unityArgs -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            Write-Log "✅ Build Unity terminé avec succès" -Level "SUCCESS"
            
            # Vérification présence build
            $builtFiles = Get-ChildItem $buildPath -File | Measure-Object
            Write-Log "📦 Fichiers générés: $($builtFiles.Count)" -Level "INFO"
            
            return $buildPath
        } else {
            Write-Log "❌ Build Unity échoué (Code: $($process.ExitCode))" -Level "ERROR"
            
            # Affichage log d'erreur
            $logFile = Join-Path $buildPath 'unity-build.log'
            if (Test-Path $logFile) {
                Write-Log "📋 Log Unity:" -Level "ERROR"
                Get-Content $logFile -Tail 20 | ForEach-Object { Write-Log "    $_" -Level "ERROR" }
            }
            
            return $null
        }
    } catch {
        Write-Log "❌ Erreur exécution Unity: $($_.Exception.Message)" -Level "ERROR"
        return $null
    }
}

function New-DockerImage {
    param([string]$BuildPath)
    
    Write-Log "🐳 Construction image Docker..." -Level "INFO"
    
    try {
        # Préparation contexte Docker
        $dockerContext = Join-Path $ProjectPath "docker-build-context"
        if (Test-Path $dockerContext) {
            Remove-Item $dockerContext -Recurse -Force
        }
        New-Item -ItemType Directory -Path $dockerContext -Force
        
        # Copie build Unity
        $unityBuildTarget = Join-Path $dockerContext "builds"
        Copy-Item $BuildPath $unityBuildTarget -Recurse -Force
        
        # Copie API et configuration
        $apiSource = Join-Path $ProjectPath "api-server"
        $apiTarget = Join-Path $dockerContext "api-server"
        if (Test-Path $apiSource) {
            Copy-Item $apiSource $apiTarget -Recurse -Force
        }
        
        # Copie scripts Docker
        $scriptsSource = Join-Path $ProjectPath "docker-scripts"
        $scriptsTarget = Join-Path $dockerContext "docker-scripts"
        if (Test-Path $scriptsSource) {
            Copy-Item $scriptsSource $scriptsTarget -Recurse -Force
        }
        
        # Copie Dockerfile
        $dockerfileSource = Join-Path $ProjectPath "Dockerfile.headless"
        $dockerfileTarget = Join-Path $dockerContext "Dockerfile.headless"
        Copy-Item $dockerfileSource $dockerfileTarget -Force
        
        # Build Docker
        $dockerArgs = @(
            "build"
            "-t", "$($DockerImageName):$DockerImageTag"
            "-t", "$($DockerImageName):$Environment-$(Get-Date -Format 'yyyyMMdd-HHmm')"
            "-f", "Dockerfile.headless"
            "--target", "production"
            $dockerContext
        )
        
        Write-Log "🔨 Exécution: docker $($dockerArgs -join ' ')" -Level "INFO"
        
        $result = & docker @dockerArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Image Docker construite: $DockerImageName:$DockerImageTag" -Level "SUCCESS"
            
            # Affichage taille image
            $imageInfo = docker images $DockerImageName --format "{{.Size}}" | Select-Object -First 1
            Write-Log "📏 Taille image: $imageInfo" -Level "INFO"
            
            return $true
        } else {
            Write-Log "❌ Échec construction Docker" -Level "ERROR"
            return $false
        }
        
    } catch {
        Write-Log "❌ Erreur construction Docker: $($_.Exception.Message)" -Level "ERROR"
        return $false
    } finally {
        # Nettoyage contexte temporaire
        if (Test-Path $dockerContext) {
            Remove-Item $dockerContext -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Start-Services {
    Write-Log "🚀 Démarrage services via Docker Compose..." -Level "INFO"
    
    try {
        $composeFile = Join-Path $ProjectPath "docker-compose.unity.yml"
        
        if (-not (Test-Path $composeFile)) {
            Write-Log "❌ Fichier docker-compose.unity.yml introuvable" -Level "ERROR"
            return $false
        }
        
        # Démarrage services
        $composeArgs = @(
            "-f", $composeFile
            "up", "-d"
            "--build"
        )
        
        & docker-compose @composeArgs
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Services démarrés avec succès" -Level "SUCCESS"
            
            # Attente services
            Write-Log "⏳ Attente initialisation services..." -Level "INFO"
            Start-Sleep -Seconds 15
            
            # Status services
            Write-Log "📊 Status services:" -Level "INFO"
            docker-compose -f $composeFile ps
            
            Write-Log "🌐 URLs disponibles:" -Level "SUCCESS"
            Write-Log "   - API Digital Twin: http://localhost:8080/docs" -Level "INFO"
            Write-Log "   - Interface Web: http://localhost:8081" -Level "INFO"
            Write-Log "   - Grafana: http://localhost:3000" -Level "INFO"
            Write-Log "   - Prometheus: http://localhost:9090" -Level "INFO"
            
            return $true
        } else {
            Write-Log "❌ Échec démarrage services" -Level "ERROR"
            return $false
        }
        
    } catch {
        Write-Log "❌ Erreur démarrage services: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

# =====================================================================================
# SCRIPT PRINCIPAL
# =====================================================================================

Write-Log "🚀 Station Traffeyère Digital Twin - Build Script" -Level "SUCCESS"
Write-Log "📋 RNCP 39394 - Version 2.1.0" -Level "INFO"
Write-Log "🔧 Environnement: $Environment | Target: $BuildTarget" -Level "INFO"

try {
    # 1. Vérifications prérequis
    Write-Log "=== VÉRIFICATIONS PRÉREQUIS ===" -Level "INFO"
    
    $unityPath = Test-UnityInstallation
    if (-not $unityPath) {
        throw "Unity non disponible"
    }
    
    if (-not $SkipDockerBuild) {
        $dockerAvailable = Test-DockerInstallation
        if (-not $dockerAvailable) {
            throw "Docker non disponible"
        }
    }
    
    # 2. Préparation projet Unity
    Write-Log "=== PRÉPARATION PROJET UNITY ===" -Level "INFO"
    New-UnityProject -UnityPath $unityPath
    Copy-UnityScripts
    
    # 3. Build Unity
    Write-Log "=== BUILD UNITY ===" -Level "INFO"
    $buildPath = Start-UnityBuild -UnityPath $unityPath -Target $BuildTarget -Env $Environment
    
    if (-not $buildPath) {
        throw "Échec build Unity"
    }
    
    # 4. Construction Docker (optionnel)
    if (-not $SkipDockerBuild) {
        Write-Log "=== CONSTRUCTION DOCKER ===" -Level "INFO"
        $dockerSuccess = New-DockerImage -BuildPath $buildPath
        
        if (-not $dockerSuccess) {
            throw "Échec construction Docker"
        }
    }
    
    # 5. Démarrage services (optionnel)
    if ($RunAfterBuild) {
        Write-Log "=== DÉMARRAGE SERVICES ===" -Level "INFO"
        $servicesSuccess = Start-Services
        
        if (-not $servicesSuccess) {
            Write-Log "⚠️ Services non démarrés automatiquement" -Level "WARNING"
        }
    }
    
    Write-Log "🎉 BUILD TERMINÉ AVEC SUCCÈS! 🎉" -Level "SUCCESS"
    Write-Log "📦 Build Unity: $buildPath" -Level "INFO"
    
    if (-not $SkipDockerBuild) {
        Write-Log "🐳 Image Docker: $DockerImageName:$DockerImageTag" -Level "INFO"
    }
    
    if (-not $RunAfterBuild) {
        Write-Log "💡 Pour démarrer les services: .\build-unity.ps1 -RunAfterBuild" -Level "INFO"
    }
    
} catch {
    Write-Log "❌ ERREUR BUILD: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}
