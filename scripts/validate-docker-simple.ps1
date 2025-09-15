# ================================================================
# SCRIPT DE VALIDATION DOCKER COMPOSE - VERSION SIMPLE
# Station Traffeyere IoT/AI Platform
# ================================================================

Write-Host "=== VALIDATION DOCKER COMPOSE PATHS ===" -ForegroundColor Cyan
Write-Host "Station Traffeyere IoT/AI Platform - RNCP 39394" -ForegroundColor Cyan
Write-Host ""

# Test des fichiers Docker Compose
$dockerFiles = @(
    "docker-compose.yml",
    "docker-compose.production.yml", 
    "docker-compose.security.yml",
    "docker-compose.monitoring.yml",
    "docker-compose.override.yml"
)

$allValid = $true

foreach ($file in $dockerFiles) {
    if (Test-Path $file) {
        Write-Host "Checking: $file" -ForegroundColor Blue
        
        $content = Get-Content $file -Raw
        
        # Anciens chemins a corriger
        $oldPaths = @("./config/", "./monitoring/prometheus/", "./monitoring/grafana/", "./database/init:")
        
        $fileValid = $true
        foreach ($oldPath in $oldPaths) {
            if ($content -like "*$oldPath*") {
                Write-Host "  [ERROR] Old path found: $oldPath" -ForegroundColor Red
                $fileValid = $false
                $allValid = $false
            }
        }
        
        if ($fileValid) {
            Write-Host "  [OK] All paths are correct" -ForegroundColor Green
        }
    } else {
        Write-Host "File not found: $file" -ForegroundColor Yellow
    }
}

# Test structure directories
Write-Host ""
Write-Host "=== DIRECTORY STRUCTURE CHECK ===" -ForegroundColor Cyan

$requiredDirs = @(
    "configurations",
    "configurations/nginx",
    "configurations/prometheus",
    "configurations/grafana",
    "configurations/mosquitto",
    "environments",
    "security",
    "interfaces/soc-dashboard"
)

$dirValid = $true
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir -PathType Container) {
        Write-Host "[OK] $dir" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $dir" -ForegroundColor Red
        $dirValid = $false
    }
}

# Summary
Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
if ($allValid) {
    Write-Host "[SUCCESS] Docker Compose paths are valid" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Docker Compose paths need correction" -ForegroundColor Red
}

if ($dirValid) {
    Write-Host "[SUCCESS] Directory structure is valid" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Directory structure is incomplete" -ForegroundColor Yellow
}

if ($allValid -and $dirValid) {
    Write-Host ""
    Write-Host "Ready for deployment!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "Actions required - see details above" -ForegroundColor Yellow
    exit 1
}