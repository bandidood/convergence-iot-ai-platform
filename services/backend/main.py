# =============================================================================
# MAIN FASTAPI APPLICATION - Station Traffeyère IoT/AI Platform
# Backend API pour la gestion IoT, IA et monitoring - RNCP 39394
# =============================================================================

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import logging
from datetime import datetime
from typing import Dict, Any
import sys
import traceback

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration de l'application
PROJECT_NAME = os.getenv("PROJECT_NAME", "Station Traffeyère IoT/AI Platform")
PROJECT_VERSION = os.getenv("PROJECT_VERSION", "1.0.0")
RNCP_CODE = os.getenv("RNCP_CODE", "39394")
ENVIRONMENT = os.getenv("FASTAPI_ENV", "production")
DEBUG = os.getenv("FASTAPI_DEBUG", "false").lower() == "true"

# Gestionnaire de contexte pour le cycle de vie de l'app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire du cycle de vie de l'application"""
    # Démarrage
    logger.info("🚀 Démarrage de l'application FastAPI")
    logger.info(f"📊 Projet: {PROJECT_NAME}")
    logger.info(f"🎓 RNCP: {RNCP_CODE}")
    logger.info(f"🏷️ Version: {PROJECT_VERSION}")
    logger.info(f"🌍 Environment: {ENVIRONMENT}")
    
    try:
        # Ici vous pourriez ajouter:
        # - Connexion aux bases de données
        # - Initialisation des services externes
        # - Chargement des modèles IA
        # - Configuration des connexions MQTT/InfluxDB
        logger.info("✅ Initialisation terminée")
        yield
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        logger.error(traceback.format_exc())
        raise
    finally:
        # Nettoyage
        logger.info("🛑 Arrêt gracieux de l'application")

# Création de l'application FastAPI
app = FastAPI(
    title=PROJECT_NAME,
    description=f"""
    🏭 **API Backend pour la Station Traffeyère IoT/AI Platform**
    
    ## 🎯 Objectifs RNCP {RNCP_CODE}
    
    Cette API fait partie d'un projet de validation des compétences 
    **Expert en Systèmes d'Information et Sécurité**.
    
    ## 🏗️ Architecture
    
    - **IoT Data Management**: Collecte et traitement des données capteurs
    - **Edge AI Engine**: Détection d'anomalies en temps réel
    - **Digital Twin Integration**: Synchronisation avec le jumeau numérique
    - **Blockchain Compliance**: Traçabilité et conformité réglementaire
    - **SIEM Integration**: Monitoring de sécurité avancé
    
    ## 🔒 Sécurité
    
    - Architecture Zero Trust
    - Chiffrement bout-en-bout
    - Conformité ISA/IEC 62443 SL3+
    - Audit trail complet
    
    """,
    version=PROJECT_VERSION,
    docs_url="/docs" if DEBUG else "/docs",
    redoc_url="/redoc" if DEBUG else "/redoc",
    lifespan=lifespan,
    debug=DEBUG
)

# Configuration CORS pour les environnements de développement
if ENVIRONMENT == "development" or DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # À restreindre en production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Configuration CORS restrictive pour la production
    allowed_origins = [
        "https://traffeyere.ccdigital.fr",
        "https://app.traffeyere.ccdigital.fr",
        "https://www.traffeyere.ccdigital.fr",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

# Middleware de sécurité - Trusted Host
if ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "api.traffeyere.ccdigital.fr",
            "traffeyere.ccdigital.fr",
            "localhost",  # Pour les health checks internes
            "127.0.0.1"   # Pour les health checks internes
        ]
    )

# Middleware de logging des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware de logging des requêtes"""
    start_time = datetime.utcnow()
    
    # Log de la requête entrante
    logger.info(f"📥 {request.method} {request.url} - IP: {request.client.host}")
    
    try:
        response = await call_next(request)
        
        # Calcul du temps de traitement
        process_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log de la réponse
        logger.info(f"📤 {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        # Ajout du header de temps de traitement
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # Log des erreurs
        process_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"❌ {request.method} {request.url} - Error: {str(e)} - Time: {process_time:.3f}s")
        logger.error(traceback.format_exc())
        
        # Retourner une réponse d'erreur générique
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "Une erreur inattendue s'est produite",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url),
                "method": request.method
            },
            headers={"X-Process-Time": str(process_time)}
        )

# =============================================================================
# ROUTES DE BASE - Health Checks et Information
# =============================================================================

@app.get("/")
async def root():
    """Point d'entrée principal de l'API"""
    return {
        "message": f"Bienvenue sur {PROJECT_NAME}",
        "version": PROJECT_VERSION,
        "rncp_code": RNCP_CODE,
        "environment": ENVIRONMENT,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "project": {
            "name": "Station de Traitement des Eaux IoT/AI",
            "location": "Saint-Quentin-Fallavier, France",
            "coordinates": "45.764043,4.835659",
            "description": "Plateforme IoT/IA convergente pour la transformation digitale des infrastructures critiques"
        }
    }

@app.get("/health")
@app.head("/health")
@app.get("/healthz")
@app.head("/healthz")
async def health_check():
    """Health check pour les orchestrateurs (Kubernetes, Docker, etc.)"""
    try:
        # Ici vous pourriez ajouter des vérifications:
        # - Connexion base de données
        # - Connexion Redis
        # - Connexion InfluxDB
        # - État des services externes
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": PROJECT_VERSION,
            "environment": ENVIRONMENT,
            "services": {
                "api": "operational",
                "database": "checking",  # À implémenter
                "redis": "checking",     # À implémenter
                "influxdb": "checking",  # À implémenter
                "mqtt": "checking"       # À implémenter
            },
            "system": {
                "python_version": sys.version,
                "fastapi_version": "0.104.0"  # À récupérer dynamiquement
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/info")
async def app_info():
    """Informations détaillées sur l'application"""
    return {
        "project": {
            "name": PROJECT_NAME,
            "version": PROJECT_VERSION,
            "rncp_code": RNCP_CODE,
            "description": "API Backend pour plateforme IoT/IA convergente"
        },
        "technical_stack": {
            "framework": "FastAPI",
            "language": "Python 3.11+",
            "database": "PostgreSQL + TimescaleDB",
            "cache": "Redis",
            "timeseries": "InfluxDB",
            "messaging": "MQTT (Eclipse Mosquitto)",
            "monitoring": "Prometheus + Grafana"
        },
        "architecture": {
            "pattern": "Microservices",
            "deployment": "Docker + Kubernetes",
            "security": "Zero Trust",
            "compliance": "ISA/IEC 62443 SL3+"
        },
        "environment": {
            "current": ENVIRONMENT,
            "debug": DEBUG,
            "timestamp": datetime.utcnow().isoformat()
        },
        "rncp_validation": {
            "code": RNCP_CODE,
            "title": "Expert en Systèmes d'Information et Sécurité",
            "competencies_covered": [
                "Bloc 3: Cybersécurité et conformité",
                "Bloc 4: Innovation IoT et IA",
                "Architecture cloud-native",
                "DevSecOps et automatisation"
            ]
        }
    }

@app.get("/metrics")
async def metrics():
    """Métriques pour Prometheus (format basique)"""
    # À implémenter avec prometheus_client
    return {
        "http_requests_total": 0,
        "http_request_duration_seconds": 0.0,
        "system_cpu_usage": 0.0,
        "system_memory_usage": 0.0,
        "active_connections": 0,
        "timestamp": datetime.utcnow().isoformat()
    }

# =============================================================================
# ROUTES IoT ET DONNÉES CAPTEURS (Exemples pour validation)
# =============================================================================

@app.get("/api/v1/sensors")
async def get_sensors():
    """Liste des capteurs de la station"""
    return {
        "sensors": [
            {
                "id": "PH_001",
                "name": "pH Mètre Principal",
                "type": "ph",
                "unit": "pH",
                "location": "Bassin d'aération",
                "status": "active",
                "last_reading": 7.2,
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "id": "O2_001", 
                "name": "Oxymètre Dissous",
                "type": "oxygen",
                "unit": "mg/L",
                "location": "Bassin d'aération",
                "status": "active",
                "last_reading": 4.5,
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "id": "TURB_001",
                "name": "Turbidimètre",
                "type": "turbidity",
                "unit": "NTU",
                "location": "Sortie clarificateur",
                "status": "active",
                "last_reading": 15.2,
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "id": "FLOW_001",
                "name": "Débitmètre Principal",
                "type": "flow",
                "unit": "m³/h",
                "location": "Entrée station",
                "status": "active",
                "last_reading": 2400,
                "timestamp": datetime.utcnow().isoformat()
            }
        ],
        "total": 4,
        "active": 4,
        "station": {
            "id": "TRAFFEYERE_001",
            "name": "Station Traffeyère",
            "location": "45.764043,4.835659"
        }
    }

@app.get("/api/v1/anomalies")
async def get_anomalies():
    """Détection d'anomalies par IA Edge"""
    return {
        "anomalies": [
            {
                "id": "ANOM_001",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "medium",
                "type": "sensor_drift",
                "sensor_id": "PH_001",
                "description": "Dérive graduelle du pH détectée",
                "confidence": 0.87,
                "ai_model": "IsolationForest",
                "edge_latency_ms": 0.28,
                "recommended_action": "Calibration capteur pH recommandée"
            }
        ],
        "summary": {
            "total_today": 3,
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 0
        },
        "ai_performance": {
            "model_accuracy": 0.976,
            "avg_latency_ms": 0.32,
            "false_positive_rate": 0.024
        }
    }

# =============================================================================
# GESTION D'ERREURS GLOBALE
# =============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Gestionnaire d'erreur 404 personnalisé"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Resource Not Found",
            "message": "La ressource demandée n'existe pas",
            "path": str(request.url),
            "method": request.method,
            "timestamp": datetime.utcnow().isoformat(),
            "suggestion": "Consultez la documentation API à /docs"
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Gestionnaire d'erreur 500 personnalisé"""
    logger.error(f"Internal server error: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Une erreur interne s'est produite",
            "path": str(request.url),
            "method": request.method,
            "timestamp": datetime.utcnow().isoformat(),
            "support": "Contactez l'administrateur système"
        }
    )

# =============================================================================
# POINT D'ENTRÉE POUR DÉVELOPPEMENT LOCAL
# =============================================================================

if __name__ == "__main__":
    # Configuration pour développement local uniquement
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )