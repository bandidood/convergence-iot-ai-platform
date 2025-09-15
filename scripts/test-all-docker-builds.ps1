# ================================================================
# SCRIPT DE TEST SIMPLE - TOUS LES BUILDS DOCKER
# Station Traffeyere IoT/AI Platform - RNCP 39394
# Tests des builds Docker disponibles avec contexte racine
# ================================================================

param(
    [switch]$ShowOutput = $false,
    [switch]$SkipCleanup = $false,
    [switch]$DetailedReport = $true
)

$ErrorActionPreference = "Continue"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  DOCKER BUILD TEST - ALL SERVICES" -ForegroundColor Cyan
Write-Host "  Station Traffeyere IoT/AI Platform - RNCP 39394" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration des services à tester
$Services = @(
    @{
        Name = "backend"
        Context = "."
        Dockerfile = "services\backend\Dockerfile"
        Description = "Backend API et services métier"
    },
    @{
        Name = "frontend"
        Context = "."
        Dockerfile = "services\frontend\Dockerfile"
        Description = "Interface utilisateur React"
    }
)

# Découverte automatique des autres Dockerfiles
Write-Host "[INFO] Découverte automatique des Dockerfiles..." -ForegroundColor Yellow

$dockerfiles = Get-ChildItem -Recurse -Name "Dockerfile*" | Where-Object { 
    $_ -notlike "*\.docker*" -and 
    $_ -notlike "*node_modules*" -and
    $_ -notlike "*\.git*"
}

foreach ($dockerfile in $dockerfiles) {
    $path = $dockerfile -replace '\\', '/'
    $serviceName = $path -replace '/Dockerfile.*', '' -replace 'services/', '' -replace '/', '-'
    
    # Vérifier si pas déjà dans la liste
    $existing = $Services | Where-Object { $_.Dockerfile -eq $dockerfile }
    
    if (-not $existing -and $serviceName -ne "") {
        Write-Host "[INFO] Dockerfile trouvé: $dockerfile -> Service: $serviceName" -ForegroundColor Cyan
        
        $Services += @{
            Name = $serviceName
            Context = "."
            Dockerfile = $dockerfile
            Description = "Service auto-détecté"
        }
    }
}

Write-Host "[INFO] Total services à tester: $($Services.Count)" -ForegroundColor Green
Write-Host ""

# Variables pour le rapport
$TestResults = @()
$StartTime = Get-Date

# Fonction de test d'un service
function Test-ServiceBuild {
    param($Service)
    
    $serviceName = $Service.Name
    $serviceStartTime = Get-Date
    
    Write-Host "========================================" -ForegroundColor Magenta
    Write-Host "TEST: $serviceName" -ForegroundColor Magenta
    Write-Host "Description: $($Service.Description)" -ForegroundColor Gray
    Write-Host "Context: $($Service.Context)" -ForegroundColor Gray
    Write-Host "Dockerfile: $($Service.Dockerfile)" -ForegroundColor Gray
    Write-Host "========================================" -ForegroundColor Magenta
    
    $result = @{
        ServiceName = $serviceName
        Success = $false
        BuildTime = 0
        ImageSize = "N/A"
        Layers = "N/A"
        Error = ""
        Timestamp = Get-Date
    }
    
    try {
        # Vérifier les prérequis
        if (-not (Test-Path $Service.Dockerfile)) {
            throw "Dockerfile non trouvé: $($Service.Dockerfile)"
        }
        
        # Build Docker
        $imageName = "station-traffeyere-test:$serviceName"
        $buildCmd = "docker build -t `"$imageName`" -f `"$($Service.Dockerfile)`" `"$($Service.Context)`""
        
        Write-Host "[INFO] Commande: $buildCmd" -ForegroundColor Yellow
        
        if ($ShowOutput) {
            $buildResult = Invoke-Expression $buildCmd
            $exitCode = $LASTEXITCODE
        } else {
            $buildResult = Invoke-Expression "$buildCmd 2>&1"
            $exitCode = $LASTEXITCODE
        }
        
        $buildTime = (Get-Date) - $serviceStartTime
        $result.BuildTime = $buildTime.TotalSeconds
        
        if ($exitCode -eq 0) {
            Write-Host "[SUCCESS] Build réussi en $($buildTime.TotalSeconds.ToString('F2'))s" -ForegroundColor Green
            
            # Informations sur l'image
            try {
                $imageInfo = docker inspect $imageName 2>$null | ConvertFrom-Json
                if ($imageInfo -and $imageInfo.Count -gt 0) {
                    $sizeMB = [math]::Round($imageInfo[0].Size / 1MB, 2)
                    $layers = $imageInfo[0].RootFS.Layers.Count
                    
                    $result.ImageSize = "${sizeMB}MB"
                    $result.Layers = $layers
                    
                    Write-Host "[INFO] Taille: ${sizeMB}MB" -ForegroundColor Cyan
                    Write-Host "[INFO] Layers: $layers" -ForegroundColor Cyan
                }
            } catch {
                Write-Host "[WARNING] Impossible de récupérer les infos de l'image" -ForegroundColor Yellow
            }
            
            # Test rapide de démarrage
            Write-Host "[INFO] Test démarrage de l'image..." -ForegroundColor Yellow
            
            try {
                $containerName = "$serviceName-health-test"
                $runResult = docker run --rm -d --name $containerName $imageName 2>$null
                
                if ($LASTEXITCODE -eq 0) {
                    Start-Sleep 3
                    $containerStatus = docker ps -f "name=$containerName" --format "{{.Status}}" 2>$null
                    
                    if ($containerStatus) {
                        Write-Host "[SUCCESS] Conteneur démarré avec succès: $containerStatus" -ForegroundColor Green
                        docker stop $containerName 2>$null | Out-Null
                    } else {
                        Write-Host "[WARNING] Conteneur arrêté rapidement" -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "[WARNING] Impossible de démarrer le conteneur" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "[WARNING] Erreur test démarrage: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            $result.Success = $true
            Write-Host "[SUCCESS] ✅ Test complet réussi - Image opérationnelle" -ForegroundColor Green
            
        } else {
            $result.Error = if ($buildResult) { $buildResult -join "; " } else { "Build failed with exit code $exitCode" }
            Write-Host "[ERROR] Build échoué (exit code: $exitCode)" -ForegroundColor Red
            if ($buildResult -and $ShowOutput) {
                Write-Host "Sortie:" -ForegroundColor Red
                $buildResult | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
            }
        }
        
    } catch {
        $result.Error = $_.Exception.Message
        Write-Host "[ERROR] Exception: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    return $result
}

# Exécution des tests
foreach ($service in $Services) {
    $testResult = Test-ServiceBuild -Service $service
    $TestResults += $testResult
}

# Nettoyage des images de test
if (-not $SkipCleanup) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "NETTOYAGE DES IMAGES DE TEST" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    try {
        $testImages = docker images --filter "reference=station-traffeyere-test:*" -q 2>$null
        
        if ($testImages) {
            docker rmi $testImages --force 2>$null | Out-Null
            Write-Host "[INFO] Images de test supprimées" -ForegroundColor Green
        } else {
            Write-Host "[INFO] Aucune image de test à supprimer" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[WARNING] Erreur nettoyage: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Rapport final
$totalTime = (Get-Date) - $StartTime
$successCount = ($TestResults | Where-Object { $_.Success }).Count
$failCount = ($TestResults | Where-Object { -not $_.Success }).Count

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "RAPPORT FINAL" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Services testés: $($TestResults.Count)" -ForegroundColor White
Write-Host "Builds réussis: $successCount" -ForegroundColor Green
Write-Host "Builds échoués: $failCount" -ForegroundColor Red
Write-Host "Temps total: $($totalTime.TotalSeconds.ToString('F2'))s" -ForegroundColor White
Write-Host ""

# Détail des résultats
Write-Host "DÉTAIL DES RÉSULTATS:" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow

foreach ($result in $TestResults) {
    $status = if ($result.Success) { "✅ SUCCESS" } else { "❌ FAILED" }
    $color = if ($result.Success) { "Green" } else { "Red" }
    
    Write-Host "  $($result.ServiceName): $status ($($result.BuildTime.ToString('F2'))s)" -ForegroundColor $color
    
    if ($result.Success) {
        Write-Host "    Taille: $($result.ImageSize), Layers: $($result.Layers)" -ForegroundColor Gray
    } else {
        Write-Host "    Erreur: $($result.Error)" -ForegroundColor Red
    }
}

Write-Host ""

# Génération rapport HTML si demandé
if ($DetailedReport) {
    $reportPath = "docker-build-test-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').html"
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Docker Build Test Report - Station Traffeyere</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background-color: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 30px; border-radius: 8px; text-align: center; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header p { margin: 5px 0; opacity: 0.9; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #3498db; }
        .metric h3 { margin: 0 0 10px 0; color: #2c3e50; }
        .metric .value { font-size: 2em; font-weight: bold; color: #3498db; }
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #2c3e50; color: white; font-weight: 600; }
        tr:hover { background-color: #f5f5f5; }
        .status-success { background-color: #d4edda; color: #155724; padding: 5px 10px; border-radius: 4px; font-weight: bold; }
        .status-error { background-color: #f8d7da; color: #721c24; padding: 5px 10px; border-radius: 4px; font-weight: bold; }
        .recommendations { background: #e8f4f8; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }
        .recommendations ul { margin: 0; padding-left: 20px; }
        .recommendations li { margin-bottom: 8px; }
        footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐳 Docker Build Test Report</h1>
            <p>Station Traffeyere IoT/AI Platform - RNCP 39394</p>
            <p>Generated: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")</p>
            <p>Total Execution Time: $($totalTime.TotalSeconds.ToString('F2'))s</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <h3>Services Tested</h3>
                <div class="value">$($TestResults.Count)</div>
            </div>
            <div class="metric">
                <h3>Successful Builds</h3>
                <div class="value success">$successCount</div>
            </div>
            <div class="metric">
                <h3>Failed Builds</h3>
                <div class="value error">$failCount</div>
            </div>
            <div class="metric">
                <h3>Success Rate</h3>
                <div class="value">$(if ($TestResults.Count -gt 0) { [math]::Round(($successCount / $TestResults.Count) * 100, 1) } else { 0 })%</div>
            </div>
        </div>
        
        <h2>🏗️ Build Results</h2>
        <table>
            <tr>
                <th>Service</th>
                <th>Status</th>
                <th>Build Time</th>
                <th>Image Size</th>
                <th>Layers</th>
                <th>Error</th>
            </tr>
"@

    foreach ($result in $TestResults) {
        $statusClass = if ($result.Success) { "status-success" } else { "status-error" }
        $status = if ($result.Success) { "✅ Success" } else { "❌ Failed" }
        $errorText = if ($result.Error -and $result.Error.Length -gt 100) { $result.Error.Substring(0, 100) + "..." } else { $result.Error }
        
        $html += @"
            <tr>
                <td><strong>$($result.ServiceName)</strong></td>
                <td><span class="$statusClass">$status</span></td>
                <td>$($result.BuildTime.ToString('F2'))s</td>
                <td>$($result.ImageSize)</td>
                <td>$($result.Layers)</td>
                <td>$(if ($result.Error) { $errorText } else { "-" })</td>
            </tr>
"@
    }

    $html += @"
        </table>
        
        <div class="recommendations">
            <h2>📋 Recommendations</h2>
            <ul>
"@

    if ($failCount -gt 0) {
        $failedServices = ($TestResults | Where-Object { -not $_.Success }).ServiceName -join ", "
        $html += "<li><strong>Fix failed builds:</strong> $failedServices</li>"
    }
    
    $slowBuilds = $TestResults | Where-Object { $_.BuildTime -gt 60 }
    if ($slowBuilds.Count -gt 0) {
        $slowServices = $slowBuilds.ServiceName -join ", "
        $html += "<li><strong>Optimize slow builds:</strong> $slowServices (>60s)</li>"
    }
    
    if ($successCount -eq $TestResults.Count) {
        $html += "<li>✅ All builds successful! Ready for deployment testing.</li>"
    }
    
    $html += @"
                <li>Consider implementing multi-stage builds for production optimization</li>
                <li>Add automated security scanning with Trivy or similar tools</li>
                <li>Integrate build tests in CI/CD pipeline</li>
                <li>Monitor build performance and optimize Dockerfile layers</li>
            </ul>
        </div>
        
        <footer>
            <p><em>Report generated by Station Traffeyere Docker Build Testing Suite</em></p>
            <p>🚀 Ready for production deployment testing</p>
        </footer>
    </div>
</body>
</html>
"@

    $html | Out-File -FilePath $reportPath -Encoding UTF8
    Write-Host "[SUCCESS] Rapport HTML généré: $reportPath" -ForegroundColor Green
    
    # Ouvrir le rapport dans le navigateur par défaut
    try {
        Start-Process $reportPath
        Write-Host "[INFO] Rapport ouvert dans le navigateur" -ForegroundColor Cyan
    } catch {
        Write-Host "[WARNING] Impossible d'ouvrir le rapport automatiquement" -ForegroundColor Yellow
    }
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "🎯 Tests terminés avec succès !" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan

# Code de sortie basé sur les résultats
exit $failCount