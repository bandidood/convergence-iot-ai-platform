#!/usr/bin/env python3
"""
Générateur de données IoT réaliste - Station Traffeyère
127 capteurs simulés avec données corrélées et anomalies
"""

import os
import time
import json
import random
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np
import paho.mqtt.client as mqtt
from faker import Faker

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/iot_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('IoTGenerator')

fake = Faker('fr_FR')

class StationTraffeyereSimulator:
    """Simulateur réaliste station d'épuration"""
    
    def __init__(self):
        # Configuration MQTT
        self.mqtt_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_BROKER_PORT', '1883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME', 'station_mqtt')
        self.mqtt_password = os.getenv('MQTT_PASSWORD', 'mqtt_secure_2024')
        self.topic_prefix = os.getenv('TOPIC_PREFIX', 'station/traffeyere')
        
        # Configuration capteurs
        self.sensor_count = int(os.getenv('SENSOR_COUNT', '127'))
        self.publish_interval = float(os.getenv('PUBLISH_INTERVAL', '5000')) / 1000  # ms to sec
        
        # Données de base station
        self.base_values = {
            'ph': 7.2,
            'temperature': 16.5,
            'o2_dissous': 4.2,
            'turbidite': 12.3,
            'conductivite': 850.0,
            'debit': 2400.0,  # m3/h
            'pression': 1.2,   # bar
            'niveau_bassin': 3.5  # m
        }
        
        # Zones de capteurs
        self.sensor_zones = {
            'entree': {'count': 15, 'range': (1, 15)},
            'pretraitement': {'count': 18, 'range': (16, 33)},
            'bassin_aeration': {'count': 25, 'range': (34, 58)},
            'clarificateur': {'count': 22, 'range': (59, 80)},
            'traitement_boues': {'count': 20, 'range': (81, 100)},
            'sortie': {'count': 15, 'range': (101, 115)},
            'equipements': {'count': 12, 'range': (116, 127)}
        }
        
        # Client MQTT
        self.mqtt_client = None
        self.running = False
        
        # État simulation
        self.simulation_start = datetime.now()
        self.sensors_data = {}
        self.anomaly_probability = 0.02  # 2% chance anomalie
        
    def setup_mqtt(self):
        """Configuration du client MQTT"""
        try:
            self.mqtt_client = mqtt.Client(client_id=f"station-iot-generator-{fake.uuid4()}")
            self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
            
            # Callbacks
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_publish = self.on_mqtt_publish
            
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
        else:
            logger.error(f"Erreur connexion MQTT: {rc}")
            
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback déconnexion MQTT"""
        logger.warning(f"MQTT déconnecté: {rc}")
        
    def on_mqtt_publish(self, client, userdata, mid):
        """Callback publication MQTT"""
        pass  # Trop verbeux pour logger chaque publication
        
    def generate_realistic_sensor_data(self, sensor_id: int, zone: str) -> Dict[str, Any]:
        """Génère données réalistes pour un capteur"""
        
        # Temps simulation (accéléré)
        elapsed_hours = (datetime.now() - self.simulation_start).total_seconds() / 3600
        hour_of_day = (elapsed_hours * 24) % 24  # Cycle 24h accéléré
        day_of_year = ((elapsed_hours * 24) / 24) % 365
        
        # Facteurs cycliques réalistes
        daily_factor = 0.8 + 0.4 * np.sin(2 * np.pi * hour_of_day / 24)
        seasonal_factor = 0.9 + 0.2 * np.sin(2 * np.pi * day_of_year / 365)
        
        # Paramètres par zone
        zone_modifiers = {
            'entree': {'ph': -0.3, 'turbidite': 2.5, 'o2_dissous': -1.2},
            'pretraitement': {'ph': -0.1, 'turbidite': 1.8, 'o2_dissous': -0.8},
            'bassin_aeration': {'ph': 0.2, 'turbidite': -0.5, 'o2_dissous': 2.3},
            'clarificateur': {'ph': 0.1, 'turbidite': -1.8, 'o2_dissous': 0.5},
            'traitement_boues': {'ph': -0.2, 'turbidite': 3.2, 'o2_dissous': -2.1},
            'sortie': {'ph': 0.0, 'turbidite': -2.1, 'o2_dissous': 0.2},
            'equipements': {'pression': 0.3, 'temperature': 2.1, 'debit': 0.1}
        }
        
        modifier = zone_modifiers.get(zone, {})
        
        # Génération données corrélées
        data = {}
        
        # pH (6.5 - 8.5)
        base_ph = self.base_values['ph'] + modifier.get('ph', 0)
        ph_variation = 0.15 * np.sin(2 * np.pi * hour_of_day / 24) + np.random.normal(0, 0.05)
        data['ph'] = np.clip(base_ph + ph_variation, 6.0, 9.0)
        
        # Température (°C)
        base_temp = self.base_values['temperature'] + modifier.get('temperature', 0)
        temp_daily = 3.0 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        temp_seasonal = 8.0 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        data['temperature'] = base_temp + temp_daily + temp_seasonal + np.random.normal(0, 0.8)
        
        # Oxygène dissous (mg/L) - corrélé avec température et pH
        base_o2 = self.base_values['o2_dissous'] + modifier.get('o2_dissous', 0)
        o2_temp_effect = -0.1 * (data['temperature'] - 20)  # Solubilité O2 vs temp
        o2_ph_effect = 0.2 * (data['ph'] - 7.0)  # Activité biologique
        data['o2_dissous'] = max(0.1, base_o2 + o2_temp_effect + o2_ph_effect + np.random.normal(0, 0.3))
        
        # Turbidité (NTU)
        base_turb = self.base_values['turbidite'] + modifier.get('turbidite', 0)
        turb_flow_effect = 0.8 * daily_factor  # Impact débit sur remise en suspension
        data['turbidite'] = max(0.1, base_turb + turb_flow_effect + np.random.normal(0, 1.2))
        
        # Conductivité (µS/cm)
        base_cond = self.base_values['conductivite']
        cond_temp_effect = 2.0 * (data['temperature'] - 20)  # 2% par °C
        data['conductivite'] = base_cond + cond_temp_effect + np.random.normal(0, 25)
        
        # Débit (m3/h) - cycle journalier réaliste
        base_flow = self.base_values['debit'] * daily_factor * seasonal_factor
        flow_variation = 0.1 * base_flow * np.random.normal(0, 1)
        data['debit'] = max(100, base_flow + flow_variation)
        
        # Pression (bar)
        base_pressure = self.base_values['pression'] + modifier.get('pression', 0)
        pressure_flow_effect = 0.0002 * (data['debit'] - 2400)
        data['pression'] = base_pressure + pressure_flow_effect + np.random.normal(0, 0.05)
        
        # Niveau bassin (m)
        base_level = self.base_values['niveau_bassin']
        level_flow_effect = 0.001 * (data['debit'] - 2400)
        data['niveau_bassin'] = max(0.5, base_level + level_flow_effect + np.random.normal(0, 0.1))
        
        # Injection anomalies réalistes
        if random.random() < self.anomaly_probability:
            data = self.inject_anomaly(data, zone, sensor_id)
            
        # Métadonnées
        data['sensor_id'] = sensor_id
        data['zone'] = zone
        data['timestamp'] = datetime.now().isoformat()
        data['quality'] = self.calculate_data_quality(data)
        
        return data
        
    def inject_anomaly(self, data: Dict[str, Any], zone: str, sensor_id: int) -> Dict[str, Any]:
        """Injection d'anomalies réalistes"""
        
        anomaly_types = [
            'panne_capteur', 'pic_pollution', 'dysfonctionnement_process',
            'colmatage_filtre', 'panne_pompe', 'derive_capteur'
        ]
        
        anomaly_type = random.choice(anomaly_types)
        
        if anomaly_type == 'panne_capteur':
            # Capteur HS - valeurs aberrantes ou null
            param = random.choice(['ph', 'o2_dissous', 'turbidite'])
            data[param] = None
            data['anomaly'] = {'type': 'sensor_failure', 'parameter': param}
            
        elif anomaly_type == 'pic_pollution':
            # Pollution soudaine
            data['turbidite'] *= random.uniform(3.0, 8.0)
            data['o2_dissous'] *= random.uniform(0.3, 0.7)
            data['ph'] += random.uniform(-0.8, 0.8)
            data['anomaly'] = {'type': 'pollution_spike', 'severity': 'high'}
            
        elif anomaly_type == 'dysfonctionnement_process':
            # Process déréglé
            data['ph'] += random.uniform(-1.5, 1.5)
            data['o2_dissous'] *= random.uniform(0.5, 2.0)
            data['anomaly'] = {'type': 'process_malfunction', 'zone': zone}
            
        elif anomaly_type == 'colmatage_filtre':
            # Filtre colmaté
            data['pression'] *= random.uniform(1.3, 2.1)
            data['debit'] *= random.uniform(0.6, 0.8)
            data['anomaly'] = {'type': 'filter_clogging', 'impact': 'flow_reduction'}
            
        elif anomaly_type == 'panne_pompe':
            # Pompe défaillante
            data['debit'] *= random.uniform(0.3, 0.7)
            data['pression'] *= random.uniform(0.4, 0.8)
            data['anomaly'] = {'type': 'pump_failure', 'equipment_id': f"pump_{sensor_id}"}
            
        elif anomaly_type == 'derive_capteur':
            # Dérive lente capteur
            drift_factor = random.uniform(0.85, 1.15)
            for param in ['ph', 'temperature', 'conductivite']:
                if param in data:
                    data[param] *= drift_factor
            data['anomaly'] = {'type': 'sensor_drift', 'drift_factor': drift_factor}
            
        logger.warning(f"Anomalie générée - Capteur {sensor_id}: {anomaly_type}")
        return data
        
    def calculate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcul qualité des données"""
        
        quality_score = 1.0
        issues = []
        
        # Vérification valeurs nulles
        null_count = sum(1 for v in data.values() if v is None)
        if null_count > 0:
            quality_score *= 0.8
            issues.append(f"{null_count} valeurs manquantes")
            
        # Vérification plages réalistes
        bounds = {
            'ph': (5.0, 10.0),
            'temperature': (-5.0, 40.0),
            'o2_dissous': (0.0, 15.0),
            'turbidite': (0.0, 200.0),
            'conductivite': (200.0, 2000.0),
            'debit': (0.0, 5000.0)
        }
        
        for param, (min_val, max_val) in bounds.items():
            if param in data and data[param] is not None:
                if not (min_val <= data[param] <= max_val):
                    quality_score *= 0.7
                    issues.append(f"{param} hors limites")
                    
        # Anomalies détectées
        if 'anomaly' in data:
            quality_score *= 0.5
            issues.append("Anomalie détectée")
            
        return {
            'score': quality_score,
            'issues': issues,
            'status': 'good' if quality_score > 0.8 else 'warning' if quality_score > 0.5 else 'bad'
        }
        
    def publish_sensor_data(self, sensor_data: Dict[str, Any]):
        """Publication données capteur via MQTT"""
        
        if not self.mqtt_client:
            return
            
        sensor_id = sensor_data['sensor_id']
        zone = sensor_data['zone']
        
        # Topic spécifique capteur
        topic = f"{self.topic_prefix}/sensors/{sensor_id:03d}/data"
        
        # Topic zone
        topic_zone = f"{self.topic_prefix}/zones/{zone}/data"
        
        try:
            # Publication données capteur
            payload = json.dumps(sensor_data, ensure_ascii=False, indent=None)
            
            result = self.mqtt_client.publish(topic, payload, qos=1)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Erreur publication capteur {sensor_id}: {result.rc}")
            
            # Publication agrégée zone (échantillonnage)
            if random.random() < 0.1:  # 10% des messages
                zone_payload = {
                    'zone': zone,
                    'sensor_count': len([s for s in range(1, 128) if self.get_zone_for_sensor(s) == zone]),
                    'sample_data': sensor_data,
                    'timestamp': sensor_data['timestamp']
                }
                self.mqtt_client.publish(topic_zone, json.dumps(zone_payload), qos=0)
                
        except Exception as e:
            logger.error(f"Erreur publication MQTT: {e}")
            
    def get_zone_for_sensor(self, sensor_id: int) -> str:
        """Détermine la zone d'un capteur"""
        for zone, info in self.sensor_zones.items():
            min_id, max_id = info['range']
            if min_id <= sensor_id <= max_id:
                return zone
        return 'unknown'
        
    def generate_and_publish_all_sensors(self):
        """Génère et publie données de tous les capteurs"""
        
        start_time = time.time()
        
        for sensor_id in range(1, self.sensor_count + 1):
            zone = self.get_zone_for_sensor(sensor_id)
            
            try:
                sensor_data = self.generate_realistic_sensor_data(sensor_id, zone)
                self.sensors_data[sensor_id] = sensor_data
                self.publish_sensor_data(sensor_data)
                
            except Exception as e:
                logger.error(f"Erreur génération capteur {sensor_id}: {e}")
                
        generation_time = time.time() - start_time
        logger.info(f"Cycle complet: {self.sensor_count} capteurs en {generation_time:.2f}s")
        
    def publish_summary_stats(self):
        """Publication statistiques globales"""
        
        if not self.sensors_data:
            return
            
        # Calcul moyennes par zone
        zone_stats = {}
        for sensor_id, data in self.sensors_data.items():
            zone = data['zone']
            if zone not in zone_stats:
                zone_stats[zone] = {'sensors': [], 'data': []}
            zone_stats[zone]['sensors'].append(sensor_id)
            zone_stats[zone]['data'].append(data)
            
        # Agrégation
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_sensors': len(self.sensors_data),
            'zones': {},
            'global_averages': {},
            'anomalies': []
        }
        
        all_values = {param: [] for param in self.base_values.keys()}
        
        for zone, info in zone_stats.items():
            zone_summary = {
                'sensor_count': len(info['sensors']),
                'averages': {},
                'anomaly_count': 0
            }
            
            zone_values = {param: [] for param in self.base_values.keys()}
            
            for data in info['data']:
                for param in self.base_values.keys():
                    if param in data and data[param] is not None:
                        zone_values[param].append(data[param])
                        all_values[param].append(data[param])
                        
                if 'anomaly' in data:
                    zone_summary['anomaly_count'] += 1
                    summary['anomalies'].append({
                        'sensor_id': data['sensor_id'],
                        'zone': zone,
                        'anomaly': data['anomaly']
                    })
                    
            # Moyennes zone
            for param, values in zone_values.items():
                if values:
                    zone_summary['averages'][param] = {
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'min': np.min(values),
                        'max': np.max(values)
                    }
                    
            summary['zones'][zone] = zone_summary
            
        # Moyennes globales
        for param, values in all_values.items():
            if values:
                summary['global_averages'][param] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
                
        # Publication
        topic = f"{self.topic_prefix}/summary/station"
        try:
            payload = json.dumps(summary, ensure_ascii=False, default=str)
            self.mqtt_client.publish(topic, payload, qos=1)
            logger.info(f"Statistiques publiées: {len(summary['anomalies'])} anomalies détectées")
        except Exception as e:
            logger.error(f"Erreur publication statistiques: {e}")
            
    def run_simulation(self):
        """Boucle principale simulation"""
        
        logger.info("Démarrage simulation Station Traffeyère")
        logger.info(f"Configuration: {self.sensor_count} capteurs, intervalle {self.publish_interval}s")
        
        if not self.setup_mqtt():
            logger.error("Impossible de configurer MQTT - Arrêt")
            return
            
        self.running = True
        cycle_count = 0
        
        try:
            while self.running:
                cycle_start = time.time()
                cycle_count += 1
                
                logger.info(f"=== Cycle {cycle_count} ===")
                
                # Génération et publication données capteurs
                self.generate_and_publish_all_sensors()
                
                # Statistiques toutes les 10 cycles
                if cycle_count % 10 == 0:
                    self.publish_summary_stats()
                    
                # Attente prochain cycle
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, self.publish_interval - cycle_duration)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"Cycle trop long: {cycle_duration:.2f}s > {self.publish_interval}s")
                    
        except KeyboardInterrupt:
            logger.info("Arrêt demandé par utilisateur")
        except Exception as e:
            logger.error(f"Erreur simulation: {e}")
        finally:
            self.running = False
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            logger.info("Simulation arrêtée")


if __name__ == "__main__":
    simulator = StationTraffeyereSimulator()
    simulator.run_simulation()