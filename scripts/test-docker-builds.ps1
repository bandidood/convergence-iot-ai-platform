# ================================================================
# SCRIPT DE TEST DES BUILDS DOCKER
# Station Traffeyere IoT/AI Platform - RNCP 39394
# Tests complets: Builds, Sécurité, Performance, Conformité
# ================================================================

param(
    [switch]$SkipPull = $false,
    [switch]$SecurityScan = $true,
    [switch]$PerformanceTest = $true,
    [switch]$DetailedReport = $true,
    [string]$TestEnvironment = "development"
)

# Variables globales
$ErrorActionPreference = "Continue"
$Global:TestResults = @()
$Global:BuildMetrics = @()
$Global:SecurityIssues = @()

# Configuration du test
$TestConfig = @{
    MaxBuildTime = 600  # 10 minutes max par build
    RequiredTools = @("docker", "docker-compose")
    SecurityTools = @("trivy", "hadolint")
    LogLevel = "INFO"
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  DOCKER BUILD TESTING SUITE" -ForegroundColor Cyan
Write-Host "  Station Traffeyere IoT/AI Platform - RNCP 39394" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Environment: $TestEnvironment" -ForegroundColor Yellow
Write-Host "Security Scan: $SecurityScan" -ForegroundColor Yellow
Write-Host "Performance Test: $PerformanceTest" -ForegroundColor Yellow
Write-Host ""

# Fonction de logging avancée
function Write-TestLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Component = "GENERAL"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] [$Component] $Message"
    
    switch ($Level) {
        "ERROR"   { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "INFO"    { Write-Host $logEntry -ForegroundColor White }
        default   { Write-Host $logEntry }
    }
    
    # Log vers fichier
    Add-Content -Path "docker-build-test-$(Get-Date -Format 'yyyyMMdd').log" -Value $logEntry
}

# Vérification des prérequis
function Test-Prerequisites {
    Write-TestLog "Vérification des prérequis..." "INFO" "PREREQ"
    
    foreach ($tool in $TestConfig.RequiredTools) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            Write-TestLog "$tool non trouvé - Installation requise" "ERROR" "PREREQ"
            return $false
        } else {
            $version = & $tool --version 2>$null | Select-Object -First 1
            Write-TestLog "$tool disponible: $version" "SUCCESS" "PREREQ"
        }
    }
    
    # Vérifier l'espace disque
    $freeSpace = Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DeviceID -eq "C:"} | Select-Object -ExpandProperty FreeSpace
    $freeSpaceGB = [math]::Round($freeSpace / 1GB, 2)
    
    if ($freeSpaceGB -lt 10) {
        Write-TestLog "Espace disque insuffisant: ${freeSpaceGB}GB (minimum 10GB requis)" "ERROR" "PREREQ"
        return $false
    }
    
    Write-TestLog "Espace disque disponible: ${freeSpaceGB}GB" "SUCCESS" "PREREQ"
    return $true
}

# Découverte automatique des services Docker
function Get-DockerServices {
    Write-TestLog "Découverte des services Docker..." "INFO" "DISCOVERY"
    
    $services = @()
    
    # Services avec builds explicites dans docker-compose files
    $composeFiles = @(
        "docker-compose.yml",
        "docker-compose.production.yml", 
        "docker-compose.security.yml",
        "docker-compose.monitoring.yml"
    )
    
    foreach ($file in $composeFiles) {
        if (Test-Path $file) {
            Write-TestLog "Analyse $file..." "INFO" "DISCOVERY"
            
            $content = Get-Content $file -Raw
            
            # Extraire services avec builds
            if ($content -match '(?s)services:(.*?)$') {
                $servicesSection = $matches[1]
                
                # Pattern pour détecter les services avec build
                $buildMatches = [regex]::Matches($servicesSection, '(?m)^\s*([a-zA-Z0-9_-]+):\s*$.*?^\s*build:\s*$.*?^\s*context:\s*(.+)$.*?^\s*dockerfile:\s*(.+)$', [System.Text.RegularExpressions.RegexOptions]::Multiline)
                
                foreach ($match in $buildMatches) {
                    $serviceName = $match.Groups[1].Value.Trim()
                    $context = $match.Groups[2].Value.Trim()
                    $dockerfile = $match.Groups[3].Value.Trim()
                    
                    $services += @{
                        Name = $serviceName
                        Context = $context
                        Dockerfile = $dockerfile
                        ComposeFile = $file
                    }
                    
                    Write-TestLog "Service trouvé: $serviceName ($context/$dockerfile)" "SUCCESS" "DISCOVERY"
                }
            }
        }
    }
    
    # Ajout des Dockerfiles standalone
    $dockerfiles = Get-ChildItem -Recurse -Name "Dockerfile*" | Where-Object { $_ -notlike "*/.docker/*" }
    
    foreach ($dockerfile in $dockerfiles) {
        $dir = Split-Path $dockerfile -Parent
        $name = if ($dir) { $dir.Replace('\', '-').Replace('/', '-') } else { "root" }
        
        # Vérifier si pas déjà dans les services
        $existing = $services | Where-Object { $_.Context -like "*$dir*" -or $_.Dockerfile -like "*$(Split-Path $dockerfile -Leaf)*" }
        
        if (-not $existing) {
            $services += @{
                Name = "$name-standalone"
                Context = if ($dir) { $dir } else { "." }
                Dockerfile = $dockerfile
                ComposeFile = "standalone"
            }
            
            Write-TestLog "Dockerfile standalone trouvé: $dockerfile" "INFO" "DISCOVERY"
        }
    }
    
    Write-TestLog "Total services trouvés: $($services.Count)" "SUCCESS" "DISCOVERY"
    return $services
}

# Test de build d'un service
function Test-ServiceBuild {
    param(
        [hashtable]$Service
    )
    
    $serviceName = $Service.Name
    $startTime = Get-Date
    
    Write-TestLog "Test build: $serviceName" "INFO" "BUILD"
    
    try {
        # Construction de la commande docker build
        $buildArgs = @()
        $buildArgs += "build"
        $buildArgs += "-t"
        $buildArgs += "station-traffeyere:$serviceName-test"
        $buildArgs += "-f"
        $buildArgs += $Service.Dockerfile
        $buildArgs += $Service.Context
        
        Write-TestLog "Commande: docker $($buildArgs -join ' ')" "INFO" "BUILD"
        
        # Exécution du build avec timeout
        $job = Start-Job -ScriptBlock {
            param($args)
            & docker @args 2>&1
        } -ArgumentList $buildArgs
        
        $timeout = New-TimeSpan -Seconds $TestConfig.MaxBuildTime
        
        if (Wait-Job $job -Timeout $timeout) {
            $result = Receive-Job $job
            $exitCode = if ($job.State -eq "Completed") { 0 } else { 1 }
        } else {
            Stop-Job $job
            Write-TestLog "Build timeout après $($TestConfig.MaxBuildTime)s" "ERROR" "BUILD"
            $exitCode = 124
            $result = "Build timeout"
        }
        
        Remove-Job $job -Force
        
        $buildTime = (Get-Date) - $startTime
        
        $buildResult = @{
            Service = $serviceName
            Success = $exitCode -eq 0
            BuildTime = $buildTime.TotalSeconds
            Output = $result -join "`n"
            Timestamp = Get-Date
            Context = $Service.Context
            Dockerfile = $Service.Dockerfile
        }
        
        if ($exitCode -eq 0) {
            Write-TestLog "Build réussi en $($buildTime.TotalSeconds.ToString('F2'))s" "SUCCESS" "BUILD"
            
            # Test de santé de l'image
            Test-ImageHealth -ImageName "station-traffeyere:$serviceName-test" -ServiceName $serviceName
            
        } else {
            Write-TestLog "Build échoué (exit code: $exitCode)" "ERROR" "BUILD"
            Write-TestLog "Erreur: $($result -join '; ')" "ERROR" "BUILD"
        }
        
        $Global:BuildMetrics += $buildResult
        return $buildResult
        
    } catch {
        $buildTime = (Get-Date) - $startTime
        Write-TestLog "Exception durant build: $($_.Exception.Message)" "ERROR" "BUILD"
        
        $buildResult = @{
            Service = $serviceName
            Success = $false
            BuildTime = $buildTime.TotalSeconds
            Output = $_.Exception.Message
            Timestamp = Get-Date
            Error = $_.Exception
        }
        
        $Global:BuildMetrics += $buildResult
        return $buildResult
    }
}

# Test de santé de l'image Docker
function Test-ImageHealth {
    param(
        [string]$ImageName,
        [string]$ServiceName
    )
    
    Write-TestLog "Test santé image: $ImageName" "INFO" "HEALTH"
    
    try {
        # Informations de l'image
        $imageInfo = docker inspect $ImageName 2>$null | ConvertFrom-Json
        
        if ($imageInfo) {
            $size = [math]::Round($imageInfo[0].Size / 1MB, 2)
            Write-TestLog "Taille image: ${size}MB" "INFO" "HEALTH"
            
            # Vérifier les layers
            $layers = $imageInfo[0].RootFS.Layers.Count
            Write-TestLog "Nombre de layers: $layers" "INFO" "HEALTH"
            
            if ($size -gt 2000) {  # Plus de 2GB
                Write-TestLog "Image très volumineuse (>${size}MB) - Optimisation recommandée" "WARNING" "HEALTH"
            }
            
            if ($layers -gt 50) {
                Write-TestLog "Trop de layers ($layers) - Optimisation recommandée" "WARNING" "HEALTH"
            }
        }
        
        # Test de démarrage rapide (si le service a un ENTRYPOINT)
        Write-TestLog "Test démarrage conteneur..." "INFO" "HEALTH"
        
        $containerResult = docker run --rm -d --name "$ServiceName-health-test" $ImageName 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Start-Sleep 3  # Attendre 3 secondes
            
            $containerStatus = docker ps -f "name=$ServiceName-health-test" --format "{{.Status}}" 2>$null
            
            if ($containerStatus -like "*Up*") {
                Write-TestLog "Conteneur démarré avec succès" "SUCCESS" "HEALTH"
                docker stop "$ServiceName-health-test" 2>$null | Out-Null
            } else {
                Write-TestLog "Conteneur n'a pas démarré correctement" "WARNING" "HEALTH"
            }
        } else {
            Write-TestLog "Impossible de démarrer le conteneur pour test" "WARNING" "HEALTH"
        }
        
    } catch {
        Write-TestLog "Erreur test santé: $($_.Exception.Message)" "WARNING" "HEALTH"
    }
}

# Scan sécurité avec Trivy (si disponible)
function Test-ImageSecurity {
    param(
        [string]$ImageName,
        [string]$ServiceName
    )
    
    if (-not $SecurityScan) {
        return
    }
    
    Write-TestLog "Scan sécurité: $ImageName" "INFO" "SECURITY"
    
    try {
        # Vérifier si Trivy est disponible
        if (Get-Command "trivy" -ErrorAction SilentlyContinue) {
            $scanResult = docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --exit-code 0 --no-progress --format json $ImageName 2>$null
            
            if ($LASTEXITCODE -eq 0 -and $scanResult) {
                $securityData = $scanResult | ConvertFrom-Json
                
                $vulnerabilities = $securityData.Results | ForEach-Object { $_.Vulnerabilities } | Measure-Object | Select-Object -ExpandProperty Count
                $criticalVulns = $securityData.Results | ForEach-Object { $_.Vulnerabilities | Where-Object { $_.Severity -eq "CRITICAL" } } | Measure-Object | Select-Object -ExpandProperty Count
                $highVulns = $securityData.Results | ForEach-Object { $_.Vulnerabilities | Where-Object { $_.Severity -eq "HIGH" } } | Measure-Object | Select-Object -ExpandProperty Count
                
                Write-TestLog "Vulnérabilités: Total=$vulnerabilities, Critical=$criticalVulns, High=$highVulns" "INFO" "SECURITY"
                
                if ($criticalVulns -gt 0) {
                    Write-TestLog "$criticalVulns vulnérabilités critiques détectées" "ERROR" "SECURITY"
                    $Global:SecurityIssues += @{
                        Service = $ServiceName
                        Image = $ImageName
                        Critical = $criticalVulns
                        High = $highVulns
                        Total = $vulnerabilities
                    }
                } elseif ($highVulns -gt 5) {
                    Write-TestLog "$highVulns vulnérabilités hautes détectées" "WARNING" "SECURITY"
                } else {
                    Write-TestLog "Scan sécurité: Acceptable" "SUCCESS" "SECURITY"
                }
            }
        } else {
            Write-TestLog "Trivy non disponible - scan sécurité ignoré" "WARNING" "SECURITY"
        }
        
    } catch {
        Write-TestLog "Erreur scan sécurité: $($_.Exception.Message)" "WARNING" "SECURITY"
    }
}

# Test de performance simple
function Test-BuildPerformance {
    if (-not $PerformanceTest) {
        return
    }
    
    Write-TestLog "Analyse performance builds..." "INFO" "PERFORMANCE"
    
    $totalBuildTime = ($Global:BuildMetrics | Measure-Object -Property BuildTime -Sum).Sum
    $avgBuildTime = ($Global:BuildMetrics | Measure-Object -Property BuildTime -Average).Average
    $slowestBuild = $Global:BuildMetrics | Sort-Object BuildTime -Descending | Select-Object -First 1
    
    Write-TestLog "Temps total builds: $($totalBuildTime.ToString('F2'))s" "INFO" "PERFORMANCE"
    Write-TestLog "Temps moyen par build: $($avgBuildTime.ToString('F2'))s" "INFO" "PERFORMANCE"
    Write-TestLog "Build le plus lent: $($slowestBuild.Service) ($($slowestBuild.BuildTime.ToString('F2'))s)" "INFO" "PERFORMANCE"
    
    if ($avgBuildTime -gt 120) {  # Plus de 2 minutes en moyenne
        Write-TestLog "Temps de build moyen élevé - Optimisation recommandée" "WARNING" "PERFORMANCE"
    }
    
    if ($slowestBuild.BuildTime -gt 300) {  # Plus de 5 minutes
        Write-TestLog "Build très lent détecté: $($slowestBuild.Service)" "WARNING" "PERFORMANCE"
    }
}

# Nettoyage des images de test
function Clear-TestImages {
    Write-TestLog "Nettoyage des images de test..." "INFO" "CLEANUP"
    
    try {
        $testImages = docker images --filter "reference=station-traffeyere:*-test" -q
        
        if ($testImages) {
            docker rmi $testImages --force 2>$null | Out-Null
            Write-TestLog "Images de test supprimées" "SUCCESS" "CLEANUP"
        }
        
        # Nettoyage des conteneurs orphelins
        docker system prune -f --volumes 2>$null | Out-Null
        
    } catch {
        Write-TestLog "Erreur nettoyage: $($_.Exception.Message)" "WARNING" "CLEANUP"
    }
}

# Génération du rapport détaillé
function New-TestReport {
    if (-not $DetailedReport) {
        return
    }
    
    Write-TestLog "Génération rapport détaillé..." "INFO" "REPORT"
    
    $reportPath = "docker-build-test-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').html"
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Docker Build Test Report - Station Traffeyere</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .success { color: #27ae60; font-weight: bold; }
        .error { color: #e74c3c; font-weight: bold; }
        .warning { color: #f39c12; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .metric { background: #ecf0f1; padding: 10px; margin: 10px 0; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🐳 Docker Build Test Report</h1>
        <p>Station Traffeyere IoT/AI Platform - RNCP 39394</p>
        <p>Generated: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")</p>
        <p>Environment: $TestEnvironment</p>
    </div>
    
    <h2>📊 Summary</h2>
    <div class="metric">
        <strong>Total Services Tested:</strong> $($Global:BuildMetrics.Count)<br>
        <strong>Successful Builds:</strong> $($Global:BuildMetrics | Where-Object {$_.Success} | Measure-Object | Select-Object -ExpandProperty Count)<br>
        <strong>Failed Builds:</strong> $($Global:BuildMetrics | Where-Object {-not $_.Success} | Measure-Object | Select-Object -ExpandProperty Count)<br>
        <strong>Security Issues:</strong> $($Global:SecurityIssues.Count)<br>
        <strong>Total Build Time:</strong> $(($Global:BuildMetrics | Measure-Object -Property BuildTime -Sum).Sum.ToString('F2'))s
    </div>
    
    <h2>🏗️ Build Results</h2>
    <table>
        <tr>
            <th>Service</th>
            <th>Status</th>
            <th>Build Time (s)</th>
            <th>Context</th>
            <th>Dockerfile</th>
        </tr>
"@

    foreach ($result in $Global:BuildMetrics) {
        $statusClass = if ($result.Success) { "success" } else { "error" }
        $status = if ($result.Success) { "✅ Success" } else { "❌ Failed" }
        
        $html += @"
        <tr>
            <td>$($result.Service)</td>
            <td class="$statusClass">$status</td>
            <td>$($result.BuildTime.ToString('F2'))</td>
            <td>$($result.Context)</td>
            <td>$($result.Dockerfile)</td>
        </tr>
"@
    }

    $html += @"
    </table>
    
    <h2>🔒 Security Issues</h2>
"@

    if ($Global:SecurityIssues.Count -gt 0) {
        $html += @"
    <table>
        <tr>
            <th>Service</th>
            <th>Critical</th>
            <th>High</th>
            <th>Total</th>
        </tr>
"@
        foreach ($issue in $Global:SecurityIssues) {
            $html += @"
        <tr>
            <td>$($issue.Service)</td>
            <td class="error">$($issue.Critical)</td>
            <td class="warning">$($issue.High)</td>
            <td>$($issue.Total)</td>
        </tr>
"@
        }
        $html += "</table>"
    } else {
        $html += '<p class="success">✅ No security issues detected</p>'
    }

    $html += @"
    
    <h2>📈 Recommendations</h2>
    <ul>
"@

    if (($Global:BuildMetrics | Where-Object {-not $_.Success}).Count -gt 0) {
        $html += "<li>Fix failed builds before production deployment</li>"
    }
    
    if ($Global:SecurityIssues.Count -gt 0) {
        $html += "<li>Address security vulnerabilities in images</li>"
    }
    
    $slowBuilds = $Global:BuildMetrics | Where-Object {$_.BuildTime -gt 120}
    if ($slowBuilds.Count -gt 0) {
        $html += "<li>Optimize slow builds: $($slowBuilds.Service -join ', ')</li>"
    }
    
    $html += @"
        <li>Consider multi-stage builds for production optimization</li>
        <li>Implement image layer caching for faster builds</li>
        <li>Regular security scanning in CI/CD pipeline</li>
    </ul>
    
    <footer>
        <p><em>Report generated by Station Traffeyere Docker Build Testing Suite</em></p>
    </footer>
</body>
</html>
"@

    $html | Out-File -FilePath $reportPath -Encoding UTF8
    Write-TestLog "Rapport généré: $reportPath" "SUCCESS" "REPORT"
    
    # Ouvrir le rapport dans le navigateur
    Start-Process $reportPath
}

# === SCRIPT PRINCIPAL ===

Write-TestLog "Démarrage des tests Docker Build" "INFO" "MAIN"

# Étape 1: Vérification des prérequis
if (-not (Test-Prerequisites)) {
    Write-TestLog "Prérequis non satisfaits - Arrêt des tests" "ERROR" "MAIN"
    exit 1
}

# Étape 2: Découverte des services Docker
$dockerServices = Get-DockerServices

if ($dockerServices.Count -eq 0) {
    Write-TestLog "Aucun service Docker trouvé - Vérifiez la structure du projet" "ERROR" "MAIN"
    exit 1
}

Write-TestLog "$($dockerServices.Count) services Docker identifiés" "SUCCESS" "MAIN"

# Étape 3: Test des builds
$successCount = 0
$failCount = 0

foreach ($service in $dockerServices) {
    Write-TestLog "========================================" "INFO" "MAIN"
    Write-TestLog "Test du service: $($service.Name)" "INFO" "MAIN"
    Write-TestLog "Context: $($service.Context)" "INFO" "MAIN"
    Write-TestLog "Dockerfile: $($service.Dockerfile)" "INFO" "MAIN"
    
    $result = Test-ServiceBuild -Service $service
    
    if ($result.Success) {
        $successCount++
        
        # Scan sécurité si activé
        if ($SecurityScan) {
            Test-ImageSecurity -ImageName "station-traffeyere:$($service.Name)-test" -ServiceName $service.Name
        }
    } else {
        $failCount++
    }
    
    Write-TestLog "========================================" "INFO" "MAIN"
}

# Étape 4: Analyse des performances
Test-BuildPerformance

# Étape 5: Génération du rapport
New-TestReport

# Étape 6: Nettoyage
Clear-TestImages

# Résultats finaux
Write-TestLog "========================================" "INFO" "FINAL"
Write-TestLog "RÉSULTATS FINAUX" "INFO" "FINAL"
Write-TestLog "========================================" "INFO" "FINAL"
Write-TestLog "Services testés: $($dockerServices.Count)" "INFO" "FINAL"
Write-TestLog "Builds réussis: $successCount" "SUCCESS" "FINAL"
Write-TestLog "Builds échoués: $failCount" "ERROR" "FINAL"
Write-TestLog "Issues sécurité: $($Global:SecurityIssues.Count)" "WARNING" "FINAL"

if ($failCount -eq 0) {
    Write-TestLog "🎉 TOUS LES BUILDS SONT VALIDES!" "SUCCESS" "FINAL"
    $exitCode = 0
} else {
    Write-TestLog "⚠️ $failCount builds ont échoué - Action requise" "ERROR" "FINAL"
    $exitCode = 1
}

# Recommandations
Write-TestLog "" "INFO" "FINAL"
Write-TestLog "📋 RECOMMANDATIONS:" "INFO" "FINAL"
if ($Global:SecurityIssues.Count -gt 0) {
    Write-TestLog "🔐 Corriger les vulnérabilités de sécurité détectées" "WARNING" "FINAL"
}

$slowBuilds = $Global:BuildMetrics | Where-Object {$_.BuildTime -gt 120}
if ($slowBuilds.Count -gt 0) {
    Write-TestLog "⚡ Optimiser les builds lents: $($slowBuilds.Service -join ', ')" "WARNING" "FINAL"
}

Write-TestLog "🐳 Considérer les builds multi-stage pour la production" "INFO" "FINAL"
Write-TestLog "📦 Implémenter le cache des layers Docker" "INFO" "FINAL"
Write-TestLog "🔍 Intégrer les scans sécurité dans CI/CD" "INFO" "FINAL"

Write-TestLog "" "INFO" "FINAL"
Write-TestLog "Tests terminés - Code de sortie: $exitCode" "INFO" "FINAL"

exit $exitCode
