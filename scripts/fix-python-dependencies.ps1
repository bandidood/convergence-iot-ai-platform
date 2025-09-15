# ================================================================
# SCRIPT DE CORRECTION DES DÉPENDANCES PYTHON
# Station Traffeyere IoT/AI Platform - RNCP 39394
# Correction des conflits de versions numpy/scikit-learn
# ================================================================

param(
    [switch]$TestAfterFix = $true,
    [switch]$BackupOriginal = $true
)

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  CORRECTION DES DÉPENDANCES PYTHON" -ForegroundColor Cyan
Write-Host "  Station Traffeyere IoT/AI Platform - RNCP 39394" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$requirementsFile = "core/edge-ai-engine/requirements.txt"

# Sauvegarde du fichier original
if ($BackupOriginal -and (Test-Path $requirementsFile)) {
    $backupFile = "$requirementsFile.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $requirementsFile $backupFile
    Write-Host "[INFO] Sauvegarde créée: $backupFile" -ForegroundColor Green
}

# Vérification du fichier
if (-not (Test-Path $requirementsFile)) {
    Write-Host "[ERROR] Fichier requirements.txt non trouvé: $requirementsFile" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Analyse du fichier requirements.txt..." -ForegroundColor Yellow

# Lecture du contenu actuel
$content = Get-Content $requirementsFile

# Configuration des versions compatibles
$fixedVersions = @{
    "scikit-learn" = "1.3.2"  # Version stable compatible
    "numpy" = "1.26.4"        # Version stable
    "pandas" = "2.2.2"        # Version actuelle OK
    "scipy" = "1.13.1"        # Version actuelle OK
    "tensorflow" = "2.17.0"   # Version actuelle OK
    "keras" = "3.4.1"         # Version actuelle OK
}

Write-Host "[INFO] Correction des versions incompatibles..." -ForegroundColor Yellow

# Correction du contenu
$newContent = @()
$changesCount = 0

foreach ($line in $content) {
    $newLine = $line
    
    # Détecter et corriger scikit-learn
    if ($line -match "^scikit-learn==([\d\.]+)") {
        $currentVersion = $matches[1]
        $newVersion = $fixedVersions["scikit-learn"]
        
        if ($currentVersion -ne $newVersion) {
            $newLine = $line -replace "scikit-learn==$currentVersion", "scikit-learn==$newVersion"
            Write-Host "  [FIX] scikit-learn: $currentVersion -> $newVersion" -ForegroundColor Green
            $changesCount++
        }
    }
    
    # Détecter et corriger numpy si nécessaire
    elseif ($line -match "^numpy==([\d\.]+)") {
        $currentVersion = $matches[1]
        $newVersion = $fixedVersions["numpy"]
        
        if ($currentVersion -ne $newVersion) {
            $newLine = $line -replace "numpy==$currentVersion", "numpy==$newVersion"
            Write-Host "  [FIX] numpy: $currentVersion -> $newVersion" -ForegroundColor Green
            $changesCount++
        }
    }
    
    $newContent += $newLine
}

# Écriture du fichier corrigé
if ($changesCount -gt 0) {
    $newContent | Out-File -FilePath $requirementsFile -Encoding utf8
    Write-Host "[SUCCESS] $changesCount corrections appliquées dans $requirementsFile" -ForegroundColor Green
} else {
    Write-Host "[INFO] Aucune correction nécessaire" -ForegroundColor Yellow
}

# Affichage des versions finales
Write-Host ""
Write-Host "VERSIONS FINALES:" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan

$finalContent = Get-Content $requirementsFile | Where-Object { $_ -match "^(numpy|scikit-learn|pandas|scipy|tensorflow|keras)==" }
foreach ($line in $finalContent) {
    if ($line -match "^([^=]+)==(.+)") {
        $package = $matches[1]
        $version = $matches[2]
        Write-Host "  $package : $version" -ForegroundColor White
    }
}

Write-Host ""

# Test du build après correction si demandé
if ($TestAfterFix) {
    Write-Host "================================================================" -ForegroundColor Magenta
    Write-Host "TEST DU BUILD APRÈS CORRECTION" -ForegroundColor Magenta
    Write-Host "================================================================" -ForegroundColor Magenta
    Write-Host ""
    
    Write-Host "[INFO] Test du build Docker avec les dépendances corrigées..." -ForegroundColor Yellow
    
    try {
        # Build avec timeout pour éviter un blocage trop long
        $buildCmd = "docker build -t station-traffeyere-test:edge-ai-fixed -f Dockerfile . --progress=plain"
        
        Write-Host "[INFO] Commande: $buildCmd" -ForegroundColor Cyan
        
        $startTime = Get-Date
        $buildJob = Start-Job -ScriptBlock {
            param($cmd)
            Invoke-Expression $cmd
        } -ArgumentList $buildCmd
        
        # Attendre maximum 5 minutes
        $timeout = New-TimeSpan -Minutes 5
        
        if (Wait-Job $buildJob -Timeout $timeout) {
            $buildResult = Receive-Job $buildJob
            $buildTime = (Get-Date) - $startTime
            
            if ($buildJob.State -eq "Completed") {
                Write-Host "[SUCCESS] ✅ Build réussi après correction !" -ForegroundColor Green
                Write-Host "  Temps: $($buildTime.TotalSeconds.ToString('F2'))s" -ForegroundColor Green
                
                # Nettoyage de l'image de test
                docker rmi station-traffeyere-test:edge-ai-fixed --force 2>$null | Out-Null
                
            } else {
                Write-Host "[ERROR] Build échoué même après correction" -ForegroundColor Red
                Write-Host "Sortie du build:" -ForegroundColor Red
                $buildResult | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
            }
        } else {
            Stop-Job $buildJob
            Write-Host "[WARNING] Build timeout après 5 minutes - Arrêt du test" -ForegroundColor Yellow
        }
        
        Remove-Job $buildJob -Force
        
    } catch {
        Write-Host "[ERROR] Erreur durant le test: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "🔧 CORRECTION DES DÉPENDANCES TERMINÉE" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan

# Recommandations
Write-Host ""
Write-Host "📋 RECOMMANDATIONS:" -ForegroundColor Yellow
Write-Host "===================" -ForegroundColor Yellow
Write-Host "• Les versions ont été ajustées pour la compatibilité" -ForegroundColor White
Write-Host "• scikit-learn 1.3.2 est compatible avec numpy 1.26.4" -ForegroundColor White
Write-Host "• Testez le build avec: .\scripts\test-single-docker-build.ps1 -ServiceName 'edge-ai-fixed' -Context '.' -Dockerfile 'Dockerfile'" -ForegroundColor White
Write-Host "• Vérifiez le fonctionnement de l'application après build" -ForegroundColor White
Write-Host ""

exit 0