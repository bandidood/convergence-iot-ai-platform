# System Requirements Check for RNCP 39394 Project

Write-Host "VALIDATION EXIGENCES SYSTEME RNCP 39394" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor White

$MIN_RAM_GB = 16  # Reduced for development environment
$MIN_DISK_GB = 100  # Reduced for development environment
$MIN_CPU_CORES = 4  # Reduced for development environment

$ERRORS = 0

# Check RAM
Write-Host "`nVerification RAM..." -ForegroundColor Yellow
$TotalRAM = Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory
$TotalRAM_GB = [Math]::Round($TotalRAM / 1GB, 2)

if ($TotalRAM_GB -ge $MIN_RAM_GB) {
    Write-Host "✅ RAM Systeme: $($TotalRAM_GB)GB (requis: $($MIN_RAM_GB)GB)" -ForegroundColor Green
} else {
    Write-Host "❌ RAM Systeme: $($TotalRAM_GB)GB (requis: $($MIN_RAM_GB)GB)" -ForegroundColor Red
    $ERRORS++
}

# Check CPU
Write-Host "`nVerification CPU..." -ForegroundColor Yellow
$CPU_CORES = (Get-CimInstance -ClassName Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum

if ($CPU_CORES -ge $MIN_CPU_CORES) {
    Write-Host "✅ CPU Cores: $CPU_CORES (requis: $MIN_CPU_CORES)" -ForegroundColor Green
} else {
    Write-Host "❌ CPU Cores: $CPU_CORES (requis: $MIN_CPU_CORES)" -ForegroundColor Red
    $ERRORS++
}

# Check Disk Space
Write-Host "`nVerification espace disque..." -ForegroundColor Yellow
$CurrentDrive = (Get-Location).Drive.Name
$DiskSpace = Get-PSDrive -Name $CurrentDrive | Select-Object -ExpandProperty Free
$AvailableSpace_GB = [Math]::Round($DiskSpace / 1GB, 2)

if ($AvailableSpace_GB -ge $MIN_DISK_GB) {
    Write-Host "✅ Espace Disque: $($AvailableSpace_GB)GB (requis: $($MIN_DISK_GB)GB)" -ForegroundColor Green
} else {
    Write-Host "❌ Espace Disque: $($AvailableSpace_GB)GB (requis: $($MIN_DISK_GB)GB)" -ForegroundColor Red
    $ERRORS++
}

# Check Docker
Write-Host "`nVerification Docker..." -ForegroundColor Yellow
try {
    $DockerVersion = docker --version 2>$null
    if ($DockerVersion) {
        Write-Host "✅ Docker installe: $DockerVersion" -ForegroundColor Green
        
        $DockerInfo = docker info 2>$null
        if ($DockerInfo) {
            Write-Host "✅ Docker daemon operationnel" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker daemon non accessible" -ForegroundColor Red
            $ERRORS++
        }
    } else {
        Write-Host "❌ Docker non installe" -ForegroundColor Red
        $ERRORS++
    }
} catch {
    Write-Host "❌ Docker non trouve" -ForegroundColor Red
    $ERRORS++
}

# Check Docker Compose
Write-Host "`nVerification Docker Compose..." -ForegroundColor Yellow
try {
    $ComposeVersion = docker compose version 2>$null
    if ($ComposeVersion) {
        Write-Host "✅ Docker Compose installe: $ComposeVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker Compose non installe" -ForegroundColor Red
        $ERRORS++
    }
} catch {
    Write-Host "❌ Docker Compose non trouve" -ForegroundColor Red
    $ERRORS++
}

# Summary
Write-Host "`n===============================================" -ForegroundColor White
if ($ERRORS -eq 0) {
    Write-Host "🎉 SYSTEME COMPATIBLE - TOUTES EXIGENCES SATISFAITES" -ForegroundColor Green
    Write-Host "✅ Pret pour le deploiement de l'infrastructure securisee" -ForegroundColor Green
    
    Write-Host "`n📋 PROCHAINES ETAPES SEMAINE 1:" -ForegroundColor Cyan
    Write-Host "1. Valider infrastructure Docker existante" -ForegroundColor White
    Write-Host "2. Examiner le docker-compose.yml actuel" -ForegroundColor White
    Write-Host "3. Creer le generateur IoT securise" -ForegroundColor White
    Write-Host "4. Configurer environnement developpement" -ForegroundColor White
    
} else {
    Write-Host "⚠️  $ERRORS EXIGENCE(S) NON SATISFAITE(S)" -ForegroundColor Red
    Write-Host "❌ Veuillez corriger les problemes avant de continuer" -ForegroundColor Red
}
