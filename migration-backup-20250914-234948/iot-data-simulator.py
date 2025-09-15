#!/usr/bin/env python3
# =============================================================================
# SIMULATEUR IoT TEMPS RÉEL - Station Traffeyère IoT/AI Platform
# 127 capteurs avec données réalistes et anomalies - RNCP 39394
# =============================================================================

import asyncio
import json
import time
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import requests
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import threading

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iot_simulator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SensorConfig:
    """Configuration d'un capteur IoT"""
    id: str
    name: str
    type: str
    location: str
    unit: str
    min_value: float
    max_value: float
    normal_mean: float
    normal_std: float
    anomaly_probability: float = 0.05
    correlation_sensors: List[str] = None

class StationTraffeyereSimulator:
    """Simulateur complet Station Traffeyère avec 127 capteurs"""
    
    def __init__(self):
        self.sensors = self._initialize_sensors()
        self.running = False
        self.data_buffer = []
        
        # Configuration connexions
        self.influx_client = None
        self.mqtt_client = None
        self.backend_url = "http://localhost:8000"
        self.setup_connections()
        
        # État simulation
        self.anomaly_scenarios = []
        self.last_anomaly = datetime.now() - timedelta(hours=1)
        
        logger.info(f"✅ Simulateur initialisé avec {len(self.sensors)} capteurs")
    
    def _initialize_sensors(self) -> Dict[str, SensorConfig]:
        """Initialise les 127 capteurs de la station"""
        sensors = {}
        
        # 🔵 SECTION TRAITEMENT PRIMAIRE (30 capteurs)
        primary_sensors = [
            ("TEMP_PRIM_001", "Température Bassin Primaire 1", "temperature", "Bassin_1", "°C", -5, 45, 18.5, 2.1),
            ("PH_PRIM_001", "pH Bassin Primaire 1", "ph", "Bassin_1", "pH", 5.5, 9.0, 7.2, 0.3),
            ("O2_PRIM_001", "Oxygène Dissous Bassin 1", "dissolved_oxygen", "Bassin_1", "mg/L", 0, 12, 4.5, 0.8),
            ("TURB_PRIM_001", "Turbidité Bassin 1", "turbidity", "Bassin_1", "NTU", 0, 100, 15.2, 5.3),
            ("DEBIT_PRIM_001", "Débit Entrée Bassin 1", "flow", "Bassin_1", "m³/h", 0, 5000, 2400, 200),
            ("PRESSION_PRIM_001", "Pression Bassin 1", "pressure", "Bassin_1", "bar", 0.5, 3.0, 1.2, 0.15),
            ("REDOX_PRIM_001", "Potentiel Redox Bassin 1", "redox", "Bassin_1", "mV", -200, 800, 250, 45),
            ("CONDUCT_PRIM_001", "Conductivité Bassin 1", "conductivity", "Bassin_1", "µS/cm", 200, 2000, 850, 120),
            ("DBO5_PRIM_001", "DBO5 Bassin 1", "bod", "Bassin_1", "mg/L", 0, 500, 180, 35),
            ("DCO_PRIM_001", "DCO Bassin 1", "cod", "Bassin_1", "mg/L", 0, 1000, 320, 65),
        ]
        
        # Répliquer pour 3 bassins primaires
        for i in range(3):
            for base_id, base_name, sensor_type, base_location, unit, min_val, max_val, mean, std in primary_sensors:
                sensor_id = base_id.replace("001", f"{i+1:03d}")
                name = base_name.replace("1", str(i+1))
                location = base_location.replace("1", str(i+1))
                
                sensors[sensor_id] = SensorConfig(
                    id=sensor_id, name=name, type=sensor_type, location=location,
                    unit=unit, min_value=min_val, max_value=max_val,
                    normal_mean=mean + random.uniform(-0.1*mean, 0.1*mean),  # Variation entre bassins
                    normal_std=std, anomaly_probability=0.03
                )
        
        # 🟢 SECTION TRAITEMENT SECONDAIRE (35 capteurs)
        secondary_base = [
            ("TEMP_SEC", "Température Traitement Secondaire", "temperature", "°C", 15, 35, 22.3, 1.8),
            ("PH_SEC", "pH Traitement Secondaire", "ph", "pH", 6.0, 8.5, 7.1, 0.25),
            ("O2_SEC", "Oxygène Dissous Secondaire", "dissolved_oxygen", "mg/L", 1, 8, 3.8, 0.6),
            ("TURB_SEC", "Turbidité Secondaire", "turbidity", "NTU", 0, 50, 8.5, 3.2),
            ("DEBIT_SEC", "Débit Secondaire", "flow", "m³/h", 1000, 4000, 2200, 150),
            ("MVS_SEC", "Matières Volatiles en Suspension", "mvs", "mg/L", 500, 4000, 2500, 400),
            ("IB_SEC", "Indice de Boues", "sludge_index", "mL/g", 50, 200, 120, 25),
        ]
        
        # 5 lignes de traitement secondaire
        for line in range(5):
            for base_id, name, sensor_type, unit, min_val, max_val, mean, std in secondary_base:
                sensor_id = f"{base_id}_L{line+1:02d}"
                full_name = f"{name} Ligne {line+1}"
                location = f"Ligne_Secondaire_{line+1}"
                
                sensors[sensor_id] = SensorConfig(
                    id=sensor_id, name=full_name, type=sensor_type, location=location,
                    unit=unit, min_value=min_val, max_value=max_val,
                    normal_mean=mean + random.uniform(-0.05*mean, 0.05*mean),
                    normal_std=std, anomaly_probability=0.04
                )
        
        # 🟡 SECTION TRAITEMENT TERTIAIRE (22 capteurs)
        tertiary_sensors = [
            ("UV_INTENSITY_001", "Intensité UV Désinfection 1", "uv_intensity", "Désinfection_1", "mJ/cm²", 20, 100, 65, 8),
            ("CHLORE_RES_001", "Chlore Résiduel 1", "chlorine", "Désinfection_1", "mg/L", 0.1, 2.0, 0.5, 0.1),
            ("COLIF_001", "Coliformes Totaux 1", "coliforms", "Désinfection_1", "UFC/100mL", 0, 1000, 15, 25),
            ("ECOLI_001", "E.Coli 1", "ecoli", "Désinfection_1", "UFC/100mL", 0, 100, 2, 5),
            ("FILTR_PRESS_001", "Pression Filtration 1", "pressure", "Filtration_1", "bar", 0.5, 4.0, 1.8, 0.3),
            ("CARBON_SAT_001", "Saturation Charbon Actif 1", "carbon_saturation", "Filtration_1", "%", 0, 100, 35, 15),
        ]
        
        # Dupliquer pour 3 unités tertiaires + 1 de secours
        for unit in range(4):
            is_backup = unit == 3
            for base_id, base_name, sensor_type, location, unit_str, min_val, max_val, mean, std in tertiary_sensors:
                sensor_id = base_id.replace("001", f"{unit+1:03d}")
                name = base_name.replace("1", f"{unit+1}" + (" (Secours)" if is_backup else ""))
                loc = location.replace("1", str(unit+1))
                
                # Unité de secours moins active
                anomaly_prob = 0.02 if is_backup else 0.03
                
                sensors[sensor_id] = SensorConfig(
                    id=sensor_id, name=name, type=sensor_type, location=loc,
                    unit=unit_str, min_value=min_val, max_value=max_val,
                    normal_mean=mean, normal_std=std, anomaly_probability=anomaly_prob
                )
        
        # 🔴 CAPTEURS SYSTÈME & INFRASTRUCTURE (20 capteurs)
        system_sensors = [
            ("POWER_TOTAL", "Consommation Électrique Totale", "power", "Électrique", "kW", 500, 3000, 1800, 200),
            ("POWER_POMPES", "Consommation Pompes", "power", "Électrique", "kW", 100, 800, 450, 80),
            ("POWER_AERATION", "Consommation Aération", "power", "Électrique", "kW", 200, 1200, 750, 100),
            ("VIBR_POMPE_001", "Vibrations Pompe Principale 1", "vibration", "Mécanique", "mm/s", 0, 25, 4.2, 1.5),
            ("TEMP_MOTEUR_001", "Température Moteur 1", "temperature", "Mécanique", "°C", 20, 120, 65, 12),
            ("PRESSION_HUILE_001", "Pression Huile 1", "pressure", "Mécanique", "bar", 1.0, 6.0, 3.5, 0.5),
            ("NIVEAU_CUVE_BOUES", "Niveau Cuve Boues", "level", "Stockage", "m", 0, 8, 3.2, 1.0),
            ("NIVEAU_CUVE_CHLORE", "Niveau Cuve Chlore", "level", "Stockage", "m", 0, 5, 2.1, 0.8),
            ("METEO_TEMP", "Température Extérieure", "temperature", "Météo", "°C", -15, 45, 18, 8),
            ("METEO_HUMID", "Humidité Extérieure", "humidity", "Météo", "%", 20, 95, 68, 15),
            ("METEO_PLUIE", "Intensité Pluie", "precipitation", "Météo", "mm/h", 0, 50, 0.8, 3.5),
            ("METEO_VENT", "Vitesse Vent", "wind_speed", "Météo", "km/h", 0, 80, 12, 8),
        ]
        
        # Dupliquer équipements critiques
        for base_id, name, sensor_type, location, unit, min_val, max_val, mean, std in system_sensors:
            if "001" in base_id:  # Dupliquer pour redondance
                for i in range(3):
                    sensor_id = base_id.replace("001", f"{i+1:03d}")
                    full_name = name.replace("1", str(i+1))
                    
                    sensors[sensor_id] = SensorConfig(
                        id=sensor_id, name=full_name, type=sensor_type, location=location,
                        unit=unit, min_value=min_val, max_value=max_val,
                        normal_mean=mean, normal_std=std, anomaly_probability=0.06  # Plus d'anomalies mécaniques
                    )
            else:
                sensors[base_id] = SensorConfig(
                    id=base_id, name=name, type=sensor_type, location=location,
                    unit=unit, min_value=min_val, max_value=max_val,
                    normal_mean=mean, normal_std=std, anomaly_probability=0.02
                )
        
        # 🟣 CAPTEURS QUALITÉ SORTIE (20 capteurs finaux)
        output_sensors = [
            ("OUT_PH", "pH Sortie", "ph", "pH", 6.5, 8.5, 7.3, 0.2),
            ("OUT_TURB", "Turbidité Sortie", "turbidity", "NTU", 0, 10, 2.1, 1.2),
            ("OUT_DBO5", "DBO5 Sortie", "bod", "mg/L", 0, 25, 8, 3),
            ("OUT_DCO", "DCO Sortie", "cod", "mg/L", 0, 75, 28, 8),
            ("OUT_MVS", "MVS Sortie", "mvs", "mg/L", 0, 30, 12, 4),
            ("OUT_AZOTE", "Azote Total Sortie", "nitrogen", "mg/L", 0, 15, 6.5, 2.1),
            ("OUT_PHOSPHORE", "Phosphore Total Sortie", "phosphorus", "mg/L", 0, 2.0, 0.8, 0.3),
            ("OUT_CHLORE", "Chlore Résiduel Sortie", "chlorine", "mg/L", 0.1, 1.0, 0.3, 0.1),
            ("OUT_COLIF", "Coliformes Sortie", "coliforms", "UFC/100mL", 0, 100, 5, 8),
            ("OUT_DEBIT", "Débit Sortie", "flow", "m³/h", 1800, 2600, 2200, 100),
        ]
        
        # Points de contrôle sortie (2 redondants)
        for point in range(2):
            for base_id, name, sensor_type, unit, min_val, max_val, mean, std in output_sensors:
                sensor_id = f"{base_id}_P{point+1}"
                full_name = f"{name} Point {point+1}"
                location = f"Contrôle_Sortie_{point+1}"
                
                sensors[sensor_id] = SensorConfig(
                    id=sensor_id, name=full_name, type=sensor_type, location=location,
                    unit=unit, min_value=min_val, max_value=max_val,
                    normal_mean=mean, normal_std=std, anomaly_probability=0.01  # Très critique
                )
        
        logger.info(f"✅ {len(sensors)} capteurs configurés")
        return sensors
    
    def setup_connections(self):
        """Configuration connexions InfluxDB et MQTT"""
        try:
            # InfluxDB
            self.influx_client = InfluxDBClient(
                url="http://localhost:8086",
                token="StationTraffeyereToken2024",
                org="traffeyere"
            )
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            logger.info("✅ Connexion InfluxDB établie")
            
            # MQTT
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.connect("localhost", 1883, 60)
            logger.info("✅ Connexion MQTT établie")
            
        except Exception as e:
            logger.error(f"❌ Erreur connexions: {e}")
    
    def generate_sensor_reading(self, sensor: SensorConfig) -> Dict:
        """Génère une lecture réaliste pour un capteur"""
        current_time = datetime.now()
        
        # Génération valeur normale
        if sensor.type in ["temperature", "ph", "dissolved_oxygen"]:
            # Cycles journaliers pour paramètres biologiques
            hour_factor = 0.9 + 0.2 * np.sin(2 * np.pi * current_time.hour / 24)
            base_value = sensor.normal_mean * hour_factor
        elif sensor.type in ["flow", "power"]:
            # Cycles consommation industrielle
            if 6 <= current_time.hour <= 22:  # Heures actives
                base_value = sensor.normal_mean * 1.1
            else:  # Heures creuses
                base_value = sensor.normal_mean * 0.8
        else:
            base_value = sensor.normal_mean
        
        # Ajout bruit gaussien
        noise = np.random.normal(0, sensor.normal_std)
        value = base_value + noise
        
        # Génération anomalies
        is_anomaly = False
        anomaly_type = None
        anomaly_severity = 0.0
        
        if random.random() < sensor.anomaly_probability:
            is_anomaly = True
            anomaly_types = ["spike", "drift", "noise", "stuck", "offset"]
            anomaly_type = random.choice(anomaly_types)
            anomaly_severity = random.uniform(0.3, 1.0)
            
            if anomaly_type == "spike":
                value *= (1 + anomaly_severity * 2)
            elif anomaly_type == "drift":
                value += sensor.normal_std * anomaly_severity * 5
            elif anomaly_type == "noise":
                value += np.random.normal(0, sensor.normal_std * anomaly_severity * 3)
            elif anomaly_type == "stuck":
                # Garder la valeur précédente (simulé par valeur fixe)
                value = sensor.normal_mean
            elif anomaly_type == "offset":
                value += sensor.normal_mean * anomaly_severity * 0.3
        
        # Contraintes physiques
        value = np.clip(value, sensor.min_value, sensor.max_value)
        
        # Corrélations réalistes (exemple: pH vs conductivité)
        if sensor.type == "ph" and "PRIM" in sensor.id:
            # pH bas → conductivité haute (pollution)
            if value < 6.5:
                correlated_sensor_id = sensor.id.replace("PH_", "CONDUCT_")
                if correlated_sensor_id in self.sensors:
                    # Signaler corrélation pour traitement ultérieur
                    pass
        
        return {
            "sensor_id": sensor.id,
            "sensor_name": sensor.name,
            "sensor_type": sensor.type,
            "location": sensor.location,
            "value": round(float(value), 3),
            "unit": sensor.unit,
            "timestamp": current_time.isoformat(),
            "is_anomaly": is_anomaly,
            "anomaly_type": anomaly_type,
            "anomaly_severity": round(anomaly_severity, 2) if is_anomaly else 0.0,
            "quality_score": round(max(0, 100 - abs((value - sensor.normal_mean) / sensor.normal_std) * 10), 1),
            "normal_range": {
                "min": round(sensor.normal_mean - 2*sensor.normal_std, 2),
                "max": round(sensor.normal_mean + 2*sensor.normal_std, 2)
            }
        }
    
    async def send_to_influxdb(self, reading: Dict):
        """Envoi vers InfluxDB"""
        try:
            point = Point("sensor_data") \
                .tag("sensor_id", reading["sensor_id"]) \
                .tag("sensor_type", reading["sensor_type"]) \
                .tag("location", reading["location"]) \
                .field("value", reading["value"]) \
                .field("quality_score", reading["quality_score"]) \
                .field("is_anomaly", reading["is_anomaly"]) \
                .field("anomaly_severity", reading["anomaly_severity"]) \
                .time(datetime.fromisoformat(reading["timestamp"]), WritePrecision.NS)
            
            self.write_api.write("iot_sensors", "traffeyere", point)
        except Exception as e:
            logger.error(f"❌ Erreur InfluxDB: {e}")
    
    async def send_to_mqtt(self, reading: Dict):
        """Envoi vers MQTT"""
        try:
            topic = f"traffeyere/sensors/{reading['location']}/{reading['sensor_id']}"
            payload = json.dumps(reading)
            self.mqtt_client.publish(topic, payload, qos=1)
        except Exception as e:
            logger.error(f"❌ Erreur MQTT: {e}")
    
    async def send_to_backend(self, reading: Dict):
        """Envoi vers Backend API"""
        try:
            response = requests.post(
                f"{self.backend_url}/api/v1/sensor-data",
                json=reading,
                timeout=5
            )
            if response.status_code != 200:
                logger.warning(f"⚠️ Backend response: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Erreur Backend: {e}")
    
    async def generate_all_sensors_data(self):
        """Génère données pour tous les capteurs"""
        readings = []
        
        for sensor in self.sensors.values():
            reading = self.generate_sensor_reading(sensor)
            readings.append(reading)
            
            # Envoi async vers tous les endpoints
            await asyncio.gather(
                self.send_to_influxdb(reading),
                self.send_to_mqtt(reading),
                self.send_to_backend(reading),
                return_exceptions=True
            )
        
        return readings
    
    def generate_scenario_anomaly(self):
        """Génère un scénario d'anomalie complexe"""
        scenarios = [
            "pollution_spike",    # Pic de pollution
            "equipment_failure",  # Panne équipement
            "process_drift",      # Dérive processus
            "calibration_error",  # Erreur calibrage
            "cyber_attack"        # Cyberattaque simulée
        ]
        
        scenario = random.choice(scenarios)
        logger.info(f"🚨 Scénario anomalie: {scenario}")
        
        if scenario == "pollution_spike":
            # Pic coordonné sur plusieurs capteurs
            affected_sensors = [s for s in self.sensors.values() if s.type in ["turbidity", "cod", "bod"]]
            for sensor in affected_sensors[:5]:  # 5 capteurs impactés
                sensor.anomaly_probability = 0.8  # Force anomalie
        
        elif scenario == "equipment_failure":
            # Panne pompe → cascade d'anomalies
            pump_sensors = [s for s in self.sensors.values() if "POMPE" in s.id or s.type == "flow"]
            for sensor in pump_sensors[:3]:
                sensor.anomaly_probability = 0.9
        
        # Reset après 10 cycles
        threading.Timer(60.0, self.reset_anomaly_probabilities).start()
    
    def reset_anomaly_probabilities(self):
        """Reset probabilités anomalies à la normale"""
        for sensor in self.sensors.values():
            if "PRIM" in sensor.id:
                sensor.anomaly_probability = 0.03
            elif "SEC" in sensor.id:
                sensor.anomaly_probability = 0.04
            else:
                sensor.anomaly_probability = 0.02
        logger.info("✅ Probabilités anomalies remises à la normale")
    
    async def run_simulation(self, interval: float = 5.0):
        """Lance la simulation continue"""
        self.running = True
        cycle_count = 0
        
        logger.info(f"🚀 Début simulation - {len(self.sensors)} capteurs - Intervalle: {interval}s")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Génération données tous capteurs
                readings = await self.generate_all_sensors_data()
                
                # Statistiques cycle
                anomalies = sum(1 for r in readings if r["is_anomaly"])
                avg_quality = np.mean([r["quality_score"] for r in readings])
                
                cycle_count += 1
                cycle_time = time.time() - start_time
                
                logger.info(
                    f"📊 Cycle {cycle_count:04d} - "
                    f"Données: {len(readings)} - "
                    f"Anomalies: {anomalies:02d} - "
                    f"Qualité: {avg_quality:.1f}% - "
                    f"Temps: {cycle_time:.2f}s"
                )
                
                # Scénario anomalie aléatoire (toutes les 10-30 minutes)
                if cycle_count % random.randint(120, 360) == 0:
                    self.generate_scenario_anomaly()
                
                # Attendre prochain cycle
                await asyncio.sleep(max(0, interval - cycle_time))
                
            except KeyboardInterrupt:
                logger.info("🛑 Interruption utilisateur - Arrêt simulation")
                break
            except Exception as e:
                logger.error(f"❌ Erreur simulation: {e}")
                await asyncio.sleep(interval)
        
        self.running = False
        logger.info("✅ Simulation terminée")
    
    def stop_simulation(self):
        """Arrêt simulation"""
        self.running = False
        if self.influx_client:
            self.influx_client.close()
        if self.mqtt_client:
            self.mqtt_client.disconnect()

def main():
    """Point d'entrée principal"""
    print("🚀 Station Traffeyère IoT/AI Platform - Simulateur Temps Réel")
    print("=" * 65)
    print("📊 127 capteurs IoT avec données réalistes et anomalies")
    print("🎯 RNCP 39394 - Expert en Systèmes d'Information et Sécurité")
    print("=" * 65)
    
    # Configuration simulation
    simulator = StationTraffeyereSimulator()
    
    print(f"✅ {len(simulator.sensors)} capteurs configurés:")
    
    # Statistiques par type
    sensor_types = {}
    for sensor in simulator.sensors.values():
        location = sensor.location.split('_')[0]
        sensor_types[location] = sensor_types.get(location, 0) + 1
    
    for location, count in sorted(sensor_types.items()):
        print(f"   📍 {location:<25}: {count:2d} capteurs")
    
    print("\n🔧 Configuration:")
    print("   InfluxDB: http://localhost:8086")
    print("   MQTT:     localhost:1883")
    print("   Backend:  http://localhost:8000")
    print("   Intervalle: 5 secondes")
    print("\n⚡ Démarrage simulation... (Ctrl+C pour arrêter)")
    
    try:
        asyncio.run(simulator.run_simulation(interval=5.0))
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    finally:
        simulator.stop_simulation()
        print("✅ Simulation arrêtée proprement")

if __name__ == "__main__":
    main()