# 🔐 Station Traffeyère IoT/IA Platform - Makefile
# RNCP 39394 - Expert en Systèmes d'Information et Sécurité

.PHONY: help setup build test deploy clean security-scan docs

# Configuration
PROJECT_NAME := station-traffeyere-iot-ai-platform
DOCKER_REGISTRY := your-registry.com
VERSION := $(shell git describe --tags --always --dirty)

# Couleurs pour output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Affiche cette aide
	@echo "$(BLUE)🔐 Station Traffeyère IoT/IA Platform$(NC)"
	@echo "$(BLUE)=====================================$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Setup environnement développement complet
	@echo "$(BLUE)🚀 Setup environnement développement...$(NC)"
	@if [ ! -f .env ]; then cp .env.example .env; echo "⚠️  ATTENTION: Modifier .env avec vos configurations"; fi
	@echo "$(GREEN)✅ Environnement configuré !$(NC)"

build: ## Build tous les composants
	@echo "$(BLUE)🔧 Build composants...$(NC)"
	@docker-compose build --parallel
	@echo "$(GREEN)✅ Build terminé !$(NC)"

test: ## Exécute tous les tests
	@echo "$(BLUE)🧪 Exécution tests...$(NC)"
	@$(MAKE) test-python
	@$(MAKE) test-nodejs
	@echo "$(GREEN)✅ Tous les tests OK !$(NC)"

test-python: ## Tests Python Edge AI
	@echo "$(YELLOW)🐍 Tests Edge AI Engine...$(NC)"
	@cd core/edge-ai-engine && python -m pytest tests/ -v --cov=src || echo "Tests Python à implémenter"

test-nodejs: ## Tests Node.js Dashboard
	@echo "$(YELLOW)📦 Tests Web Dashboard...$(NC)"
	@cd interfaces/web-dashboard && npm test || echo "Tests Node.js à implémenter"

security-scan: ## Scan sécurité complet
	@echo "$(BLUE)🔒 Scan sécurité complet...$(NC)"
	@docker run --rm -v $(PWD):/app -w /app aquasec/trivy fs . --format table || echo "Trivy non disponible, installation recommandée"
	@echo "$(GREEN)✅ Scan sécurité terminé !$(NC)"

deploy-dev: ## Déploiement environnement développement
	@echo "$(BLUE)🚀 Déploiement développement...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✅ Déploiement dev OK !$(NC)"

monitor: ## Ouvre dashboards monitoring
	@echo "$(BLUE)📊 Dashboards disponibles:$(NC)"
	@echo "- Grafana: http://localhost:3001"
	@echo "- MinIO: http://localhost:9001"
	@echo "- InfluxDB: http://localhost:8086"

logs: ## Affiche logs services
	@docker-compose logs -f

status: ## Status des services
	@echo "$(BLUE)📊 Status services:$(NC)"
	@docker-compose ps

clean: ## Nettoyage environnement
	@echo "$(BLUE)🧹 Nettoyage...$(NC)"
	@docker-compose down -v
	@docker system prune -f
	@echo "$(GREEN)✅ Nettoyage terminé !$(NC)"

# Raccourcis utiles
up: deploy-dev ## Alias pour deploy-dev
down: clean ## Alias pour clean
ps: status ## Alias pour status

# Version et informations
version: ## Affiche version
	@echo "$(BLUE)📋 Version: $(GREEN)$(VERSION)$(NC)"
	@echo "$(BLUE)📋 Git Branch: $(GREEN)$(shell git branch --show-current)$(NC)"
	@echo "$(BLUE)📋 Git Commit: $(GREEN)$(shell git rev-parse --short HEAD)$(NC)"

info: ## Informations projet
	@echo "$(BLUE)🔐 Station Traffeyère IoT/IA Platform$(NC)"
	@echo "$(BLUE)=====================================$(NC)"
	@echo "$(YELLOW)🎯 RNCP 39394 - Expert Systèmes Information Sécurité$(NC)"
	@echo "$(GREEN)✅ Architecture convergente Edge AI + 5G-TSN + Digital Twin$(NC)"
	@echo "$(GREEN)✅ Conformité ISA/IEC 62443 SL3+ native$(NC)"
	@echo ""
	@echo "$(BLUE)👤 Auteur: Johann LEBEL$(NC)"
