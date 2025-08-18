# =============================================================================
# SCRIPT DE VÉRIFICATION EXIGENCES SYSTÈME - RNCP 39394 (Windows PowerShell)
# Expert en Systèmes d'Information et Sécurité
# =============================================================================

# Configuration des couleurs
$Host.UI.RawUI.ForegroundColor = 'Green'

Write-Host "🔧 VALIDATION EXIGENCES SYSTÈME RNCP 39394" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor White

# Exigences système selon le plan technique
$MIN_RAM_GB = 32
$MIN_DISK_GB = 500
$MIN_CPU_CORES = 8
$REQUIRED_GPU = "RTX 3060"

# Variables pour le tracking des erreurs
$ERRORS = 0

function Check-Requirement {
    param(
        [string]$Description,
        [string]$CurrentValue,
        [string]$RequiredValue,
        [string]$Status
    )
    
    if ($Status -eq "OK") {
        Write-Host "✅ $Description`: $CurrentValue (requis: $RequiredValue)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ $Description`: $CurrentValue (requis: $RequiredValue)" -ForegroundColor Red
        return $false
    }
}

# 1. Vérification RAM
Write-Host "`n🔍 Vérification RAM..." -ForegroundColor Yellow
try {
    $TotalRAM = Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory
    $TotalRAM_GB = [Math]::Round($TotalRAM / 1GB, 2)
    
    if ($TotalRAM_GB -ge $MIN_RAM_GB) {
        Check-Requirement "RAM Système" "$($TotalRAM_GB)GB" "$($MIN_RAM_GB)GB" "OK"
    } else {
        Check-Requirement "RAM Système" "$($TotalRAM_GB)GB" "$($MIN_RAM_GB)GB" "FAIL"
        $ERRORS++
    }
} catch {
    Write-Host "❌ Impossible de détecter la RAM système" -ForegroundColor Red
    $ERRORS++
}

# 2. Vérification CPU
Write-Host "`n🔍 Vérification CPU..." -ForegroundColor Yellow
try {
    $CPU_CORES = (Get-CimInstance -ClassName Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
    
    if ($CPU_CORES -ge $MIN_CPU_CORES) {
        Check-Requirement "CPU Cores" "$CPU_CORES" "$MIN_CPU_CORES" "OK"
    } else {
        Check-Requirement "CPU Cores" "$CPU_CORES" "$MIN_CPU_CORES" "FAIL"
        $ERRORS++
    }
} catch {
    Write-Host "❌ Impossible de vérifier le CPU" -ForegroundColor Red
    $ERRORS++
}

# 3. Vérification espace disque
Write-Host "`n🔍 Vérification espace disque..." -ForegroundColor Yellow
try {
    $CurrentDrive = (Get-Location).Drive.Name
    $DiskSpace = Get-PSDrive -Name $CurrentDrive | Select-Object -ExpandProperty Free
    $AvailableSpace_GB = [Math]::Round($DiskSpace / 1GB, 2)
    
    if ($AvailableSpace_GB -ge $MIN_DISK_GB) {
        Check-Requirement "Espace Disque" "$($AvailableSpace_GB)GB" "$($MIN_DISK_GB)GB" "OK"
    } else {
        Check-Requirement "Espace Disque" "$($AvailableSpace_GB)GB" "$($MIN_DISK_GB)GB" "FAIL"
        $ERRORS++
    }
} catch {
    Write-Host "❌ Impossible de vérifier l'espace disque" -ForegroundColor Red
    $ERRORS++
}

# 4. Vérification GPU (optionnelle mais recommandée)
Write-Host "`n🔍 Vérification GPU..." -ForegroundColor Yellow
try {
    $GPUInfo = Get-CimInstance -ClassName Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" } | Select-Object -First 1 -ExpandProperty Name
    
    if ($GPUInfo) {
        if ($GPUInfo -like "*RTX 3060*" -or $GPUInfo -like "*RTX 30*" -or $GPUInfo -like "*RTX 40*") {
            Check-Requirement "GPU Compatible" "$GPUInfo" "$REQUIRED_GPU" "OK"
        } else {
            Write-Host "⚠️  GPU Détecté: $GPUInfo (recommandé: $REQUIRED_GPU)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Aucun GPU NVIDIA détecté (optionnel pour développement)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Impossible de détecter le GPU" -ForegroundColor Yellow
}

# 5. Vérification Docker
Write-Host "`n🔍 Vérification Docker..." -ForegroundColor Yellow
try {
    $DockerVersion = docker --version 2>$null
    if ($DockerVersion) {
        Write-Host "✅ Docker installé: $DockerVersion" -ForegroundColor Green
        
        # Vérification que Docker fonctionne
        $DockerInfo = docker info 2>$null
        if ($DockerInfo) {
            Write-Host "✅ Docker daemon opérationnel" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker daemon non accessible" -ForegroundColor Red
            $ERRORS++
        }
    } else {
        Write-Host "❌ Docker non installé" -ForegroundColor Red
        $ERRORS++
    }
} catch {
    Write-Host "❌ Docker non trouvé" -ForegroundColor Red
    $ERRORS++
}

# 6. Vérification Docker Compose
Write-Host "`n🔍 Vérification Docker Compose..." -ForegroundColor Yellow
try {
    $ComposeVersion = docker compose version 2>$null
    if ($ComposeVersion) {
        Write-Host "✅ Docker Compose installé: $ComposeVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker Compose non installé" -ForegroundColor Red
        $ERRORS++
    }
} catch {
    Write-Host "❌ Docker Compose non trouvé" -ForegroundColor Red
    $ERRORS++
}

# 7. Vérification outils de développement
Write-Host "`n🔍 Vérification outils développement..." -ForegroundColor Yellow

# Python
try {
    $PythonVersion = python --version 2>$null
    if ($PythonVersion) {
        Write-Host "✅ Python installé: $PythonVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Python non trouvé" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Python non détecté" -ForegroundColor Yellow
}

# Node.js
try {
    $NodeVersion = node --version 2>$null
    if ($NodeVersion) {
        Write-Host "✅ Node.js installé: $NodeVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Node.js non trouvé" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Node.js non détecté" -ForegroundColor Yellow
}

# Git
try {
    $GitVersion = git --version 2>$null
    if ($GitVersion) {
        Write-Host "✅ Git installé: $GitVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Git non trouvé" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Git non détecté" -ForegroundColor Yellow
}

# Résumé final
Write-Host "`n==================================================" -ForegroundColor White
if ($ERRORS -eq 0) {
    Write-Host "🎉 SYSTÈME COMPATIBLE - TOUTES EXIGENCES SATISFAITES" -ForegroundColor Green
    Write-Host "✅ Prêt pour le déploiement de l'infrastructure sécurisée" -ForegroundColor Green
    
    # Affichage des prochaines étapes
    Write-Host "`n📋 PROCHAINES ÉTAPES SEMAINE 1:" -ForegroundColor Cyan
    Write-Host "1. Valider votre infrastructure Docker existante" -ForegroundColor White
    Write-Host "2. Examiner le docker-compose.yml actuel" -ForegroundColor White
    Write-Host "3. Commencer la creation du generateur IoT securise" -ForegroundColor White
    Write-Host "4. Configurer l'environnement de developpement" -ForegroundColor White
    
    exit 0
} else {
    Write-Host "⚠️  $ERRORS EXIGENCE(S) NON SATISFAITE(S)" -ForegroundColor Red
    Write-Host "❌ Veuillez corriger les problèmes avant de continuer" -ForegroundColor Red
    exit 1
}
