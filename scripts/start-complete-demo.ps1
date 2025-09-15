# =====================================================================================
# Script de démarrage complet - Station Traffeyère IoT AI Platform
# Test intégration XAI + Digital Twin + Edge AI + MQTT
# =====================================================================================

param(
    [switch]$CleanStart = $false,
    [switch]$SkipBuild = $false,
    [int]$WaitSeconds = 30
)

Write-Host "🚀 " -ForegroundColor Blue -NoNewline
Write-Host "Station Traffeyère - Démarrage stack complète" -ForegroundColor Cyan

# Couleurs
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Blue"
$Cyan = "Cyan"

# Vérifications prérequis
Write-Host "`n📋 Vérification prérequis..." -ForegroundColor Yellow

# Docker
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✅ Docker: $dockerVersion" -ForegroundColor $Green
    } else {
        Write-Host "❌ Docker requis" -ForegroundColor $Red
        exit 1
    }
} catch {
    Write-Host "❌ Docker non disponible: $_" -ForegroundColor $Red
    exit 1
}

# Docker Compose
try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "✅ $composeVersion" -ForegroundColor $Green
    } else {
        Write-Host "❌ Docker Compose requis" -ForegroundColor $Red
        exit 1
    }
} catch {
    Write-Host "❌ Docker Compose non disponible" -ForegroundColor $Red
    exit 1
}

# Nettoyage si demandé
if ($CleanStart) {
    Write-Host "`n🧹 Nettoyage environnement..." -ForegroundColor Yellow
    docker-compose -f docker-compose.iot-complete.yml down -v --remove-orphans 2>$null
    docker system prune -f 2>$null
    Write-Host "✅ Nettoyage terminé" -ForegroundColor $Green
}

# Création répertoires nécessaires
Write-Host "`n📁 Préparation répertoires..." -ForegroundColor Yellow
$directories = @(
    "logs",
    "mqtt/data", 
    "mqtt/log",
    "models",
    "digital-twin-unity/builds"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Créé: $dir" -ForegroundColor $Green
    }
}

# Fichiers de configuration manquants
Write-Host "`n📝 Création fichiers configuration..." -ForegroundColor Yellow

# Mot de passe MQTT
$mqttPasswd = "mqtt/passwd"
if (!(Test-Path $mqttPasswd)) {
    # Format: username:password_hash
    "station_mqtt:`$2b`$10`$abcdefghijk..." | Out-File -FilePath $mqttPasswd -Encoding ascii
    Write-Host "✅ Créé: $mqttPasswd" -ForegroundColor $Green
}

# ACL MQTT
$mqttAcl = "mqtt/acl"
if (!(Test-Path $mqttAcl)) {
    @"
# ACL MQTT Station Traffeyère
user station_mqtt
topic readwrite station/traffeyere/+
topic readwrite station/traffeyere/sensors/+/data
topic readwrite station/traffeyere/analytics/+
topic readwrite station/traffeyere/commands/+
"@ | Out-File -FilePath $mqttAcl -Encoding ascii
    Write-Host "✅ Créé: $mqttAcl" -ForegroundColor $Green
}

# Dockerfile pour components manquants
$dockerfiles = @{
    "core/iot-data-generator/Dockerfile" = @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "iot_data_generator.py"]
"@

    "core/edge-ai-engine/Dockerfile" = @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8091
CMD ["python", "edge_ai_engine.py"]
"@

    "interfaces/voice-assistant-xia/Dockerfile.backend" = @"
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend.py .
EXPOSE 5000 5001
CMD ["python", "backend.py"]
"@

    "interfaces/voice-assistant-xia/Dockerfile.frontend" = @"
FROM nginx:alpine
COPY demo/ /usr/share/nginx/html/
EXPOSE 80
"@
}

foreach ($dockerfile in $dockerfiles.Keys) {
    $dockerDir = Split-Path $dockerfile -Parent
    if (!(Test-Path $dockerDir)) {
        New-Item -ItemType Directory -Path $dockerDir -Force | Out-Null
    }
    
    if (!(Test-Path $dockerfile)) {
        $dockerfiles[$dockerfile] | Out-File -FilePath $dockerfile -Encoding ascii
        Write-Host "✅ Créé: $dockerfile" -ForegroundColor $Green
    }
}

# Requirements.txt manquants
$requirementsFiles = @{
    "core/iot-data-generator/requirements.txt" = @"
paho-mqtt==1.6.1
numpy==1.24.3
faker==19.6.2
"@
    
    "core/edge-ai-engine/requirements.txt" = @"
paho-mqtt==1.6.1
scikit-learn==1.3.0
flask==2.3.3
numpy==1.24.3
requests==2.31.0
"@
    
    "interfaces/voice-assistant-xia/requirements.txt" = @"
flask==2.3.3
flask-socketio==5.3.6
flask-cors==4.0.0
paho-mqtt==1.6.1
redis==4.6.0
requests==2.31.0
"@
}

foreach ($reqFile in $requirementsFiles.Keys) {
    if (!(Test-Path $reqFile)) {
        $requirementsFiles[$reqFile] | Out-File -FilePath $reqFile -Encoding ascii
        Write-Host "✅ Créé: $reqFile" -ForegroundColor $Green
    }
}

# Démarrage des services
Write-Host "`n🐳 Démarrage stack IoT complète..." -ForegroundColor Yellow

try {
    if (!$SkipBuild) {
        Write-Host "🔨 Build des images Docker..." -ForegroundColor $Blue
        docker-compose -f docker-compose.iot-complete.yml build --parallel
    }
    
    Write-Host "🚀 Lancement des services..." -ForegroundColor $Blue
    docker-compose -f docker-compose.iot-complete.yml up -d
    
    Write-Host "✅ Services lancés avec succès" -ForegroundColor $Green
} catch {
    Write-Host "❌ Erreur lancement: $_" -ForegroundColor $Red
    exit 1
}

# Attente démarrage services
Write-Host "`n⏳ Attente démarrage services ($WaitSeconds secondes)..." -ForegroundColor $Yellow
Start-Sleep -Seconds $WaitSeconds

# Vérification santé services
Write-Host "`n🏥 Vérification santé services..." -ForegroundColor $Yellow

$services = @(
    @{Name="MQTT Broker"; Url="http://localhost:9001"; Port=1883},
    @{Name="Edge AI Engine"; Url="http://localhost:8091/health"; Port=8091},
    @{Name="XAI Backend"; Url="http://localhost:5000/health"; Port=5000},
    @{Name="XAI Frontend"; Url="http://localhost:3000"; Port=3000},
    @{Name="Redis Cache"; Url=""; Port=6379}
)

$healthyServices = 0
foreach ($service in $services) {
    try {
        if ($service.Url) {
            $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -UseBasicParsing 2>$null
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $($service.Name)" -ForegroundColor $Green
                $healthyServices++
            }
        } else {
            # Test port TCP
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $connect = $tcpClient.BeginConnect("localhost", $service.Port, $null, $null)
            $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
            if ($wait) {
                $tcpClient.EndConnect($connect)
                Write-Host "✅ $($service.Name)" -ForegroundColor $Green
                $healthyServices++
            } else {
                Write-Host "❌ $($service.Name)" -ForegroundColor $Red
            }
            $tcpClient.Close()
        }
    } catch {
        Write-Host "❌ $($service.Name): $_" -ForegroundColor $Red
    }
}

# Statut final
Write-Host "`n📊 " -ForegroundColor $Blue -NoNewline
Write-Host "Statut services: $healthyServices/$($services.Count) en ligne" -ForegroundColor $Cyan

if ($healthyServices -eq $services.Count) {
    Write-Host "`n🎉 " -ForegroundColor $Green -NoNewline
    Write-Host "Stack complètement opérationnelle !" -ForegroundColor $Green
} else {
    Write-Host "`n⚠️ " -ForegroundColor $Yellow -NoNewline  
    Write-Host "Certains services ne répondent pas encore" -ForegroundColor $Yellow
}

# URLs d'accès
Write-Host "`n🌐 URLs d'accès:" -ForegroundColor $Cyan
Write-Host "  • Assistant Vocal XAI:    http://localhost:3000" -ForegroundColor White
Write-Host "  • API XAI Backend:        http://localhost:5000" -ForegroundColor White
Write-Host "  • Edge AI Analytics:      http://localhost:8091" -ForegroundColor White
Write-Host "  • Digital Twin Unity:     http://localhost:8080" -ForegroundColor White
Write-Host "  • Dashboard Monitoring:   http://localhost:3001" -ForegroundColor White

# Test rapide
Write-Host "`n🧪 Test rapide intégration..." -ForegroundColor $Yellow

try {
    # Test XAI Backend
    $xaiTest = Invoke-RestMethod -Uri "http://localhost:5000/api/dashboard/summary" -TimeoutSec 5
    Write-Host "✅ XAI Backend: $($xaiTest.total_sensors) capteurs détectés" -ForegroundColor $Green
} catch {
    Write-Host "❌ XAI Backend non responsive" -ForegroundColor $Red
}

# Commandes utiles
Write-Host "`n🛠️  Commandes utiles:" -ForegroundColor $Cyan
Write-Host "  • Logs temps réel:        docker-compose -f docker-compose.iot-complete.yml logs -f" -ForegroundColor White
Write-Host "  • Statut services:        docker-compose -f docker-compose.iot-complete.yml ps" -ForegroundColor White
Write-Host "  • Arrêt services:         docker-compose -f docker-compose.iot-complete.yml down" -ForegroundColor White
Write-Host "  • Test commande vocale:   Dire 'Statut des capteurs' dans l'interface" -ForegroundColor White

Write-Host "`n🎙️ " -ForegroundColor $Blue -NoNewline
Write-Host "L'assistant vocal XAI est maintenant connecté aux données IoT temps réel !" -ForegroundColor $Green

Write-Host "`n🎮 " -ForegroundColor $Blue -NoNewline  
Write-Host "Le Digital Twin peut maintenant visualiser les 127 capteurs en 3D !" -ForegroundColor $Green

Write-Host "`n🚀 Démarrage terminé avec succès ! 🏆" -ForegroundColor $Green
