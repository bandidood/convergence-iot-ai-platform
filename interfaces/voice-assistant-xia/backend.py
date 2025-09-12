#!/usr/bin/env python3
"""
Backend XAI avec intégration MQTT et données IoT temps réel
Station Traffeyère IoT AI Platform - RNCP 39394
"""

import os
import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import paho.mqtt.client as mqtt
import redis
import requests
from threading import Thread, Lock

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SensorReading:
    """Lecture capteur IoT"""
    sensor_id: str
    value: float
    unit: str
    timestamp: datetime
    quality: float = 100.0
    status: str = "online"

@dataclass  
class AnalyticsResult:
    """Résultat analyse Edge AI"""
    sensor_id: str
    anomaly_score: float
    prediction: float
    confidence: float
    explanation: str
    timestamp: datetime

class XAIBackend:
    """Backend XAI avec intégration IoT temps réel"""
    
    def __init__(self):
        # Configuration
        self.mqtt_broker = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_BROKER_PORT', '1883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME', 'station_mqtt')
        self.mqtt_password = os.getenv('MQTT_PASSWORD', 'mqtt_secure_2024')
        
        self.edge_ai_url = os.getenv('EDGE_AI_API_URL', 'http://localhost:8091')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # Cache données en mémoire
        self.sensor_cache: Dict[str, SensorReading] = {}
        self.analytics_cache: Dict[str, AnalyticsResult] = {}
        self.cache_lock = Lock()
        
        # Client MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_connected = False
        
        # Client Redis
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis non disponible: {e}")
            self.redis_client = None
            
        # Flask + SocketIO
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'xai_secret_key_2024'
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self._setup_mqtt()
        self._setup_routes()
        self._setup_websocket_events()
        
    def _setup_mqtt(self):
        """Configuration client MQTT"""
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info("✅ Connecté au broker MQTT")
                self.mqtt_connected = True
                
                # Souscription aux topics capteurs
                client.subscribe("station/traffeyere/sensors/+/data", qos=1)
                client.subscribe("station/traffeyere/analytics/+", qos=1)
                
            else:
                logger.error(f"❌ Échec connexion MQTT: {rc}")
                self.mqtt_connected = False
        
        def on_message(client, userdata, msg):
            """Traitement messages MQTT"""
            try:
                topic = msg.topic
                payload = json.loads(msg.payload.decode())
                
                if "/sensors/" in topic and "/data" in topic:
                    # Message capteur
                    sensor_id = topic.split("/sensors/")[1].split("/data")[0]
                    self._process_sensor_data(sensor_id, payload)
                    
                elif "/analytics/" in topic:
                    # Résultat analyse IA
                    sensor_id = topic.split("/analytics/")[1]
                    self._process_analytics_data(sensor_id, payload)
                    
            except Exception as e:
                logger.error(f"Erreur traitement message MQTT: {e}")
        
        self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
        
    def _process_sensor_data(self, sensor_id: str, payload: Dict):
        """Traitement données capteur"""
        try:
            reading = SensorReading(
                sensor_id=sensor_id,
                value=float(payload.get('value', 0)),
                unit=payload.get('unit', ''),
                timestamp=datetime.fromisoformat(payload.get('timestamp', datetime.now().isoformat())),
                quality=float(payload.get('quality', 100.0)),
                status=payload.get('status', 'online')
            )
            
            with self.cache_lock:
                self.sensor_cache[sensor_id] = reading
                
            # Cache Redis si disponible
            if self.redis_client:
                try:
                    self.redis_client.setex(
                        f"sensor:{sensor_id}",
                        300,  # 5 minutes TTL
                        json.dumps({
                            'value': reading.value,
                            'unit': reading.unit,
                            'timestamp': reading.timestamp.isoformat(),
                            'quality': reading.quality,
                            'status': reading.status
                        })
                    )
                except Exception as e:
                    logger.warning(f"Erreur cache Redis: {e}")
            
            # Notification WebSocket
            self.socketio.emit('sensor_update', {
                'sensor_id': sensor_id,
                'value': reading.value,
                'unit': reading.unit,
                'timestamp': reading.timestamp.isoformat(),
                'status': reading.status
            })
            
        except Exception as e:
            logger.error(f"Erreur traitement sensor data: {e}")
            
    def _process_analytics_data(self, sensor_id: str, payload: Dict):
        """Traitement résultats analytics IA"""
        try:
            analytics = AnalyticsResult(
                sensor_id=sensor_id,
                anomaly_score=float(payload.get('anomaly_score', 0)),
                prediction=float(payload.get('prediction', 0)),
                confidence=float(payload.get('confidence', 0)),
                explanation=payload.get('explanation', ''),
                timestamp=datetime.fromisoformat(payload.get('timestamp', datetime.now().isoformat()))
            )
            
            with self.cache_lock:
                self.analytics_cache[sensor_id] = analytics
                
            # Notification WebSocket pour anomalies importantes
            if analytics.anomaly_score > 0.8:
                self.socketio.emit('anomaly_alert', {
                    'sensor_id': sensor_id,
                    'anomaly_score': analytics.anomaly_score,
                    'explanation': analytics.explanation,
                    'timestamp': analytics.timestamp.isoformat()
                })
                
        except Exception as e:
            logger.error(f"Erreur traitement analytics: {e}")
    
    def _setup_routes(self):
        """Configuration routes Flask"""
        
        @self.app.route('/health')
        def health_check():
            """Endpoint santé"""
            return jsonify({
                'status': 'healthy',
                'mqtt_connected': self.mqtt_connected,
                'sensors_count': len(self.sensor_cache),
                'analytics_count': len(self.analytics_cache),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/sensors')
        def get_sensors():
            """Liste des capteurs"""
            with self.cache_lock:
                sensors_data = {}
                for sensor_id, reading in self.sensor_cache.items():
                    sensors_data[sensor_id] = {
                        'value': reading.value,
                        'unit': reading.unit,
                        'timestamp': reading.timestamp.isoformat(),
                        'quality': reading.quality,
                        'status': reading.status
                    }
            return jsonify(sensors_data)
        
        @self.app.route('/api/sensor/<sensor_id>')
        def get_sensor(sensor_id: str):
            """Données capteur spécifique"""
            with self.cache_lock:
                reading = self.sensor_cache.get(sensor_id)
                if not reading:
                    return jsonify({'error': 'Capteur non trouvé'}), 404
                    
                return jsonify({
                    'sensor_id': sensor_id,
                    'value': reading.value,
                    'unit': reading.unit,
                    'timestamp': reading.timestamp.isoformat(),
                    'quality': reading.quality,
                    'status': reading.status
                })
        
        @self.app.route('/api/voice/query', methods=['POST'])
        def voice_query():
            """Traitement requête vocale"""
            try:
                data = request.get_json()
                query_text = data.get('text', '').lower()
                
                response = self._process_voice_query(query_text)
                
                return jsonify({
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Erreur voice query: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/<sensor_id>')
        def get_analytics(sensor_id: str):
            """Analytics pour capteur spécifique"""
            with self.cache_lock:
                analytics = self.analytics_cache.get(sensor_id)
                if not analytics:
                    return jsonify({'error': 'Analytics non disponibles'}), 404
                    
                return jsonify({
                    'sensor_id': sensor_id,
                    'anomaly_score': analytics.anomaly_score,
                    'prediction': analytics.prediction,
                    'confidence': analytics.confidence,
                    'explanation': analytics.explanation,
                    'timestamp': analytics.timestamp.isoformat()
                })
        
        @self.app.route('/api/dashboard/summary')
        def dashboard_summary():
            """Résumé pour dashboard"""
            with self.cache_lock:
                online_sensors = sum(1 for r in self.sensor_cache.values() if r.status == 'online')
                anomalies = sum(1 for a in self.analytics_cache.values() if a.anomaly_score > 0.8)
                avg_quality = sum(r.quality for r in self.sensor_cache.values()) / len(self.sensor_cache) if self.sensor_cache else 0
                
                return jsonify({
                    'total_sensors': len(self.sensor_cache),
                    'online_sensors': online_sensors,
                    'anomalies_count': anomalies,
                    'avg_quality': round(avg_quality, 1),
                    'last_update': max((r.timestamp.isoformat() for r in self.sensor_cache.values()), default='N/A')
                })
    
    def _setup_websocket_events(self):
        """Configuration événements WebSocket"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info("Client WebSocket connecté")
            emit('status', {
                'connected': True, 
                'mqtt_status': self.mqtt_connected,
                'sensors_count': len(self.sensor_cache)
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info("Client WebSocket déconnecté")
        
        @self.socketio.on('request_sensor_data')
        def handle_sensor_request(data):
            """Demande données capteur via WebSocket"""
            sensor_id = data.get('sensor_id')
            if sensor_id:
                with self.cache_lock:
                    reading = self.sensor_cache.get(sensor_id)
                    if reading:
                        emit('sensor_data', {
                            'sensor_id': sensor_id,
                            'value': reading.value,
                            'unit': reading.unit,
                            'timestamp': reading.timestamp.isoformat(),
                            'status': reading.status
                        })
    
    def _process_voice_query(self, query_text: str) -> str:
        """Traitement requête vocale en français"""
        query_text = query_text.lower().strip()
        
        # Extraction sensor_id si mentionné
        sensor_id = None
        for word in query_text.split():
            if word.startswith('capteur'):
                # Recherche nombre après "capteur"
                idx = query_text.find(word)
                remaining = query_text[idx + len(word):].strip()
                numbers = [w for w in remaining.split() if w.isdigit()]
                if numbers:
                    sensor_id = f"sensor_{numbers[0].zfill(3)}"
                    break
        
        # Analyse type de question
        if 'température' in query_text or 'temp' in query_text:
            return self._get_temperature_response(sensor_id)
        elif 'ph' in query_text:
            return self._get_ph_response(sensor_id)
        elif 'débit' in query_text or 'flow' in query_text:
            return self._get_flow_response(sensor_id)
        elif 'statut' in query_text or 'status' in query_text:
            return self._get_status_response(sensor_id)
        elif 'alerte' in query_text or 'anomalie' in query_text:
            return self._get_alerts_response()
        elif 'résumé' in query_text or 'summary' in query_text:
            return self._get_summary_response()
        else:
            return "Je n'ai pas compris votre demande. Vous pouvez demander le statut, la température, le pH, ou les alertes."
    
    def _get_temperature_response(self, sensor_id: Optional[str]) -> str:
        """Réponse température"""
        with self.cache_lock:
            if sensor_id and sensor_id in self.sensor_cache:
                reading = self.sensor_cache[sensor_id]
                if 'temp' in reading.unit.lower() or 'celsius' in reading.unit.lower():
                    return f"La température du capteur {sensor_id} est de {reading.value}°C."
            
            # Recherche capteurs température
            temp_sensors = [r for r in self.sensor_cache.values() 
                          if 'temp' in r.unit.lower() or 'celsius' in r.unit.lower()]
            
            if temp_sensors:
                avg_temp = sum(r.value for r in temp_sensors) / len(temp_sensors)
                return f"Température moyenne: {avg_temp:.1f}°C sur {len(temp_sensors)} capteurs."
            else:
                return "Aucun capteur de température trouvé."
    
    def _get_ph_response(self, sensor_id: Optional[str]) -> str:
        """Réponse pH"""
        with self.cache_lock:
            if sensor_id and sensor_id in self.sensor_cache:
                reading = self.sensor_cache[sensor_id]
                if 'ph' in reading.unit.lower():
                    return f"Le pH du capteur {sensor_id} est de {reading.value}."
            
            # Recherche capteurs pH
            ph_sensors = [r for r in self.sensor_cache.values() if 'ph' in r.unit.lower()]
            
            if ph_sensors:
                avg_ph = sum(r.value for r in ph_sensors) / len(ph_sensors)
                return f"pH moyen: {avg_ph:.2f} sur {len(ph_sensors)} capteurs."
            else:
                return "Aucun capteur de pH trouvé."
    
    def _get_status_response(self, sensor_id: Optional[str]) -> str:
        """Réponse statut"""
        with self.cache_lock:
            if sensor_id and sensor_id in self.sensor_cache:
                reading = self.sensor_cache[sensor_id]
                return f"Capteur {sensor_id}: {reading.status}, qualité {reading.quality}%."
            
            online = sum(1 for r in self.sensor_cache.values() if r.status == 'online')
            total = len(self.sensor_cache)
            return f"{online} capteurs en ligne sur {total} total."
    
    def _get_alerts_response(self) -> str:
        """Réponse alertes"""
        with self.cache_lock:
            anomalies = [a for a in self.analytics_cache.values() if a.anomaly_score > 0.8]
            
            if not anomalies:
                return "Aucune alerte critique détectée."
            
            if len(anomalies) == 1:
                alert = anomalies[0]
                return f"Alerte sur capteur {alert.sensor_id}: {alert.explanation}"
            else:
                return f"{len(anomalies)} alertes détectées. Consultez le dashboard pour plus de détails."
    
    def _get_summary_response(self) -> str:
        """Résumé général"""
        with self.cache_lock:
            total = len(self.sensor_cache)
            online = sum(1 for r in self.sensor_cache.values() if r.status == 'online')
            anomalies = sum(1 for a in self.analytics_cache.values() if a.anomaly_score > 0.8)
            
            return f"Station Traffeyère: {online}/{total} capteurs en ligne, {anomalies} anomalies détectées."
    
    def start_mqtt_connection(self):
        """Démarrage connexion MQTT"""
        try:
            logger.info(f"🔌 Connexion MQTT {self.mqtt_broker}:{self.mqtt_port}")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"❌ Erreur connexion MQTT: {e}")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Démarrage serveur"""
        # Démarrage MQTT en arrière-plan
        mqtt_thread = Thread(target=self.start_mqtt_connection)
        mqtt_thread.daemon = True
        mqtt_thread.start()
        
        # Attente connexion MQTT
        time.sleep(2)
        
        logger.info(f"🚀 Démarrage XAI Backend sur {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)

if __name__ == '__main__':
    backend = XAIBackend()
    backend.run(debug=True)
