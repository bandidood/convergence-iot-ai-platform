#!/bin/bash

# =============================================================================
# DOCKER ENTRYPOINT - EDGE AI ENGINE RNCP 39394
# Expert en Systèmes d'Information et Sécurité
#
# Point d'entrée sécurisé avec gestion des signaux et monitoring
# =============================================================================

set -euo pipefail

# Configuration des couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables d'environnement par défaut
AI_MODEL_PATH=${AI_MODEL_PATH:-/app/models}
AI_LOG_LEVEL=${AI_LOG_LEVEL:-INFO}
AI_METRICS_PORT=${AI_METRICS_PORT:-8080}
AI_PROMETHEUS_PORT=${AI_PROMETHEUS_PORT:-9090}

echo -e "${GREEN}🤖 EDGE AI ENGINE - RNCP 39394 STARTING${NC}"
echo "========================================"

# Fonction de nettoyage pour arrêt propre
cleanup() {
    echo -e "${YELLOW}📋 Arrêt propre du service AI Engine...${NC}"
    
    # Arrêt des processus enfants
    jobs -p | xargs -r kill
    
    # Sauvegarde des modèles si nécessaire
    if [ -f "/app/models/model_state.lock" ]; then
        echo -e "${BLUE}💾 Sauvegarde état des modèles...${NC}"
        python3 -c "
import sys
sys.path.append('/app')
from explainable_ai_engine import ExplainableAIEngine
engine = ExplainableAIEngine()
engine.save_models('$AI_MODEL_PATH')
"
    fi
    
    echo -e "${GREEN}✅ Arrêt terminé${NC}"
    exit 0
}

# Configuration des signaux Unix pour arrêt propre
trap cleanup SIGTERM SIGINT SIGQUIT

# Vérification des permissions et de l'environnement
echo -e "${BLUE}🔍 Vérification environnement...${NC}"

# Vérification répertoires
for dir in "$AI_MODEL_PATH" "/app/logs" "/app/metrics"; do
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}📁 Création répertoire $dir${NC}"
        mkdir -p "$dir"
    fi
done

# Vérification permissions
if [ ! -w "$AI_MODEL_PATH" ]; then
    echo -e "${RED}❌ Permissions insuffisantes sur $AI_MODEL_PATH${NC}"
    exit 1
fi

# Vérification GPU CUDA (optionnel)
if command -v nvidia-smi >/dev/null 2>&1; then
    GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    echo -e "${GREEN}🎮 GPU détecté: $GPU_INFO${NC}"
    
    # Test CUDA
    python3 -c "
import tensorflow as tf
try:
    print(f'TensorFlow version: {tf.__version__}')
    print(f'CUDA available: {tf.test.is_built_with_cuda()}')
    print(f'GPU devices: {len(tf.config.list_physical_devices(\"GPU\"))}')
except Exception as e:
    print(f'GPU test failed: {e}')
" || echo -e "${YELLOW}⚠️  GPU non disponible, utilisation CPU${NC}"
else
    echo -e "${YELLOW}⚠️  NVIDIA GPU non détecté${NC}"
fi

# Vérification des dépendances Python
echo -e "${BLUE}🔍 Vérification dépendances...${NC}"
python3 -c "
import sys
required_modules = ['sklearn', 'numpy', 'pandas']
missing = []

for module in required_modules:
    try:
        __import__(module)
        print(f'✅ {module} disponible')
    except ImportError:
        missing.append(module)
        print(f'❌ {module} manquant')

if missing:
    print(f'Modules manquants: {missing}')
    sys.exit(1)
else:
    print('✅ Toutes les dépendances sont satisfaites')
"

# Configuration logging
echo -e "${BLUE}📋 Configuration logging...${NC}"
export PYTHONUNBUFFERED=1
export TF_CPP_MIN_LOG_LEVEL=2

# Initialisation des métriques Prometheus
echo -e "${BLUE}📊 Initialisation métriques...${NC}"
cat > /app/metrics/health.json << EOF
{
    "service": "edge-ai-engine",
    "status": "starting",
    "timestamp": "$(date -Iseconds)",
    "version": "3.0.0-RNCP39394",
    "performance": {
        "target_latency_ms": 0.28,
        "target_accuracy": 0.976
    }
}
EOF

# Test rapide du modèle AI
echo -e "${BLUE}🧪 Test initialisation AI Engine...${NC}"
python3 -c "
import sys
sys.path.append('/app')

try:
    from demo_ai_engine import DemoAIEngine
    engine = DemoAIEngine()
    print('✅ AI Engine initialisé avec succès')
except Exception as e:
    print(f'❌ Erreur initialisation: {e}')
    sys.exit(1)
" || exit 1

# Affichage de l'état du système
echo -e "${GREEN}📊 État du système:${NC}"
echo "  - CPU: $(nproc) cores"
echo "  - RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  - Disque: $(df -h /app | awk 'NR==2 {print $4}') libre"
echo "  - Python: $(python3 --version)"
echo "  - PID: $$"
echo "  - User: $(whoami)"
echo "  - Workdir: $(pwd)"

# Mise à jour du statut
cat > /app/metrics/health.json << EOF
{
    "service": "edge-ai-engine",
    "status": "ready",
    "timestamp": "$(date -Iseconds)",
    "version": "3.0.0-RNCP39394",
    "pid": $$,
    "ports": {
        "api": $AI_METRICS_PORT,
        "metrics": $AI_PROMETHEUS_PORT
    }
}
EOF

echo -e "${GREEN}🚀 Démarrage AI Engine...${NC}"
echo "========================================"

# Démarrage du service principal avec gestion des signaux
if [ "$1" = "python3" ] && [ "$2" = "explainable_ai_engine.py" ]; then
    # Mode service complet
    echo -e "${GREEN}🎯 Mode service complet${NC}"
    exec "$@" &
    
    # Attente du processus principal avec gestion des signaux
    wait $!
    
elif [ "$1" = "demo" ]; then
    # Mode démonstration
    echo -e "${YELLOW}🔬 Mode démonstration${NC}"
    python3 /app/demo_ai_engine.py
    
elif [ "$1" = "benchmark" ]; then
    # Mode benchmark
    echo -e "${YELLOW}⚡ Mode benchmark performance${NC}"
    python3 -c "
import sys
sys.path.append('/app')
from demo_ai_engine import main
results = main()
print('Benchmark terminé')
"
    
elif [ "$1" = "test" ]; then
    # Mode test
    echo -e "${YELLOW}🧪 Mode test${NC}"
    python3 -m pytest /app/tests/ -v
    
else
    # Mode par défaut - démonstration
    echo -e "${GREEN}🔬 Mode démonstration (défaut)${NC}"
    python3 /app/demo_ai_engine.py
fi

# Nettoyage final
cleanup
