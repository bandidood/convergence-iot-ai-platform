#!/usr/bin/env python3
"""
Station Traffeyère Digital Twin API Server
RNCP 39394 - Serveur API REST/WebSocket pour Unity Digital Twin
Conformité ISA/IEC 62443 SL3+ avec authentification robuste
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import aioredis
import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn
from cryptography.fernet import Fernet
import jwt
import bcrypt

# =====================================================================================
# CONFIGURATION
# =====================================================================================

# Configuration logging sécurisé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/digital-twin-api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration environnement
class Config:
    MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'mqtt-broker')
    MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    API_PORT = int(os.getenv('API_PORT', 8080))
    
    # Sécurité JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'station-traffeyere-secret-key-2024')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    
    # Chiffrement données sensibles
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())

config = Config()

# =====================================================================================
# MODÈLES DE DONNÉES
# =====================================================================================

@dataclass
class SensorData:
    sensor_id: str
    sensor_type: str
    zone: str
    value: float
    unit: str
    status: str
    timestamp: datetime
    alert_level: str = "normal"
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class CameraCommand(BaseModel):
    command_type: str = Field(..., description="Type de commande caméra")
    target_sensor: Optional[str] = Field(None, description="ID capteur cible")
    zone: Optional[str] = Field(None, description="Zone cible")
    preset: Optional[str] = Field(None, description="Preset caméra")
    zoom_level: Optional[float] = Field(None, description="Niveau de zoom")
    
class VoiceCommand(BaseModel):
    command: str = Field(..., description="Commande vocale")
    confidence: float = Field(..., description="Niveau de confiance")
    user_id: str = Field(..., description="ID utilisateur")

class AuthRequest(BaseModel):
    username: str
    password: str

# =====================================================================================
# GESTIONNAIRE DE SÉCURITÉ
# =====================================================================================

class SecurityManager:
    def __init__(self):
        self.fernet = Fernet(config.ENCRYPTION_KEY)
        self.security = HTTPBearer()
        
    def hash_password(self, password: str) -> str:
        """Hash sécurisé du mot de passe"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Vérification mot de passe"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_jwt_token(self, user_id: str, username: str) -> str:
        """Création token JWT"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow(),
            'iss': 'station-traffeyere-dt'
        }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    
    def verify_jwt_token(self, token: str) -> Dict:
        """Vérification token JWT"""
        try:
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expiré")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token invalide")
    
    def encrypt_data(self, data: str) -> str:
        """Chiffrement données sensibles"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Déchiffrement données sensibles"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

security_manager = SecurityManager()

# =====================================================================================
# GESTIONNAIRE DE DONNÉES
# =====================================================================================

class DataManager:
    def __init__(self):
        self.sensors_cache: Dict[str, SensorData] = {}
        self.redis_client: Optional[aioredis.Redis] = None
        self.mqtt_client: Optional[mqtt.Client] = None
        self.connected_websockets: List[WebSocket] = []
        
    async def initialize(self):
        """Initialisation des connexions"""
        try:
            # Connexion Redis
            self.redis_client = aioredis.from_url(
                f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✓ Connexion Redis établie")
            
            # Connexion MQTT
            await self.setup_mqtt()
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation DataManager: {e}")
            raise
    
    async def setup_mqtt(self):
        """Configuration MQTT avec sécurité"""
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info("✓ Connexion MQTT établie")
                # Abonnement à tous les capteurs
                client.subscribe("station/sensors/+/data")
                client.subscribe("station/alerts/+")
            else:
                logger.error(f"❌ Erreur connexion MQTT: {rc}")
        
        def on_message(client, userdata, msg):
            try:
                topic_parts = msg.topic.split('/')
                if len(topic_parts) >= 3:
                    sensor_id = topic_parts[2]
                    data = json.loads(msg.payload.decode())
                    asyncio.create_task(self.process_sensor_data(sensor_id, data))
            except Exception as e:
                logger.error(f"❌ Erreur traitement message MQTT: {e}")
        
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
        
        try:
            self.mqtt_client.connect(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"❌ Erreur connexion MQTT: {e}")
    
    async def process_sensor_data(self, sensor_id: str, data: Dict):
        """Traitement données capteur en temps réel"""
        try:
            sensor_data = SensorData(
                sensor_id=sensor_id,
                sensor_type=data.get('type', 'unknown'),
                zone=data.get('zone', 'default'),
                value=float(data.get('value', 0)),
                unit=data.get('unit', ''),
                status=data.get('status', 'unknown'),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                alert_level=data.get('alert_level', 'normal')
            )
            
            # Cache local
            self.sensors_cache[sensor_id] = sensor_data
            
            # Cache Redis avec expiration
            await self.redis_client.setex(
                f"sensor:{sensor_id}",
                300,  # 5 minutes
                json.dumps(sensor_data.to_dict())
            )
            
            # Diffusion WebSocket
            await self.broadcast_sensor_update(sensor_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement capteur {sensor_id}: {e}")
    
    async def broadcast_sensor_update(self, sensor_data: SensorData):
        """Diffusion mise à jour capteur via WebSocket"""
        message = {
            'type': 'sensor_update',
            'data': sensor_data.to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Suppression des connexions fermées
        active_websockets = []
        for ws in self.connected_websockets:
            try:
                await ws.send_json(message)
                active_websockets.append(ws)
            except Exception:
                pass  # Connexion fermée
        
        self.connected_websockets = active_websockets
    
    async def get_all_sensors(self) -> List[Dict]:
        """Récupération de tous les capteurs"""
        return [sensor.to_dict() for sensor in self.sensors_cache.values()]
    
    async def get_sensor_by_id(self, sensor_id: str) -> Optional[Dict]:
        """Récupération capteur par ID"""
        if sensor_id in self.sensors_cache:
            return self.sensors_cache[sensor_id].to_dict()
        
        # Fallback Redis
        try:
            cached_data = await self.redis_client.get(f"sensor:{sensor_id}")
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"❌ Erreur récupération capteur {sensor_id}: {e}")
        
        return None
    
    async def send_voice_command(self, command: VoiceCommand) -> bool:
        """Envoi commande vocale vers Unity"""
        try:
            message = {
                'type': 'voice_command',
                'command': command.command,
                'confidence': command.confidence,
                'user_id': command.user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Publication MQTT vers Unity
            if self.mqtt_client:
                self.mqtt_client.publish(
                    "station/unity/voice_commands",
                    json.dumps(message)
                )
            
            # Stockage Redis pour historique
            await self.redis_client.lpush(
                f"voice_commands:{command.user_id}",
                json.dumps(message)
            )
            await self.redis_client.ltrim(f"voice_commands:{command.user_id}", 0, 99)  # Garder 100 derniers
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur envoi commande vocale: {e}")
            return False

data_manager = DataManager()

# =====================================================================================
# APPLICATION FASTAPI
# =====================================================================================

app = FastAPI(
    title="Station Traffeyère Digital Twin API",
    description="API REST/WebSocket pour le jumeau numérique de la station de traitement d'eau",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS pour développement (à restreindre en production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production: liste spécifique
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================================
# MIDDLEWARES D'AUTHENTIFICATION
# =====================================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_manager.security)):
    """Middleware d'authentification JWT"""
    try:
        payload = security_manager.verify_jwt_token(credentials.credentials)
        return payload
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token d'authentification invalide",
            headers={"WWW-Authenticate": "Bearer"}
        )

# =====================================================================================
# ROUTES D'AUTHENTIFICATION
# =====================================================================================

@app.post("/auth/login", tags=["Authentification"])
async def login(auth_request: AuthRequest):
    """Authentification utilisateur avec JWT"""
    # Validation simple pour la démo (en production: base de données)
    valid_users = {
        "admin": security_manager.hash_password("admin123"),
        "operator": security_manager.hash_password("operator123"),
        "viewer": security_manager.hash_password("viewer123")
    }
    
    if (auth_request.username in valid_users and 
        security_manager.verify_password(auth_request.password, valid_users[auth_request.username])):
        
        token = security_manager.create_jwt_token(
            user_id=f"user_{hash(auth_request.username)}",
            username=auth_request.username
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": config.JWT_EXPIRATION_HOURS * 3600,
            "user": {
                "username": auth_request.username,
                "role": auth_request.username  # Simplification pour la démo
            }
        }
    else:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

@app.get("/auth/verify", tags=["Authentification"])
async def verify_token(current_user: Dict = Depends(get_current_user)):
    """Vérification validité token"""
    return {
        "valid": True,
        "user": current_user,
        "expires": current_user.get('exp')
    }

# =====================================================================================
# ROUTES API CAPTEURS
# =====================================================================================

@app.get("/api/sensors", tags=["Capteurs"])
async def get_sensors(current_user: Dict = Depends(get_current_user)):
    """Récupération liste des capteurs"""
    try:
        sensors = await data_manager.get_all_sensors()
        return {
            "success": True,
            "count": len(sensors),
            "data": sensors,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erreur récupération capteurs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensors/{sensor_id}", tags=["Capteurs"])
async def get_sensor(sensor_id: str, current_user: Dict = Depends(get_current_user)):
    """Récupération capteur spécifique"""
    sensor = await data_manager.get_sensor_by_id(sensor_id)
    if sensor:
        return {
            "success": True,
            "data": sensor,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail=f"Capteur {sensor_id} non trouvé")

@app.get("/api/sensors/zone/{zone}", tags=["Capteurs"])
async def get_sensors_by_zone(zone: str, current_user: Dict = Depends(get_current_user)):
    """Récupération capteurs par zone"""
    all_sensors = await data_manager.get_all_sensors()
    zone_sensors = [s for s in all_sensors if s.get('zone') == zone]
    
    return {
        "success": True,
        "zone": zone,
        "count": len(zone_sensors),
        "data": zone_sensors,
        "timestamp": datetime.now().isoformat()
    }

# =====================================================================================
# ROUTES API COMMANDES
# =====================================================================================

@app.post("/api/camera/command", tags=["Contrôle"])
async def send_camera_command(command: CameraCommand, current_user: Dict = Depends(get_current_user)):
    """Envoi commande caméra vers Unity"""
    try:
        message = {
            'type': 'camera_command',
            'data': command.dict(),
            'user_id': current_user.get('user_id'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Publication MQTT
        if data_manager.mqtt_client:
            data_manager.mqtt_client.publish(
                "station/unity/camera_commands",
                json.dumps(message)
            )
        
        return {
            "success": True,
            "message": "Commande caméra envoyée",
            "command": command.dict()
        }
    except Exception as e:
        logger.error(f"❌ Erreur commande caméra: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/command", tags=["Contrôle"])
async def send_voice_command(command: VoiceCommand, current_user: Dict = Depends(get_current_user)):
    """Traitement commande vocale"""
    try:
        success = await data_manager.send_voice_command(command)
        if success:
            return {
                "success": True,
                "message": "Commande vocale traitée",
                "command": command.dict()
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur traitement commande vocale")
    except Exception as e:
        logger.error(f"❌ Erreur commande vocale: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================================
# ROUTES SYSTÈME
# =====================================================================================

@app.get("/health", tags=["Système"])
async def health_check():
    """Contrôle santé du système"""
    try:
        # Test Redis
        redis_ok = False
        if data_manager.redis_client:
            await data_manager.redis_client.ping()
            redis_ok = True
        
        # Test MQTT
        mqtt_ok = data_manager.mqtt_client and data_manager.mqtt_client.is_connected()
        
        return {
            "status": "healthy" if redis_ok and mqtt_ok else "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "2.1.0",
            "components": {
                "redis": "ok" if redis_ok else "error",
                "mqtt": "ok" if mqtt_ok else "error",
                "sensors_cache": len(data_manager.sensors_cache),
                "websocket_connections": len(data_manager.connected_websockets)
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/metrics", tags=["Système"])
async def get_metrics(current_user: Dict = Depends(get_current_user)):
    """Métriques système pour monitoring"""
    return {
        "sensors": {
            "total": len(data_manager.sensors_cache),
            "by_status": {},  # TODO: calculer par statut
            "by_zone": {}     # TODO: calculer par zone
        },
        "connections": {
            "websockets": len(data_manager.connected_websockets),
            "mqtt": data_manager.mqtt_client.is_connected() if data_manager.mqtt_client else False
        },
        "timestamp": datetime.now().isoformat()
    }

# =====================================================================================
# WEBSOCKET TEMPS RÉEL
# =====================================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour données temps réel"""
    await websocket.accept()
    data_manager.connected_websockets.append(websocket)
    
    try:
        while True:
            # Garder la connexion active
            message = await websocket.receive_text()
            
            # Echo pour test connectivité
            if message == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                
    except WebSocketDisconnect:
        if websocket in data_manager.connected_websockets:
            data_manager.connected_websockets.remove(websocket)
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket: {e}")
        if websocket in data_manager.connected_websockets:
            data_manager.connected_websockets.remove(websocket)

# =====================================================================================
# ÉVÉNEMENTS STARTUP/SHUTDOWN
# =====================================================================================

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    logger.info("🚀 Démarrage Station Traffeyère Digital Twin API")
    try:
        await data_manager.initialize()
        logger.info("✅ API prête - RNCP 39394 - Station Traffeyère")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation: {e}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage à l'arrêt"""
    logger.info("🛑 Arrêt Station Traffeyère Digital Twin API")
    
    # Fermeture MQTT
    if data_manager.mqtt_client:
        data_manager.mqtt_client.loop_stop()
        data_manager.mqtt_client.disconnect()
    
    # Fermeture Redis
    if data_manager.redis_client:
        await data_manager.redis_client.close()

# =====================================================================================
# POINT D'ENTRÉE
# =====================================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.API_PORT,
        log_level="info",
        reload=False  # Production
    )
