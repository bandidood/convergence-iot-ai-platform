#!/usr/bin/env python3
"""
Edge AI Engine - Station Traffeyère
Analyse temps réel des données IoT avec IA explicable
"""

import os
import time
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import paho.mqtt.client as mqtt
import joblib

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/edge_ai_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EdgeAI')

class EdgeAIEngine:
    """Moteur IA Edge pour analyse temps réel"""
    
    def __init__(self):
        # Configuration
        self.mqtt_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_BROKER_PORT', '1883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME', 'station_mqtt')
        self.mqtt_password = os.getenv('MQTT_PASSWORD', 'mqtt_secure_2024')
        self.analytics_topic_prefix = os.getenv('ANALYTICS_TOPIC_PREFIX', 'station/traffeyere/analytics')
        self.anomaly_threshold = float(os.getenv('ANOMALY_THRESHOLD', '0.85'))
        
        # Client MQTT
        self.mqtt_client = None
        
        # Modèles IA
        self.anomaly_model = None
        self.scaler = None
        self.is_trained = False
        
        # Buffer de données
        self.sensor_buffer = {}
        self.buffer_size = 100
        self.analysis_window = 10  # Fenêtre glissante
        
        # Statistiques
        self.stats = {
            'total_messages': 0,
            'anomalies_detected': 0,
            'analysis_count': 0,
            'avg_processing_time': 0.0,
            'uptime_start': datetime.now()
        }
        
        # Flask app pour API REST
        self.app = Flask(__name__)
        self.setup_api_routes()
        
        # Threading
        self.running = False
        
    def setup_mqtt(self):
        """Configuration du client MQTT"""
        try:
            self.mqtt_client = mqtt.Client(client_id="station-edge-ai-engine")
            self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
            
            # Callbacks
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            # Connexion
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()
            
            logger.info(f"MQTT configuré: {self.mqtt_host}:{self.mqtt_port}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur configuration MQTT: {e}")
            return False
            
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback connexion MQTT"""
        if rc == 0:
            logger.info("MQTT connecté avec succès")
            # Souscription aux données capteurs
            client.subscribe("station/traffeyere/sensors/+/data")
            client.subscribe("station/traffeyere/summary/station")
            logger.info("Souscription aux topics de données")
        else:
            logger.error(f"Erreur connexion MQTT: {rc}")
            
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback déconnexion MQTT"""
        logger.warning(f"MQTT déconnecté: {rc}")
        
    def on_mqtt_message(self, client, userdata, msg):
        """Callback réception message MQTT"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            self.stats['total_messages'] += 1
            
            if '/sensors/' in topic and '/data' in topic:
                # Extraction ID capteur
                sensor_id = int(topic.split('/sensors/')[1].split('/')[0])
                self.process_sensor_data(sensor_id, payload)
                
            elif topic.endswith('/summary/station'):
                self.process_station_summary(payload)
                
        except Exception as e:
            logger.error(f"Erreur traitement message MQTT: {e}")
            
    def process_sensor_data(self, sensor_id: int, data: Dict[str, Any]):
        """Traitement données capteur individuel"""
        
        start_time = time.time()
        
        try:
            # Ajout au buffer
            if sensor_id not in self.sensor_buffer:
                self.sensor_buffer[sensor_id] = []
                
            self.sensor_buffer[sensor_id].append(data)
            
            # Limitation taille buffer
            if len(self.sensor_buffer[sensor_id]) > self.buffer_size:
                self.sensor_buffer[sensor_id].pop(0)
                
            # Analyse si suffisamment de données
            if len(self.sensor_buffer[sensor_id]) >= self.analysis_window:
                analysis_result = self.analyze_sensor_data(sensor_id)
                if analysis_result:
                    self.publish_analysis_result(sensor_id, analysis_result)
                    
        except Exception as e:
            logger.error(f"Erreur traitement capteur {sensor_id}: {e}")
            
        # Mise à jour statistiques
        processing_time = time.time() - start_time
        self.update_processing_stats(processing_time)
        
    def analyze_sensor_data(self, sensor_id: int) -> Optional[Dict[str, Any]]:
        """Analyse IA des données capteur"""
        
        if not self.sensor_buffer.get(sensor_id):
            return None
            
        try:
            # Préparation données
            recent_data = self.sensor_buffer[sensor_id][-self.analysis_window:]
            
            # Extraction features numériques
            features = []
            feature_names = ['ph', 'temperature', 'o2_dissous', 'turbidite', 'conductivite', 'debit', 'pression', 'niveau_bassin']
            
            for entry in recent_data:
                feature_row = []
                for feature in feature_names:
                    value = entry.get(feature, 0.0)
                    if value is None:
                        value = 0.0  # Imputation simple
                    feature_row.append(float(value))
                features.append(feature_row)
                
            if not features:
                return None
                
            features_array = np.array(features)
            
            # Analyse anomalies
            anomaly_score = self.detect_anomaly(features_array[-1])  # Dernière mesure
            
            # Analyse tendances
            trends = self.analyze_trends(features_array, feature_names)
            
            # Corrélations
            correlations = self.analyze_correlations(features_array, feature_names)
            
            # Qualité données
            data_quality = self.assess_data_quality(recent_data)
            
            # Prédictions simples
            predictions = self.make_predictions(features_array, feature_names)
            
            result = {
                'sensor_id': sensor_id,
                'timestamp': datetime.now().isoformat(),
                'anomaly': {
                    'score': float(anomaly_score),
                    'is_anomalous': float(anomaly_score) < -self.anomaly_threshold,
                    'threshold': self.anomaly_threshold
                },
                'trends': trends,
                'correlations': correlations,
                'data_quality': data_quality,
                'predictions': predictions,
                'window_size': len(recent_data)
            }
            
            self.stats['analysis_count'] += 1
            
            if result['anomaly']['is_anomalous']:
                self.stats['anomalies_detected'] += 1
                logger.warning(f"Anomalie détectée - Capteur {sensor_id}: score {anomaly_score:.3f}")
                
            return result
            
        except Exception as e:
            logger.error(f"Erreur analyse capteur {sensor_id}: {e}")
            return None
            
    def detect_anomaly(self, features: np.ndarray) -> float:
        """Détection d'anomalies avec Isolation Forest"""
        
        if not self.is_trained:
            return 0.0  # Pas de modèle entraîné
            
        try:
            # Normalisation
            if self.scaler:
                features_scaled = self.scaler.transform([features])
            else:
                features_scaled = [features]
                
            # Prédiction
            score = self.anomaly_model.decision_function(features_scaled)[0]
            return score
            
        except Exception as e:
            logger.error(f"Erreur détection anomalie: {e}")
            return 0.0
            
    def analyze_trends(self, features: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """Analyse des tendances temporelles"""
        
        trends = {}
        
        try:
            for i, feature_name in enumerate(feature_names):
                values = features[:, i]
                
                # Tendance linéaire simple
                x = np.arange(len(values))
                trend_slope = np.polyfit(x, values, 1)[0]
                
                # Variation récente
                recent_change = values[-1] - values[0] if len(values) > 1 else 0.0
                
                trends[feature_name] = {
                    'slope': float(trend_slope),
                    'recent_change': float(recent_change),
                    'direction': 'increasing' if trend_slope > 0.01 else 'decreasing' if trend_slope < -0.01 else 'stable'
                }
                
        except Exception as e:
            logger.error(f"Erreur analyse tendances: {e}")
            
        return trends
        
    def analyze_correlations(self, features: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """Analyse des corrélations entre paramètres"""
        
        correlations = {}
        
        try:
            if features.shape[0] < 3:  # Pas assez de données
                return correlations
                
            # Matrice de corrélation
            corr_matrix = np.corrcoef(features.T)
            
            # Corrélations significatives
            for i, feature1 in enumerate(feature_names):
                strong_correlations = []
                for j, feature2 in enumerate(feature_names):
                    if i != j and abs(corr_matrix[i, j]) > 0.7:
                        strong_correlations.append({
                            'parameter': feature2,
                            'correlation': float(corr_matrix[i, j])
                        })
                        
                if strong_correlations:
                    correlations[feature1] = strong_correlations
                    
        except Exception as e:
            logger.error(f"Erreur analyse corrélations: {e}")
            
        return correlations
        
    def assess_data_quality(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Évaluation qualité des données"""
        
        total_points = len(data)
        null_count = 0
        anomaly_count = 0
        
        for entry in data:
            # Comptage valeurs nulles
            for value in entry.values():
                if value is None:
                    null_count += 1
                    
            # Comptage anomalies explicites
            if 'anomaly' in entry:
                anomaly_count += 1
                
        completeness = 1.0 - (null_count / (total_points * 8))  # 8 paramètres principaux
        anomaly_rate = anomaly_count / total_points
        
        quality_score = completeness * (1.0 - min(anomaly_rate * 2, 0.5))
        
        return {
            'score': quality_score,
            'completeness': completeness,
            'anomaly_rate': anomaly_rate,
            'total_points': total_points,
            'status': 'excellent' if quality_score > 0.9 else 'good' if quality_score > 0.7 else 'poor'
        }
        
    def make_predictions(self, features: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """Prédictions simples basées sur les tendances"""
        
        predictions = {}
        
        try:
            for i, feature_name in enumerate(feature_names):
                values = features[:, i]
                
                if len(values) >= 3:
                    # Prédiction linéaire simple
                    x = np.arange(len(values))
                    coeffs = np.polyfit(x, values, 1)
                    next_value = coeffs[0] * len(values) + coeffs[1]
                    
                    # Confiance basée sur R²
                    predicted_values = np.polyval(coeffs, x)
                    ss_res = np.sum((values - predicted_values) ** 2)
                    ss_tot = np.sum((values - np.mean(values)) ** 2)
                    r_squared = 1 - (ss_res / (ss_tot + 1e-8))
                    
                    predictions[feature_name] = {
                        'next_value': float(next_value),
                        'confidence': max(0.0, float(r_squared)),
                        'current_value': float(values[-1])
                    }
                    
        except Exception as e:
            logger.error(f"Erreur prédictions: {e}")
            
        return predictions
        
    def publish_analysis_result(self, sensor_id: int, result: Dict[str, Any]):
        """Publication résultats d'analyse via MQTT"""
        
        if not self.mqtt_client:
            return
            
        try:
            topic = f"{self.analytics_topic_prefix}/sensor_{sensor_id:03d}"
            payload = json.dumps(result, ensure_ascii=False, default=str)
            
            self.mqtt_client.publish(topic, payload, qos=1)
            
        except Exception as e:
            logger.error(f"Erreur publication analyse: {e}")
            
    def process_station_summary(self, summary_data: Dict[str, Any]):
        """Traitement données synthèse station"""
        
        try:
            # Entraînement/mise à jour modèle si suffisamment de données
            if summary_data.get('total_sensors', 0) >= 50 and not self.is_trained:
                self.train_anomaly_model()
                
            # Publication analyse globale
            global_analysis = self.analyze_station_health(summary_data)
            self.publish_global_analysis(global_analysis)
            
        except Exception as e:
            logger.error(f"Erreur traitement synthèse station: {e}")
            
    def train_anomaly_model(self):
        """Entraînement modèle détection d'anomalies"""
        
        try:
            # Collecte données d'entraînement depuis le buffer
            training_data = []
            feature_names = ['ph', 'temperature', 'o2_dissous', 'turbidite', 'conductivite', 'debit', 'pression', 'niveau_bassin']
            
            for sensor_buffer in self.sensor_buffer.values():
                for entry in sensor_buffer:
                    feature_row = []
                    for feature in feature_names:
                        value = entry.get(feature, 0.0)
                        if value is None:
                            value = 0.0
                        feature_row.append(float(value))
                    training_data.append(feature_row)
                    
            if len(training_data) < 100:  # Pas assez de données
                logger.warning("Pas assez de données pour entraîner le modèle")
                return
                
            training_array = np.array(training_data)
            
            # Normalisation
            self.scaler = StandardScaler()
            training_scaled = self.scaler.fit_transform(training_array)
            
            # Entraînement Isolation Forest
            self.anomaly_model = IsolationForest(
                contamination=0.1,  # 10% d'anomalies attendues
                random_state=42,
                n_estimators=100
            )
            self.anomaly_model.fit(training_scaled)
            
            self.is_trained = True
            logger.info(f"Modèle d'anomalie entraîné avec {len(training_data)} échantillons")
            
            # Sauvegarde modèle
            model_path = '/app/models/edge_ai_model.pkl'
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            joblib.dump({
                'model': self.anomaly_model,
                'scaler': self.scaler,
                'feature_names': feature_names
            }, model_path)
            
        except Exception as e:
            logger.error(f"Erreur entraînement modèle: {e}")
            
    def analyze_station_health(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse santé globale de la station"""
        
        try:
            total_sensors = summary_data.get('total_sensors', 0)
            anomalies = summary_data.get('anomalies', [])
            zones = summary_data.get('zones', {})
            
            # Score santé global
            anomaly_rate = len(anomalies) / max(total_sensors, 1)
            base_health_score = 1.0 - min(anomaly_rate * 2, 0.8)
            
            # Analyse par zone
            zone_health = {}
            for zone_name, zone_data in zones.items():
                zone_anomaly_rate = zone_data.get('anomaly_count', 0) / max(zone_data.get('sensor_count', 1), 1)
                zone_score = 1.0 - min(zone_anomaly_rate * 2, 0.8)
                
                zone_health[zone_name] = {
                    'health_score': zone_score,
                    'anomaly_rate': zone_anomaly_rate,
                    'sensor_count': zone_data.get('sensor_count', 0),
                    'status': 'healthy' if zone_score > 0.8 else 'warning' if zone_score > 0.5 else 'critical'
                }
                
            # Alertes critiques
            critical_alerts = []
            for anomaly in anomalies:
                if anomaly.get('anomaly', {}).get('type') in ['pollution_spike', 'pump_failure', 'process_malfunction']:
                    critical_alerts.append({
                        'sensor_id': anomaly.get('sensor_id'),
                        'zone': anomaly.get('zone'),
                        'type': anomaly.get('anomaly', {}).get('type'),
                        'severity': 'critical'
                    })
                    
            # Recommandations
            recommendations = []
            if anomaly_rate > 0.1:
                recommendations.append("Taux d'anomalies élevé - Vérifier la maintenance préventive")
            if len(critical_alerts) > 0:
                recommendations.append("Alertes critiques détectées - Intervention immédiate requise")
                
            global_analysis = {
                'timestamp': datetime.now().isoformat(),
                'global_health_score': base_health_score,
                'total_sensors': total_sensors,
                'total_anomalies': len(anomalies),
                'anomaly_rate': anomaly_rate,
                'zone_health': zone_health,
                'critical_alerts': critical_alerts,
                'recommendations': recommendations,
                'status': 'healthy' if base_health_score > 0.8 else 'warning' if base_health_score > 0.5 else 'critical'
            }
            
            return global_analysis
            
        except Exception as e:
            logger.error(f"Erreur analyse santé station: {e}")
            return {}
            
    def publish_global_analysis(self, analysis: Dict[str, Any]):
        """Publication analyse globale"""
        
        if not self.mqtt_client or not analysis:
            return
            
        try:
            topic = f"{self.analytics_topic_prefix}/station_health"
            payload = json.dumps(analysis, ensure_ascii=False, default=str)
            
            self.mqtt_client.publish(topic, payload, qos=1)
            
        except Exception as e:
            logger.error(f"Erreur publication analyse globale: {e}")
            
    def update_processing_stats(self, processing_time: float):
        """Mise à jour statistiques de traitement"""
        
        # Moyenne mobile
        alpha = 0.1
        self.stats['avg_processing_time'] = (
            alpha * processing_time + 
            (1 - alpha) * self.stats['avg_processing_time']
        )
        
    def setup_api_routes(self):
        """Configuration routes API REST"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            uptime = (datetime.now() - self.stats['uptime_start']).total_seconds()
            return jsonify({
                'status': 'healthy',
                'uptime_seconds': uptime,
                'is_trained': self.is_trained,
                'mqtt_connected': self.mqtt_client and self.mqtt_client.is_connected() if self.mqtt_client else False
            })
            
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            return jsonify(self.stats)
            
        @self.app.route('/sensors/<int:sensor_id>/analysis', methods=['GET'])
        def get_sensor_analysis(sensor_id):
            if sensor_id in self.sensor_buffer:
                analysis = self.analyze_sensor_data(sensor_id)
                if analysis:
                    return jsonify(analysis)
            return jsonify({'error': 'No analysis available'}), 404
            
        @self.app.route('/model/retrain', methods=['POST'])
        def retrain_model():
            self.train_anomaly_model()
            return jsonify({'status': 'retraining_initiated'})
            
    def run(self):
        """Démarrage du service"""
        
        logger.info("Démarrage Edge AI Engine")
        
        if not self.setup_mqtt():
            logger.error("Impossible de configurer MQTT - Arrêt")
            return
            
        self.running = True
        
        # Lancement API REST dans un thread séparé
        def run_api():
            self.app.run(host='0.0.0.0', port=8091, debug=False)
            
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Arrêt demandé")
        finally:
            self.running = False
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            logger.info("Edge AI Engine arrêté")


if __name__ == "__main__":
    engine = EdgeAIEngine()
    engine.run()