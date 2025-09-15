# Script PKI simplifié pour Station Traffeyère Zero-Trust
# Conforme RNCP 39394 - Semaine 5

Write-Host "🔐 Génération PKI Zero-Trust - RNCP 39394" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green

# Ajouter System.Web pour la génération de mots de passe
Add-Type -AssemblyName System.Web

# 1. Générer les secrets nécessaires
Write-Host "`n1️⃣ Génération des secrets sécurisés" -ForegroundColor Magenta

$Secrets = @{
    "postgres_password" = [System.Web.Security.Membership]::GeneratePassword(32, 8)
    "postgres_tde_key" = [System.Web.Security.Membership]::GeneratePassword(64, 16)
    "keycloak_db_password" = [System.Web.Security.Membership]::GeneratePassword(32, 8)
    "keycloak_admin_password" = [System.Web.Security.Membership]::GeneratePassword(24, 6)
    "grafana_admin_password" = [System.Web.Security.Membership]::GeneratePassword(24, 6)
    "grafana_oauth_secret" = [System.Web.Security.Membership]::GeneratePassword(48, 12)
    "redis_password" = [System.Web.Security.Membership]::GeneratePassword(32, 8)
    "lorawan_aes_key" = [System.Web.Security.Membership]::GeneratePassword(32, 8)
}

foreach ($SecretName in $Secrets.Keys) {
    $SecretFile = "secrets\$SecretName.txt"
    $SecretValue = $Secrets[$SecretName]
    $SecretValue | Out-File -FilePath $SecretFile -Encoding UTF8 -NoNewline
    Write-Host "🔐 Secret créé: $SecretName" -ForegroundColor Green
}

# 2. Créer un certificat auto-signé pour les tests
Write-Host "`n2️⃣ Génération certificat auto-signé pour tests" -ForegroundColor Magenta

$CertPath = "certs/test-selfsigned.crt"
$KeyPath = "certs/test-selfsigned.key"

try {
    # Utiliser PowerShell pour créer un certificat auto-signé
    $Cert = New-SelfSignedCertificate -DnsName @("localhost", "127.0.0.1", "station-traffeyere.local", "*.station-traffeyere.local") -CertStoreLocation "cert:\LocalMachine\My" -KeyAlgorithm RSA -KeyLength 2048 -NotAfter (Get-Date).AddYears(10)
    
    # Exporter le certificat
    Export-Certificate -Cert $Cert -FilePath $CertPath -Type CERT | Out-Null
    
    # Exporter la clé privée (pour les tests uniquement)
    $Password = ConvertTo-SecureString -String "StationTraffeyere2024!" -Force -AsPlainText
    Export-PfxCertificate -Cert $Cert -FilePath "certs/test-selfsigned.pfx" -Password $Password | Out-Null
    
    Write-Host "✅ Certificat auto-signé créé pour tests" -ForegroundColor Green
    Write-Host "   Certificat: $CertPath" -ForegroundColor Gray
    Write-Host "   PFX: certs/test-selfsigned.pfx" -ForegroundColor Gray
    
} catch {
    Write-Host "⚠️  PowerShell certificat non disponible, création manuelle requise" -ForegroundColor Yellow
}

# 3. Créer variables d'environnement pour Docker Compose
Write-Host "`n3️⃣ Génération fichier .env pour Zero-Trust" -ForegroundColor Magenta

$EnvContent = @"
# Variables d'environnement Zero-Trust - Station Traffeyère
# Généré automatiquement - RNCP 39394

# Base de données PostgreSQL
POSTGRES_PASSWORD=$($Secrets["postgres_password"])
POSTGRES_TDE_KEY=$($Secrets["postgres_tde_key"])

# Keycloak OAuth
KEYCLOAK_DB_PASSWORD=$($Secrets["keycloak_db_password"])
KEYCLOAK_ADMIN_PASSWORD=$($Secrets["keycloak_admin_password"])

# Grafana
GRAFANA_ADMIN_PASSWORD=$($Secrets["grafana_admin_password"])
GRAFANA_OAUTH_SECRET=$($Secrets["grafana_oauth_secret"])

# Redis
REDIS_PASSWORD=$($Secrets["redis_password"])

# IoT Security
LORAWAN_AES_KEY=$($Secrets["lorawan_aes_key"])

# Cloudflare (optionnel pour Let's Encrypt)
CF_API_EMAIL=admin@station-traffeyere.local
CF_DNS_API_TOKEN=your_cloudflare_token_here

# Monitoring
PROMETHEUS_PASSWORD=prometheus2024!
ALERTMANAGER_PASSWORD=alertmanager2024!
"@

$EnvContent | Out-File -FilePath ".env.zerotrust" -Encoding UTF8
Write-Host "✅ Fichier .env.zerotrust créé" -ForegroundColor Green

# 4. Créer configuration Traefik simplifiée
Write-Host "`n4️⃣ Configuration Traefik" -ForegroundColor Magenta

$TraefikConfig = @"
# Configuration Traefik dynamique
# Station Traffeyère Zero-Trust

api:
  dashboard: true
  debug: false

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true

  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: dmz_public

certificatesResolvers:
  letsencrypt:
    acme:
      tlsChallenge: {}
      email: admin@station-traffeyere.local
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

log:
  level: INFO

accessLog:
  bufferingSize: 100

metrics:
  prometheus:
    addEntryPointsLabels: true
    addServicesLabels: true
"@

$TraefikConfig | Out-File -FilePath "security/traefik/traefik.yml" -Encoding UTF8
Write-Host "✅ Configuration Traefik créée" -ForegroundColor Green

# 5. Résumé
Write-Host "`n🎯 INFRASTRUCTURE ZERO-TRUST GÉNÉRÉE" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

Write-Host "`n📋 Éléments créés:" -ForegroundColor Cyan
Write-Host "  ✅ 8 secrets sécurisés" -ForegroundColor Green
Write-Host "  ✅ Certificat auto-signé pour tests" -ForegroundColor Green
Write-Host "  ✅ Fichier .env.zerotrust" -ForegroundColor Green  
Write-Host "  ✅ Configuration Traefik" -ForegroundColor Green

Write-Host "`n🚀 Prochaines étapes:" -ForegroundColor Yellow
Write-Host "  1. Copier .env.zerotrust vers .env" -ForegroundColor White
Write-Host "  2. Déployer: docker-compose -f docker-compose.zerotrust.yml up -d" -ForegroundColor White
Write-Host "  3. Configurer /etc/hosts pour les domaines locaux" -ForegroundColor White

Write-Host "`n🎉 Infrastructure Zero-Trust prête!" -ForegroundColor Green
