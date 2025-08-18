# Script PKI ultra-simple pour Station Traffeyere Zero-Trust
# Conforme RNCP 39394 - Semaine 5

Write-Host "Generation PKI Zero-Trust - RNCP 39394" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Ajouter System.Web pour la generation de mots de passe
Add-Type -AssemblyName System.Web

# 1. Generer les secrets necessaires
Write-Host "1. Generation des secrets securises" -ForegroundColor Magenta

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
    Write-Host "Secret cree: $SecretName" -ForegroundColor Green
}

# 2. Creer variables d'environnement pour Docker Compose
Write-Host "2. Generation fichier .env pour Zero-Trust" -ForegroundColor Magenta

$EnvLines = @()
$EnvLines += "# Variables d'environnement Zero-Trust - Station Traffeyere"
$EnvLines += "# Genere automatiquement - RNCP 39394"
$EnvLines += ""
$EnvLines += "# Base de donnees PostgreSQL"
$EnvLines += "POSTGRES_PASSWORD=$($Secrets['postgres_password'])"
$EnvLines += "POSTGRES_TDE_KEY=$($Secrets['postgres_tde_key'])"
$EnvLines += ""
$EnvLines += "# Keycloak OAuth"
$EnvLines += "KEYCLOAK_DB_PASSWORD=$($Secrets['keycloak_db_password'])"
$EnvLines += "KEYCLOAK_ADMIN_PASSWORD=$($Secrets['keycloak_admin_password'])"
$EnvLines += ""
$EnvLines += "# Grafana"
$EnvLines += "GRAFANA_ADMIN_PASSWORD=$($Secrets['grafana_admin_password'])"
$EnvLines += "GRAFANA_OAUTH_SECRET=$($Secrets['grafana_oauth_secret'])"
$EnvLines += ""
$EnvLines += "# Redis"
$EnvLines += "REDIS_PASSWORD=$($Secrets['redis_password'])"
$EnvLines += ""
$EnvLines += "# IoT Security"
$EnvLines += "LORAWAN_AES_KEY=$($Secrets['lorawan_aes_key'])"
$EnvLines += ""
$EnvLines += "# Cloudflare (optionnel pour Let's Encrypt)"
$EnvLines += "CF_API_EMAIL=admin@station-traffeyere.local"
$EnvLines += "CF_DNS_API_TOKEN=your_cloudflare_token_here"
$EnvLines += ""
$EnvLines += "# Monitoring"
$EnvLines += "PROMETHEUS_PASSWORD=prometheus2024!"
$EnvLines += "ALERTMANAGER_PASSWORD=alertmanager2024!"

$EnvLines | Out-File -FilePath ".env.zerotrust" -Encoding UTF8
Write-Host "Fichier .env.zerotrust cree" -ForegroundColor Green

# 3. Creer configuration Traefik simplifiee
Write-Host "3. Configuration Traefik" -ForegroundColor Magenta

$TraefikLines = @()
$TraefikLines += "# Configuration Traefik dynamique"
$TraefikLines += "# Station Traffeyere Zero-Trust"
$TraefikLines += ""
$TraefikLines += "api:"
$TraefikLines += "  dashboard: true"
$TraefikLines += "  debug: false"
$TraefikLines += ""
$TraefikLines += "entryPoints:"
$TraefikLines += "  web:"
$TraefikLines += "    address: ':80'"
$TraefikLines += "  websecure:"
$TraefikLines += "    address: ':443'"
$TraefikLines += ""
$TraefikLines += "providers:"
$TraefikLines += "  docker:"
$TraefikLines += "    endpoint: 'unix:///var/run/docker.sock'"
$TraefikLines += "    exposedByDefault: false"
$TraefikLines += "    network: dmz_public"
$TraefikLines += ""
$TraefikLines += "log:"
$TraefikLines += "  level: INFO"
$TraefikLines += ""
$TraefikLines += "metrics:"
$TraefikLines += "  prometheus:"
$TraefikLines += "    addEntryPointsLabels: true"
$TraefikLines += "    addServicesLabels: true"

$TraefikLines | Out-File -FilePath "security/traefik/traefik.yml" -Encoding UTF8
Write-Host "Configuration Traefik creee" -ForegroundColor Green

# 4. Resume
Write-Host "INFRASTRUCTURE ZERO-TRUST GENEREE" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

Write-Host "Elements crees:" -ForegroundColor Cyan
Write-Host "  - 8 secrets securises" -ForegroundColor Green
Write-Host "  - Fichier .env.zerotrust" -ForegroundColor Green  
Write-Host "  - Configuration Traefik" -ForegroundColor Green

Write-Host "Prochaines etapes:" -ForegroundColor Yellow
Write-Host "  1. Copier .env.zerotrust vers .env" -ForegroundColor White
Write-Host "  2. Deployer: docker-compose -f docker-compose.zerotrust.yml up -d" -ForegroundColor White
Write-Host "  3. Configurer /etc/hosts pour les domaines locaux" -ForegroundColor White

Write-Host "Infrastructure Zero-Trust prete!" -ForegroundColor Green
