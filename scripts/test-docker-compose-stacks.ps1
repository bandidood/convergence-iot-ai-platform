# ================================================================
# TEST DES STACKS DOCKER COMPOSE COMPLETES
# Station Traffeyere IoT/AI Platform - RNCP 39394
# Validation des stacks complètes avec tests d'intégration
# ================================================================

param(
    [switch]$TestMainStack = $true,
    [switch]$TestSecurityStack = $true,
    [switch]$TestMonitoringStack = $true,
    [switch]$TestProductionStack = $false,
    [switch]$QuickTest = $false,
    [int]$HealthCheckTimeout = 180,
    [switch]$GenerateReport = $true
)

# Configuration des stacks
$DockerComposeStacks = @{
    'main' = @{
        File = 'docker-compose.yml'
        Description = 'Stack principale avec tous les services de base'
        CriticalServices = @('postgres', 'redis', 'influxdb', 'mosquitto', 'backend')
        OptionalServices = @('keycloak', 'minio', 'grafana', 'prometheus')
        HealthChecks = @{
            'postgres' = 'SELECT 1'
            'redis' = 'PING'
            'mosquitto' = 'TCP:1883'
            'backend' = 'http://localhost:8000/health'
            'grafana' = 'http://localhost:3000/api/health'
        }
        ExpectedPorts = @(5432, 6379, 8086, 1883, 8000, 3000, 9090)
    }
    
    'security' = @{
        File = 'docker-compose.security.yml'
        Description = 'Stack sécurité avec SIEM et SOAR'
        CriticalServices = @('vault', 'elasticsearch', 'kibana', 'wazuh-manager')
        OptionalServices = @('suricata', 'nginx-security', 'soar-engine', 'security-dashboard')
        HealthChecks = @{
            'vault' = 'http://localhost:8200/v1/sys/health'
            'elasticsearch' = 'http://localhost:9200/_cluster/health'
            'kibana' = 'http://localhost:5601/api/status'
            'security-dashboard' = 'http://localhost:3001/health'
        }
        ExpectedPorts = @(8200, 9200, 5601, 1514, 1515, 55000, 3001)
    }
    
    'monitoring' = @{
        File = 'docker-compose.monitoring.yml'
        Description = 'Stack monitoring et observabilité'
        CriticalServices = @('prometheus', 'grafana', 'node-exporter', 'cadvisor')
        OptionalServices = @('alertmanager', 'jaeger', 'loki', 'promtail', 'blackbox-exporter')
        HealthChecks = @{
            'prometheus' = 'http://localhost:9090/-/healthy'
            'grafana' = 'http://localhost:3000/api/health'
            'alertmanager' = 'http://localhost:9093/-/healthy'
            'jaeger' = 'http://localhost:16686/'
        }
        ExpectedPorts = @(9090, 3000, 9100, 8080, 9093, 16686, 3100)
    }
    
    'production' = @{
        File = 'docker-compose.production.yml'
        Description = 'Stack production optimisée'
        CriticalServices = @('postgres', 'redis', 'influxdb', 'mosquitto', 'backend')
        OptionalServices = @('prometheus', 'grafana')
        HealthChecks = @{
            'postgres' = 'SELECT 1'
            'redis' = 'PING'
            'mosquitto' = 'TCP:1883'
            'backend' = 'http://localhost:8000/health'
        }
        ExpectedPorts = @(5432, 6379, 8086, 1883, 8000)
    }
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  DOCKER COMPOSE STACK TESTING SUITE" -ForegroundColor Cyan
Write-Host "  Station Traffeyere IoT/AI Platform - RNCP 39394" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Main Stack: $TestMainStack" -ForegroundColor Yellow
Write-Host "Security Stack: $TestSecurityStack" -ForegroundColor Yellow
Write-Host "Monitoring Stack: $TestMonitoringStack" -ForegroundColor Yellow
Write-Host "Production Stack: $TestProductionStack" -ForegroundColor Yellow
Write-Host "Quick Test Mode: $QuickTest" -ForegroundColor Yellow
Write-Host ""

# Résultats globaux
$Global:StackResults = @()
$Global:StackErrors = @()

function Write-StackLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Stack = "GENERAL"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] [$Stack] $Message"
    
    switch ($Level) {
        "ERROR"   { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "INFO"    { Write-Host $logEntry -ForegroundColor White }
        default   { Write-Host $logEntry }
    }
    
    Add-Content -Path "compose-stack-test-$(Get-Date -Format 'yyyyMMdd').log" -Value $logEntry
}

# Test de disponibilité des fichiers Docker Compose
function Test-ComposeFileAvailability {
    param(
        [string]$StackName,
        [hashtable]$StackConfig
    )
    
    Write-StackLog "Vérification disponibilité fichier compose..." "INFO" $StackName
    
    if (-not (Test-Path $StackConfig.File)) {
        Write-StackLog "Fichier compose manquant: $($StackConfig.File)" "ERROR" $StackName
        return $false
    }
    
    # Vérification syntaxe Docker Compose
    Write-StackLog "Validation syntaxe Docker Compose..." "INFO" $StackName
    
    $validateOutput = docker-compose -f $StackConfig.File config 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-StackLog "Erreur syntaxe Docker Compose: $($validateOutput -join '; ')" "ERROR" $StackName
        return $false
    }
    
    Write-StackLog "Fichier compose validé avec succès" "SUCCESS" $StackName
    return $true
}

# Démarrage d'une stack Docker Compose
function Start-DockerComposeStack {
    param(
        [string]$StackName,
        [hashtable]$StackConfig
    )
    
    Write-StackLog "Démarrage de la stack..." "INFO" $StackName
    
    try {
        # Nettoyage préventif
        docker-compose -f $StackConfig.File down --remove-orphans 2>$null
        
        # Démarrage de la stack
        $startOutput = docker-compose -f $StackConfig.File up -d 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-StackLog "Échec démarrage stack: $($startOutput -join '; ')" "ERROR" $StackName
            return $false
        }
        
        Write-StackLog "Stack démarrée avec succès" "SUCCESS" $StackName
        return $true
        
    } catch {
        Write-StackLog "Exception démarrage stack: $($_.Exception.Message)" "ERROR" $StackName
        return $false
    }
}

# Vérification de l'état des services
function Test-ServiceStatus {
    param(
        [string]$StackName,
        [hashtable]$StackConfig
    )
    
    Write-StackLog "Vérification état des services..." "INFO" $StackName
    
    $serviceStatus = @{}
    $allHealthy = $true
    
    # Obtenir la liste des services en cours d'exécution
    $runningServices = docker-compose -f $StackConfig.File ps --services 2>$null
    
    if (-not $runningServices) {
        Write-StackLog "Impossible d'obtenir la liste des services" "ERROR" $StackName
        return $false
    }
    
    foreach ($service in $runningServices) {
        if (-not $service.Trim()) { continue }
        
        Write-StackLog "Vérification service: $service" "INFO" $StackName
        
        # Vérifier l'état du conteneur
        $containerStatus = docker-compose -f $StackConfig.File ps $service 2>$null
        
        if ($containerStatus -match "Up") {
            Write-StackLog "Service $service: Running" "SUCCESS" $StackName
            $serviceStatus[$service] = @{
                Status = "Running"
                Healthy = $true
            }
        } elseif ($containerStatus -match "Exit") {
            Write-StackLog "Service $service: Exited" "ERROR" $StackName
            $serviceStatus[$service] = @{
                Status = "Exited"
                Healthy = $false
            }
            $allHealthy = $false
        } else {
            Write-StackLog "Service $service: Unknown status" "WARNING" $StackName
            $serviceStatus[$service] = @{
                Status = "Unknown"
                Healthy = $false
            }
            $allHealthy = $false
        }
    }
    
    return @{
        AllHealthy = $allHealthy
        Services = $serviceStatus
    }
}

# Test des health checks
function Test-HealthChecks {
    param(
        [string]$StackName,
        [hashtable]$StackConfig
    )
    
    Write-StackLog "Exécution des health checks..." "INFO" $StackName
    
    $healthResults = @{}
    
    foreach ($service in $StackConfig.HealthChecks.Keys) {
        $healthCheck = $StackConfig.HealthChecks[$service]
        Write-StackLog "Health check pour $service : $healthCheck" "INFO" $StackName
        
        $startTime = Get-Date
        $healthy = $false
        $attempts = 0
        $maxAttempts = if ($QuickTest) { 3 } else { 10 }
        
        while (-not $healthy -and $attempts -lt $maxAttempts) {
            $attempts++
            
            try {
                if ($healthCheck.StartsWith("http")) {
                    # Test HTTP
                    $response = Invoke-WebRequest -Uri $healthCheck -TimeoutSec 5 -UseBasicParsing 2>$null
                    $healthy = $response.StatusCode -eq 200
                } elseif ($healthCheck.StartsWith("TCP:")) {
                    # Test TCP
                    $port = $healthCheck.Split(":")[1]
                    $tcpClient = New-Object System.Net.Sockets.TcpClient
                    $connectResult = $tcpClient.ConnectAsync("localhost", $port)
                    $healthy = $connectResult.Wait(5000)  # 5 seconds timeout
                    $tcpClient.Close()
                } elseif ($healthCheck -eq "PING") {
                    # Test Redis PING
                    $pingResult = docker exec $(docker-compose -f $StackConfig.File ps -q $service) redis-cli ping 2>$null
                    $healthy = $pingResult -eq "PONG"
                } elseif ($healthCheck.StartsWith("SELECT")) {
                    # Test SQL
                    $sqlResult = docker exec $(docker-compose -f $StackConfig.File ps -q $service) psql -U postgres -c "$healthCheck" 2>$null
                    $healthy = $LASTEXITCODE -eq 0
                }
                
            } catch {
                $healthy = $false
            }
            
            if (-not $healthy) {
                Start-Sleep 10
            }
        }
        
        $responseTime = (Get-Date) - $startTime
        
        $healthResults[$service] = @{
            Healthy = $healthy
            Attempts = $attempts
            ResponseTime = $responseTime.TotalSeconds
        }
        
        if ($healthy) {
            Write-StackLog "Health check $service : OK ($($responseTime.TotalSeconds.ToString('F2'))s)" "SUCCESS" $StackName
        } else {
            Write-StackLog "Health check $service : FAILED après $attempts tentatives" "ERROR" $StackName
        }
    }
    
    return $healthResults
}

# Test des ports réseau
function Test-NetworkPorts {
    param(
        [string]$StackName,
        [hashtable]$StackConfig
    )
    
    Write-StackLog "Vérification des ports réseau..." "INFO" $StackName
    
    $portResults = @{}
    
    foreach ($port in $StackConfig.ExpectedPorts) {
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $connectResult = $tcpClient.ConnectAsync("localhost", $port)
            $connected = $connectResult.Wait(2000)  # 2 seconds timeout
            
            $portResults[$port] = $connected
            
            if ($connected) {
                Write-StackLog "Port $port : Accessible" "SUCCESS" $StackName
            } else {
                Write-StackLog "Port $port : Non accessible" "WARNING" $StackName
            }
            
            $tcpClient.Close()
            
        } catch {
            $portResults[$port] = $false
            Write-StackLog "Port $port : Erreur de test" "WARNING" $StackName
        }
    }
    
    return $portResults
}

# Test d'intégration basique
function Test-BasicIntegration {
    param(
        [string]$StackName,
        [hashtable]$StackConfig
    )
    
    if ($QuickTest) {
        Write-StackLog "Tests d'intégration ignorés en mode quick test" "INFO" $StackName
        return @{ Success = $true; Results = @{} }
    }
    
    Write-StackLog "Tests d'intégration basique..." "INFO" $StackName
    
    $integrationResults = @{}
    
    # Tests spécifiques selon la stack
    switch ($StackName) {
        'main' {
            # Test connexion backend -> base de données
            try {
                $dbTestResult = Invoke-WebRequest -Uri "http://localhost:8000/api/health/database" -TimeoutSec 10 -UseBasicParsing 2>$null
                $integrationResults['backend_db'] = $dbTestResult.StatusCode -eq 200
            } catch {
                $integrationResults['backend_db'] = $false
            }
            
            # Test MQTT publish/subscribe
            try {
                # Simuler un message MQTT simple
                $mqttTest = docker exec $(docker-compose -f $StackConfig.File ps -q mosquitto) mosquitto_pub -h localhost -t test/topic -m "test_message" 2>$null
                $integrationResults['mqtt_pubsub'] = $LASTEXITCODE -eq 0
            } catch {
                $integrationResults['mqtt_pubsub'] = $false
            }
        }
        
        'security' {
            # Test intégration Vault -> applications
            try {
                $vaultStatus = Invoke-WebRequest -Uri "http://localhost:8200/v1/sys/seal-status" -TimeoutSec 10 -UseBasicParsing 2>$null
                $vaultData = $vaultStatus.Content | ConvertFrom-Json
                $integrationResults['vault_unsealed'] = -not $vaultData.sealed
            } catch {
                $integrationResults['vault_unsealed'] = $false
            }
            
            # Test Elasticsearch -> Kibana
            try {
                $esHealth = Invoke-WebRequest -Uri "http://localhost:9200/_cluster/health" -TimeoutSec 10 -UseBasicParsing 2>$null
                $esData = $esHealth.Content | ConvertFrom-Json
                $integrationResults['es_kibana'] = $esData.status -in @('green', 'yellow')
            } catch {
                $integrationResults['es_kibana'] = $false
            }
        }
        
        'monitoring' {
            # Test Prometheus -> targets
            try {
                $promTargets = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/targets" -TimeoutSec 10 -UseBasicParsing 2>$null
                $promData = $promTargets.Content | ConvertFrom-Json
                $activeTargets = $promData.data.activeTargets | Where-Object { $_.health -eq "up" }
                $integrationResults['prometheus_targets'] = $activeTargets.Count -gt 0
            } catch {
                $integrationResults['prometheus_targets'] = $false
            }
            
            # Test Grafana -> Prometheus datasource
            try {
                $grafanaDs = Invoke-WebRequest -Uri "http://localhost:3000/api/datasources" -TimeoutSec 10 -UseBasicParsing 2>$null
                $integrationResults['grafana_prometheus'] = $grafanaDs.StatusCode -eq 200
            } catch {
                $integrationResults['grafana_prometheus'] = $false
            }
        }
    }
    
    $successCount = ($integrationResults.Values | Where-Object { $_ -eq $true }).Count
    $totalCount = $integrationResults.Count
    
    Write-StackLog "Tests d'intégration: $successCount/$totalCount réussis" "INFO" $StackName
    
    return @{
        Success = $successCount -eq $totalCount
        Results = $integrationResults
    }
}

# Nettoyage d'une stack
function Stop-DockerComposeStack {
    param(
        [string]$StackName,
        [hashtable]$StackConfig
    )
    
    Write-StackLog "Arrêt et nettoyage de la stack..." "INFO" $StackName
    
    try {
        docker-compose -f $StackConfig.File down --remove-orphans --volumes 2>$null
        Write-StackLog "Stack arrêtée et nettoyée" "SUCCESS" $StackName
    } catch {
        Write-StackLog "Erreur lors du nettoyage: $($_.Exception.Message)" "WARNING" $StackName
    }
}

# Test complet d'une stack
function Test-CompleteStack {
    param(
        [string]$StackName,
        [hashtable]$StackConfig
    )
    
    Write-StackLog "========================================" "INFO" $StackName
    Write-StackLog "TEST COMPLET DE LA STACK: $StackName" "INFO" $StackName
    Write-StackLog "Description: $($StackConfig.Description)" "INFO" $StackName
    Write-StackLog "========================================" "INFO" $StackName
    
    $startTime = Get-Date
    $testResult = @{
        StackName = $StackName
        StartTime = $startTime
        Success = $false
        Phases = @{}
    }
    
    # Phase 1: Vérification fichier compose
    Write-StackLog "Phase 1: Vérification fichier compose" "INFO" $StackName
    $fileCheck = Test-ComposeFileAvailability -StackName $StackName -StackConfig $StackConfig
    $testResult.Phases['FileCheck'] = $fileCheck
    
    if (-not $fileCheck) {
        $testResult.EndTime = Get-Date
        $testResult.Duration = ($testResult.EndTime - $testResult.StartTime).TotalSeconds
        $Global:StackResults += $testResult
        return $testResult
    }
    
    # Phase 2: Démarrage stack
    Write-StackLog "Phase 2: Démarrage de la stack" "INFO" $StackName
    $startStack = Start-DockerComposeStack -StackName $StackName -StackConfig $StackConfig
    $testResult.Phases['StartStack'] = $startStack
    
    if (-not $startStack) {
        $testResult.EndTime = Get-Date
        $testResult.Duration = ($testResult.EndTime - $testResult.StartTime).TotalSeconds
        $Global:StackResults += $testResult
        return $testResult
    }
    
    # Phase 3: Vérification états services
    Write-StackLog "Phase 3: Vérification état des services" "INFO" $StackName
    $serviceStatus = Test-ServiceStatus -StackName $StackName -StackConfig $StackConfig
    $testResult.Phases['ServiceStatus'] = $serviceStatus
    
    # Attendre un peu pour la stabilisation
    if (-not $QuickTest) {
        Write-StackLog "Attente stabilisation services (30s)..." "INFO" $StackName
        Start-Sleep 30
    }
    
    # Phase 4: Health checks
    Write-StackLog "Phase 4: Health checks" "INFO" $StackName
    $healthChecks = Test-HealthChecks -StackName $StackName -StackConfig $StackConfig
    $testResult.Phases['HealthChecks'] = $healthChecks
    
    # Phase 5: Tests réseau
    Write-StackLog "Phase 5: Tests des ports réseau" "INFO" $StackName
    $networkPorts = Test-NetworkPorts -StackName $StackName -StackConfig $StackConfig
    $testResult.Phases['NetworkPorts'] = $networkPorts
    
    # Phase 6: Tests d'intégration
    Write-StackLog "Phase 6: Tests d'intégration" "INFO" $StackName
    $integration = Test-BasicIntegration -StackName $StackName -StackConfig $StackConfig
    $testResult.Phases['Integration'] = $integration
    
    # Phase 7: Nettoyage
    Write-StackLog "Phase 7: Nettoyage" "INFO" $StackName
    Stop-DockerComposeStack -StackName $StackName -StackConfig $StackConfig
    
    # Évaluation globale
    $healthyServices = ($healthChecks.Values | Where-Object { $_.Healthy -eq $true }).Count
    $totalHealthChecks = $healthChecks.Count
    $accessiblePorts = ($networkPorts.Values | Where-Object { $_ -eq $true }).Count
    $totalPorts = $networkPorts.Count
    
    $testResult.Success = (
        $fileCheck -and 
        $startStack -and 
        $serviceStatus.AllHealthy -and 
        ($healthyServices -ge ($totalHealthChecks * 0.8)) -and  # Au moins 80% des health checks OK
        $integration.Success
    )
    
    $testResult.EndTime = Get-Date
    $testResult.Duration = ($testResult.EndTime - $testResult.StartTime).TotalSeconds
    
    Write-StackLog "========================================" "INFO" $StackName
    if ($testResult.Success) {
        Write-StackLog "✅ STACK VALIDÉE avec succès en $($testResult.Duration.ToString('F2'))s" "SUCCESS" $StackName
    } else {
        Write-StackLog "❌ STACK ÉCHOUÉE après $($testResult.Duration.ToString('F2'))s" "ERROR" $StackName
    }
    Write-StackLog "Services sains: $healthyServices/$totalHealthChecks" "INFO" $StackName
    Write-StackLog "Ports accessibles: $accessiblePorts/$totalPorts" "INFO" $StackName
    Write-StackLog "========================================" "INFO" $StackName
    
    $Global:StackResults += $testResult
    return $testResult
}

# Génération du rapport final
function New-StackTestReport {
    if (-not $GenerateReport) {
        return
    }
    
    Write-StackLog "Génération du rapport final..." "INFO" "REPORT"
    
    $reportPath = "docker-compose-stack-test-$(Get-Date -Format 'yyyyMMdd-HHmmss').html"
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Docker Compose Stack Test Report - Station Traffeyere</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
        .stack-result { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .success { border-left: 5px solid #27ae60; }
        .error { border-left: 5px solid #e74c3c; }
        .phase { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px; }
        .metrics { display: flex; justify-content: space-around; margin: 20px 0; }
        .metric { text-align: center; background: white; padding: 15px; border-radius: 8px; }
        .metric h3 { margin: 0; color: #2c3e50; }
        .metric .value { font-size: 2em; font-weight: bold; color: #3498db; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background: #34495e; color: white; }
        .status-ok { color: #27ae60; font-weight: bold; }
        .status-error { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🐳 Docker Compose Stack Test Report</h1>
        <p>Station Traffeyere IoT/AI Platform - RNCP 39394</p>
        <p>Generated: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")</p>
        <p>Test Duration: $((($Global:StackResults | Measure-Object Duration -Sum).Sum).ToString('F2')) seconds total</p>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <h3>Total Stacks</h3>
            <div class="value">$($Global:StackResults.Count)</div>
        </div>
        <div class="metric">
            <h3>Successful</h3>
            <div class="value">$($Global:StackResults | Where-Object {$_.Success} | Measure-Object | Select-Object -ExpandProperty Count)</div>
        </div>
        <div class="metric">
            <h3>Failed</h3>
            <div class="value">$($Global:StackResults | Where-Object {-not $_.Success} | Measure-Object | Select-Object -ExpandProperty Count)</div>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <div class="value">$(if ($Global:StackResults.Count -gt 0) { (($Global:StackResults | Where-Object {$_.Success}).Count / $Global:StackResults.Count * 100).ToString('F1') } else { '0' })%</div>
        </div>
    </div>
"@

    foreach ($result in $Global:StackResults) {
        $statusClass = if ($result.Success) { "success" } else { "error" }
        $statusText = if ($result.Success) { "✅ SUCCESS" } else { "❌ FAILED" }
        
        $html += @"
    <div class="stack-result $statusClass">
        <h2>$($result.StackName.ToUpper()) STACK</h2>
        <p><strong>Status:</strong> <span class="status-$(if ($result.Success) { 'ok' } else { 'error' })">$statusText</span></p>
        <p><strong>Duration:</strong> $($result.Duration.ToString('F2')) seconds</p>
        <p><strong>Start Time:</strong> $($result.StartTime.ToString('HH:mm:ss'))</p>
        <p><strong>End Time:</strong> $($result.EndTime.ToString('HH:mm:ss'))</p>
        
        <h3>Test Phases</h3>
"@

        foreach ($phaseName in $result.Phases.Keys) {
            $phase = $result.Phases[$phaseName]
            $phaseStatus = "Unknown"
            
            if ($phase -is [bool]) {
                $phaseStatus = if ($phase) { "✅ OK" } else { "❌ FAILED" }
            } elseif ($phase -is [hashtable]) {
                if ($phase.ContainsKey('Success')) {
                    $phaseStatus = if ($phase.Success) { "✅ OK" } else { "❌ FAILED" }
                } elseif ($phase.ContainsKey('AllHealthy')) {
                    $phaseStatus = if ($phase.AllHealthy) { "✅ OK" } else { "⚠️ PARTIAL" }
                }
            }
            
            $html += "<div class='phase'><strong>$phaseName:</strong> $phaseStatus</div>"
        }
        
        $html += "</div>"
    }

    $html += @"
    
    <div style="background: white; padding: 20px; border-radius: 8px; margin-top: 30px;">
        <h2>📋 Recommendations</h2>
        <ul>
"@

    if (($Global:StackResults | Where-Object {-not $_.Success}).Count -gt 0) {
        $html += "<li>🔧 Fix failed stack tests before production deployment</li>"
    }
    
    $html += @"
            <li>🚀 Consider implementing automated stack health monitoring</li>
            <li>📊 Set up alerting for critical service failures</li>
            <li>🔄 Implement rolling updates for zero-downtime deployments</li>
            <li>📈 Monitor stack performance metrics in production</li>
            <li>🔒 Regular security scanning of Docker images</li>
        </ul>
    </div>
    
    <footer style="text-align: center; margin-top: 30px; color: #7f8c8d;">
        <p><em>Report generated by Station Traffeyere Docker Compose Stack Testing Suite</em></p>
    </footer>
</body>
</html>
"@

    $html | Out-File -FilePath $reportPath -Encoding UTF8
    Write-StackLog "Rapport HTML généré: $reportPath" "SUCCESS" "REPORT"
    
    # Ouvrir le rapport dans le navigateur
    Start-Process $reportPath
}

# === SCRIPT PRINCIPAL ===

Write-StackLog "Démarrage des tests de stacks Docker Compose" "INFO" "MAIN"

# Sélection des stacks à tester
$stacksToTest = @()

if ($TestMainStack -and (Test-Path $DockerComposeStacks['main'].File)) {
    $stacksToTest += 'main'
}

if ($TestSecurityStack -and (Test-Path $DockerComposeStacks['security'].File)) {
    $stacksToTest += 'security'
}

if ($TestMonitoringStack -and (Test-Path $DockerComposeStacks['monitoring'].File)) {
    $stacksToTest += 'monitoring'
}

if ($TestProductionStack -and (Test-Path $DockerComposeStacks['production'].File)) {
    $stacksToTest += 'production'
}

Write-StackLog "$($stacksToTest.Count) stacks sélectionnées pour les tests: $($stacksToTest -join ', ')" "INFO" "MAIN"

if ($stacksToTest.Count -eq 0) {
    Write-StackLog "Aucune stack disponible pour les tests" "ERROR" "MAIN"
    exit 1
}

# Test de chaque stack
foreach ($stackName in $stacksToTest) {
    $stackConfig = $DockerComposeStacks[$stackName]
    Test-CompleteStack -StackName $stackName -StackConfig $stackConfig
}

# Génération du rapport
New-StackTestReport

# Résultats finaux
$successCount = ($Global:StackResults | Where-Object {$_.Success}).Count
$totalCount = $Global:StackResults.Count
$successRate = if ($totalCount -gt 0) { ($successCount / $totalCount * 100) } else { 0 }

Write-StackLog "========================================" "INFO" "FINAL"
Write-StackLog "RÉSULTATS FINAUX" "INFO" "FINAL"
Write-StackLog "========================================" "INFO" "FINAL"
Write-StackLog "Stacks testées: $totalCount" "INFO" "FINAL"
Write-StackLog "Stacks validées: $successCount" "SUCCESS" "FINAL"
Write-StackLog "Taux de réussite: $($successRate.ToString('F1'))%" "INFO" "FINAL"

if ($successCount -eq $totalCount) {
    Write-StackLog "🎉 TOUTES LES STACKS SONT OPÉRATIONNELLES!" "SUCCESS" "FINAL"
    exit 0
} else {
    Write-StackLog "⚠️ $($totalCount - $successCount) stack(s) nécessitent une attention" "ERROR" "FINAL"
    exit 1
}