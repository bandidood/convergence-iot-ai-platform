#!/bin/bash

# =============================================================================
# SCRIPT DE VÉRIFICATION EXIGENCES SYSTÈME - RNCP 39394
# Expert en Systèmes d'Information et Sécurité
# =============================================================================

set -euo pipefail

# Configuration des couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Exigences système selon le plan technique
MIN_RAM_GB=32
MIN_DISK_GB=500
MIN_CPU_CORES=8
REQUIRED_GPU="RTX 3060"

echo -e "${GREEN}🔧 VALIDATION EXIGENCES SYSTÈME RNCP 39394${NC}"
echo "=================================================="

# Fonction d'affichage des résultats
check_requirement() {
    local description=$1
    local current_value=$2
    local required_value=$3
    local status=$4
    
    if [[ $status == "OK" ]]; then
        echo -e "${GREEN}✅ $description: $current_value (requis: $required_value)${NC}"
        return 0
    else
        echo -e "${RED}❌ $description: $current_value (requis: $required_value)${NC}"
        return 1
    fi
}

# Variables pour le tracking des erreurs
ERRORS=0

# 1. Vérification RAM
echo -e "\n${YELLOW}🔍 Vérification RAM...${NC}"
if command -v free >/dev/null 2>&1; then
    TOTAL_RAM_KB=$(free -k | awk '/^Mem:/{print $2}')
    TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
elif [[ "$OSTYPE" == "darwin"* ]]; then
    TOTAL_RAM_BYTES=$(sysctl -n hw.memsize)
    TOTAL_RAM_GB=$((TOTAL_RAM_BYTES / 1024 / 1024 / 1024))
else
    echo -e "${RED}❌ Impossible de détecter la RAM système${NC}"
    TOTAL_RAM_GB=0
fi

if [[ $TOTAL_RAM_GB -ge $MIN_RAM_GB ]]; then
    check_requirement "RAM Système" "${TOTAL_RAM_GB}GB" "${MIN_RAM_GB}GB" "OK"
else
    check_requirement "RAM Système" "${TOTAL_RAM_GB}GB" "${MIN_RAM_GB}GB" "FAIL"
    ((ERRORS++))
fi

# 2. Vérification CPU
echo -e "\n${YELLOW}🔍 Vérification CPU...${NC}"
if command -v nproc >/dev/null 2>&1; then
    CPU_CORES=$(nproc)
elif [[ "$OSTYPE" == "darwin"* ]]; then
    CPU_CORES=$(sysctl -n hw.ncpu)
else
    CPU_CORES=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || echo "0")
fi

if [[ $CPU_CORES -ge $MIN_CPU_CORES ]]; then
    check_requirement "CPU Cores" "$CPU_CORES" "$MIN_CPU_CORES" "OK"
else
    check_requirement "CPU Cores" "$CPU_CORES" "$MIN_CPU_CORES" "FAIL"
    ((ERRORS++))
fi

# 3. Vérification espace disque
echo -e "\n${YELLOW}🔍 Vérification espace disque...${NC}"
CURRENT_DIR=$(pwd)
if command -v df >/dev/null 2>&1; then
    AVAILABLE_SPACE_KB=$(df "$CURRENT_DIR" | awk 'NR==2 {print $4}')
    AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE_KB / 1024 / 1024))
else
    echo -e "${RED}❌ Impossible de vérifier l'espace disque${NC}"
    AVAILABLE_SPACE_GB=0
fi

if [[ $AVAILABLE_SPACE_GB -ge $MIN_DISK_GB ]]; then
    check_requirement "Espace Disque" "${AVAILABLE_SPACE_GB}GB" "${MIN_DISK_GB}GB" "OK"
else
    check_requirement "Espace Disque" "${AVAILABLE_SPACE_GB}GB" "${MIN_DISK_GB}GB" "FAIL"
    ((ERRORS++))
fi

# 4. Vérification GPU (optionnelle mais recommandée)
echo -e "\n${YELLOW}🔍 Vérification GPU...${NC}"
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    if [[ -n "$GPU_INFO" ]]; then
        if [[ "$GPU_INFO" == *"RTX 3060"* ]] || [[ "$GPU_INFO" == *"RTX 30"* ]] || [[ "$GPU_INFO" == *"RTX 40"* ]]; then
            check_requirement "GPU Compatible" "$GPU_INFO" "$REQUIRED_GPU" "OK"
        else
            echo -e "${YELLOW}⚠️  GPU Détecté: $GPU_INFO (recommandé: $REQUIRED_GPU)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Aucun GPU NVIDIA détecté (optionnel pour développement)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  nvidia-smi non trouvé - GPU NVIDIA non détecté${NC}"
fi

# 5. Vérification Docker
echo -e "\n${YELLOW}🔍 Vérification Docker...${NC}"
if command -v docker >/dev/null 2>&1; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${GREEN}✅ Docker installé: version $DOCKER_VERSION${NC}"
    
    # Vérification que Docker fonctionne
    if docker info >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker daemon opérationnel${NC}"
    else
        echo -e "${RED}❌ Docker daemon non accessible${NC}"
        ((ERRORS++))
    fi
else
    echo -e "${RED}❌ Docker non installé${NC}"
    ((ERRORS++))
fi

# 6. Vérification Docker Compose
echo -e "\n${YELLOW}🔍 Vérification Docker Compose...${NC}"
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${GREEN}✅ Docker Compose installé: version $COMPOSE_VERSION${NC}"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version --short)
    echo -e "${GREEN}✅ Docker Compose (plugin) installé: version $COMPOSE_VERSION${NC}"
else
    echo -e "${RED}❌ Docker Compose non installé${NC}"
    ((ERRORS++))
fi

# 7. Vérification outils de développement
echo -e "\n${YELLOW}🔍 Vérification outils développement...${NC}"

# Python 3.11+
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 11 ]]; then
        echo -e "${GREEN}✅ Python: version $PYTHON_VERSION${NC}"
    else
        echo -e "${YELLOW}⚠️  Python: version $PYTHON_VERSION (recommandé 3.11+)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Python 3 non trouvé${NC}"
fi

# Node.js
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js installé: $NODE_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  Node.js non trouvé${NC}"
fi

# Résumé final
echo -e "\n=================================================="
if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}🎉 SYSTÈME COMPATIBLE - TOUTES EXIGENCES SATISFAITES${NC}"
    echo -e "${GREEN}✅ Prêt pour le déploiement de l'infrastructure sécurisée${NC}"
    exit 0
else
    echo -e "${RED}⚠️  $ERRORS EXIGENCE(S) NON SATISFAITE(S)${NC}"
    echo -e "${RED}❌ Veuillez corriger les problèmes avant de continuer${NC}"
    exit 1
fi
