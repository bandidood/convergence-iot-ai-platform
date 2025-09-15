"""
🏭 GÉNÉRATEUR IoT STATION TRAFFEYÈRE - 127 CAPTEURS
Générateur de données réalistes pour simulation complète station d'épuration
Compatible RNCP 39394 - Expert en Systèmes d'Information et Sécurité

Auteur: Expert DevSecOps & IA Explicable  
Version: 1.0.0
"""

import asyncio
import time
import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from prometheus_client import Gauge, Counter, Histogram, start_http_server
import requests
import math

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SensorType(Enum):
    """Types de capteurs station d'épuration"""
    PH = "ph"
    OXYGEN_DISSOLVED = "o2_dissous" 
    TURBIDITY = "turbidite"
    FLOW_RATE = "debit"
    TEMPERATURE = "temperature"
    PRESSURE = "pression"
    CONDUCTIVITY = "conductivite"
    NITROGEN = "azote_total"
    PHOSPHORUS = "phosphore"
    SUSPENDED_SOLIDS = "mes"  # Matières en suspension
    COD = "dco"  # Demande chimique en oxygène
    BOD = "dbo5"  # Demande biologique en oxygène
    HEAVY_METALS = "metaux_lourds"
    CHLORINE = "chlore_residuel"
    AMMONIA = "ammoniac"
    NITRATES = "nitrates"
    NITRITES = "nitrites"
    ENERGY_CONSUMPTION = "consommation_energie"
    PUMP_STATUS = "statut_pompe"
    VALVE_POSITION = "position_vanne"

class ProcessStage(Enum):
    """Étapes du processus d'épuration"""
    PRETREATMENT = "pretraitement"
    PRIMARY_SETTLING = "decantation_primaire"
    BIOLOGICAL_TREATMENT = "traitement_biologique"
    SECONDARY_SETTLING = "decantation_secondaire"
    TERTIARY_TREATMENT = "traitement_tertiaire"
    DISINFECTION = "desinfection"
    SLUDGE_TREATMENT = "traitement_boues"
    OUTLET = "sortie"

@dataclass
class SensorReading:
    """Lecture d'un capteur IoT"""
    sensor_id: str
    sensor_type: SensorType
    process_stage: ProcessStage
    value: float
    unit: str
    timestamp: datetime
    location: str
    quality_grade: str  # A, B, C, D selon ISA/IEC 62443
    is_anomaly: bool = False
    anomaly_type: Optional[str] = None
    confidence: float = 1.0

class StationTraffeyereSimulator:
    """
    Simulateur complet Station d'Épuration Traffeyère
    127 capteurs IoT avec corrélations physico-chimiques réalistes
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.sensors_config = self._initialize_sensors()
        self.weather_data = {}
        self.process_parameters = self._initialize_process_parameters()
        self.anomaly_probability = 0.02  # 2% de probabilité d'anomalie
        
        # Métriques Prometheus
        self.setup_prometheus_metrics()
        
        # État interne simulation
        self.current_readings = {}
        self.historical_data = []
        self.active_anomalies = {}
        
        logger.info(f"🏭 Simulateur Station Traffeyère initialisé - {len(self.sensors_config)} capteurs")

    def _initialize_sensors(self) -> List[Dict[str, Any]]:
        """Configuration des 127 capteurs de la station"""
        sensors = []
        
        # Prétraitement - 15 capteurs
        for i in range(15):
            sensors.append({
                'id': f'PRE_{i:03d}',
                'type': random.choice([SensorType.FLOW_RATE, SensorType.PH, SensorType.TEMPERATURE, 
                                     SensorType.SUSPENDED_SOLIDS, SensorType.CONDUCTIVITY]),
                'stage': ProcessStage.PRETREATMENT,
                'location': f'Dégrillage_{i%3 + 1}',
                'base_value': self._get_base_value_by_type(SensorType.FLOW_RATE),
                'variance': 0.1
            })
        
        # Décantation primaire - 18 capteurs
        for i in range(18):
            sensors.append({
                'id': f'DEC1_{i:03d}',
                'type': random.choice([SensorType.TURBIDITY, SensorType.SUSPENDED_SOLIDS, 
                                     SensorType.FLOW_RATE, SensorType.PH, SensorType.COD]),
                'stage': ProcessStage.PRIMARY_SETTLING,
                'location': f'Bassin_Primaire_{i%6 + 1}',
                'base_value': self._get_base_value_by_type(SensorType.TURBIDITY),
                'variance': 0.15
            })
        
        # Traitement biologique - 35 capteurs (le plus critique)
        for i in range(35):
            sensors.append({
                'id': f'BIO_{i:03d}',
                'type': random.choice([SensorType.OXYGEN_DISSOLVED, SensorType.BOD, SensorType.COD,
                                     SensorType.NITROGEN, SensorType.PHOSPHORUS, SensorType.AMMONIA,
                                     SensorType.NITRATES, SensorType.NITRITES, SensorType.TEMPERATURE]),
                'stage': ProcessStage.BIOLOGICAL_TREATMENT,
                'location': f'Bassin_Biologique_{i%7 + 1}',
                'base_value': self._get_base_value_by_type(SensorType.OXYGEN_DISSOLVED),
                'variance': 0.08
            })
        
        # Décantation secondaire - 16 capteurs
        for i in range(16):
            sensors.append({
                'id': f'DEC2_{i:03d}',
                'type': random.choice([SensorType.TURBIDITY, SensorType.SUSPENDED_SOLIDS,
                                     SensorType.COD, SensorType.BOD, SensorType.NITROGEN]),
                'stage': ProcessStage.SECONDARY_SETTLING,
                'location': f'Clarificateur_{i%4 + 1}',
                'base_value': self._get_base_value_by_type(SensorType.SUSPENDED_SOLIDS),
                'variance': 0.12
            })
        
        # Traitement tertiaire - 12 capteurs
        for i in range(12):
            sensors.append({
                'id': f'TER_{i:03d}',
                'type': random.choice([SensorType.PHOSPHORUS, SensorType.NITROGEN, SensorType.HEAVY_METALS,
                                     SensorType.CONDUCTIVITY, SensorType.PH]),
                'stage': ProcessStage.TERTIARY_TREATMENT,
                'location': f'Filtration_{i%3 + 1}',
                'base_value': self._get_base_value_by_type(SensorType.PHOSPHORUS),
                'variance': 0.05
            })
        
        # Désinfection - 8 capteurs
        for i in range(8):
            sensors.append({
                'id': f'DIS_{i:03d}',
                'type': random.choice([SensorType.CHLORINE, SensorType.PH, SensorType.TURBIDITY,
                                     SensorType.TEMPERATURE]),
                'stage': ProcessStage.DISINFECTION,
                'location': f'UV_Ozone_{i%2 + 1}',
                'base_value': self._get_base_value_by_type(SensorType.CHLORINE),
                'variance': 0.1
            })
        
        # Traitement des boues - 10 capteurs
        for i in range(10):
            sensors.append({
                'id': f'BOU_{i:03d}',
                'type': random.choice([SensorType.SUSPENDED_SOLIDS, SensorType.PH, SensorType.TEMPERATURE,
                                     SensorType.PRESSURE]),
                'stage': ProcessStage.SLUDGE_TREATMENT,
                'location': f'Digesteur_{i%2 + 1}',
                'base_value': self._get_base_value_by_type(SensorType.PRESSURE),
                'variance': 0.2
            })
        
        # Sortie et contrôle final - 13 capteurs
        for i in range(13):
            sensors.append({
                'id': f'OUT_{i:03d}',
                'type': random.choice([SensorType.PH, SensorType.COD, SensorType.BOD, SensorType.NITROGEN,
                                     SensorType.PHOSPHORUS, SensorType.TURBIDITY, SensorType.HEAVY_METALS]),
                'stage': ProcessStage.OUTLET,
                'location': f'Rejet_Final',
                'base_value': self._get_base_value_by_type(SensorType.COD),
                'variance': 0.05
            })
        
        return sensors

    def _get_base_value_by_type(self, sensor_type: SensorType) -> float:
        """Valeurs de base réalistes par type de capteur"""
        base_values = {
            SensorType.PH: 7.2,
            SensorType.OXYGEN_DISSOLVED: 4.5,
            SensorType.TURBIDITY: 15.0,
            SensorType.FLOW_RATE: 2400.0,  # m³/h
            SensorType.TEMPERATURE: 18.5,
            SensorType.PRESSURE: 1.013,  # bar
            SensorType.CONDUCTIVITY: 1200.0,  # µS/cm
            SensorType.NITROGEN: 25.0,  # mg/L
            SensorType.PHOSPHORUS: 3.5,  # mg/L
            SensorType.SUSPENDED_SOLIDS: 180.0,  # mg/L
            SensorType.COD: 420.0,  # mg O2/L
            SensorType.BOD: 250.0,  # mg O2/L
            SensorType.HEAVY_METALS: 0.08,  # mg/L
            SensorType.CHLORINE: 0.5,  # mg/L
            SensorType.AMMONIA: 18.0,  # mg/L
            SensorType.NITRATES: 12.0,  # mg/L
            SensorType.NITRITES: 0.8,  # mg/L
            SensorType.ENERGY_CONSUMPTION: 850.0,  # kWh
            SensorType.PUMP_STATUS: 1.0,  # 0=arrêt, 1=marche
            SensorType.VALVE_POSITION: 50.0  # % ouverture
        }
        return base_values.get(sensor_type, 1.0)
    
    def _get_unit_by_type(self, sensor_type: SensorType) -> str:
        """Unités par type de capteur"""
        units = {
            SensorType.PH: "pH",
            SensorType.OXYGEN_DISSOLVED: "mg/L",
            SensorType.TURBIDITY: "NTU",
            SensorType.FLOW_RATE: "m³/h",
            SensorType.TEMPERATURE: "°C",
            SensorType.PRESSURE: "bar",
            SensorType.CONDUCTIVITY: "µS/cm",
            SensorType.NITROGEN: "mg/L",
            SensorType.PHOSPHORUS: "mg/L",
            SensorType.SUSPENDED_SOLIDS: "mg/L",
            SensorType.COD: "mg O2/L",
            SensorType.BOD: "mg O2/L",
            SensorType.HEAVY_METALS: "mg/L",
            SensorType.CHLORINE: "mg/L",
            SensorType.AMMONIA: "mg/L",
            SensorType.NITRATES: "mg/L",
            SensorType.NITRITES: "mg/L",
            SensorType.ENERGY_CONSUMPTION: "kWh",
            SensorType.PUMP_STATUS: "status",
            SensorType.VALVE_POSITION: "%"
        }
        return units.get(sensor_type, "unit")

    def _initialize_process_parameters(self) -> Dict[str, float]:
        """Paramètres du processus d'épuration"""
        return {
            'hydraulic_retention_time': 8.5,  # heures
            'sludge_age': 12.0,  # jours
            'recirculation_ratio': 1.2,
            'food_to_microorganism_ratio': 0.25,
            'mixed_liquor_concentration': 3500.0,  # mg/L
            'oxygen_transfer_efficiency': 0.82,
            'settling_velocity': 1.8,  # m/h
            'removal_efficiency_cod': 0.92,
            'removal_efficiency_nitrogen': 0.78,
            'removal_efficiency_phosphorus': 0.85
        }

    def setup_prometheus_metrics(self):
        """Configuration métriques Prometheus pour tous capteurs"""
        # Métriques par type de capteur
        self.prometheus_gauges = {}
        
        for sensor_type in SensorType:
            # Valeur actuelle
            self.prometheus_gauges[f'{sensor_type.value}_current'] = Gauge(
                f'station_traffeyere_{sensor_type.value}_current',
                f'Valeur actuelle {sensor_type.value}',
                ['sensor_id', 'process_stage', 'location']
            )
            
            # Qualité signal
            self.prometheus_gauges[f'{sensor_type.value}_quality'] = Gauge(
                f'station_traffeyere_{sensor_type.value}_quality',
                f'Qualité signal {sensor_type.value} (0-1)',
                ['sensor_id', 'process_stage', 'location']
            )
        
        # Métriques globales
        self.total_sensors = Gauge('station_traffeyere_total_sensors', 'Nombre total capteurs actifs')
        self.anomaly_counter = Counter('station_traffeyere_anomalies_total', 'Total anomalies détectées')
        self.data_generation_latency = Histogram('station_traffeyere_generation_latency_seconds', 
                                               'Latence génération données')
        
        # Métriques process globaux
        self.inlet_flow = Gauge('station_traffeyere_inlet_flow_m3h', 'Débit entrée station')
        self.treatment_efficiency = Gauge('station_traffeyere_treatment_efficiency_percent', 
                                        'Efficacité traitement global')
        self.energy_consumption = Gauge('station_traffeyere_energy_consumption_kwh', 'Consommation énergétique')
        self.compliance_score = Gauge('station_traffeyere_compliance_score', 'Score conformité DERU')

    async def get_weather_data(self) -> Dict[str, float]:
        """Récupération données météo réelles (simulation)"""
        # Simulation météo réaliste Saint-Quentin-Fallavier
        now = datetime.now()
        day_of_year = now.timetuple().tm_yday
        hour = now.hour
        
        # Cycle saisonnier + journalier
        base_temp = 12 + 8 * math.sin(2 * math.pi * day_of_year / 365)
        temp = base_temp + 5 * math.sin(2 * math.pi * hour / 24) + random.gauss(0, 2)
        
        # Précipitations aléatoires avec saisonnalité
        rain_probability = 0.3 if day_of_year < 120 or day_of_year > 300 else 0.15
        precipitation = random.expovariate(0.1) if random.random() < rain_probability else 0
        
        weather = {
            'temperature': round(temp, 1),
            'humidity': random.randint(45, 95),
            'precipitation': round(precipitation, 1),
            'wind_speed': round(random.expovariate(0.2), 1),
            'pressure': round(1013.25 + random.gauss(0, 10), 1),
            'solar_irradiance': max(0, 800 * math.sin(2 * math.pi * hour / 24)) if 6 <= hour <= 18 else 0
        }
        
        self.weather_data = weather
        return weather

    def calculate_correlated_values(self, sensor_config: Dict[str, Any], weather: Dict[str, float]) -> float:
        """Calcul valeurs corrélées physico-chimiques réalistes"""
        base_value = sensor_config['base_value']
        variance = sensor_config['variance']
        sensor_type = sensor_config['type']
        stage = sensor_config['stage']
        
        # Facteur temporel (cycles journaliers)
        hour = datetime.now().hour
        daily_factor = 0.8 + 0.4 * math.sin(2 * math.pi * hour / 24)
        
        # Influence météorologique
        weather_factor = 1.0
        if weather['precipitation'] > 0:
            if sensor_type in [SensorType.FLOW_RATE, SensorType.TURBIDITY]:
                weather_factor = 1 + (weather['precipitation'] / 10)  # Augmentation avec pluie
            elif sensor_type == SensorType.TEMPERATURE:
                weather_factor = 0.95  # Légère baisse température avec pluie
        
        # Corrélations process biologique
        process_factor = 1.0
        if stage == ProcessStage.BIOLOGICAL_TREATMENT:
            if sensor_type == SensorType.OXYGEN_DISSOLVED:
                # O2 dépend de la température et de la charge
                temp_effect = 1 - (weather['temperature'] - 20) * 0.02
                process_factor = temp_effect * daily_factor
            elif sensor_type == SensorType.BOD:
                # DBO5 inversement corrélée à l'efficacité
                process_factor = daily_factor * (0.9 + 0.2 * random.random())
        
        # Corrélations chimiques
        if sensor_type == SensorType.PH:
            # pH plus stable, faibles variations
            variance = 0.05
            process_factor = 0.98 + 0.04 * random.random()
        
        # Calcul final avec corrélations
        final_value = base_value * daily_factor * weather_factor * process_factor
        
        # Ajout bruit gaussien
        noise = random.gauss(0, base_value * variance)
        final_value += noise
        
        # Contraintes physiques réalistes
        if sensor_type == SensorType.PH:
            final_value = max(5.5, min(9.0, final_value))
        elif sensor_type == SensorType.OXYGEN_DISSOLVED:
            final_value = max(0, min(12.0, final_value))
        elif sensor_type == SensorType.TURBIDITY:
            final_value = max(0, final_value)
        elif sensor_type == SensorType.FLOW_RATE:
            final_value = max(0, final_value)
        
        return round(final_value, 3)

    def inject_anomaly(self, sensor_reading: SensorReading) -> SensorReading:
        """Injection d'anomalies réalistes controlées"""
        if random.random() > self.anomaly_probability:
            return sensor_reading  # Pas d'anomalie
        
        anomaly_types = [
            'sensor_failure',      # Panne capteur
            'drift',              # Dérive capteur  
            'pollution_spike',    # Pic pollution
            'process_malfunction',# Dysfonctionnement process
            'cyber_attack'        # Cyberattaque (simulation)
        ]
        
        anomaly_type = random.choice(anomaly_types)
        
        if anomaly_type == 'sensor_failure':
            # Capteur défaillant - valeurs aberrantes
            sensor_reading.value = float('inf') if random.random() > 0.5 else -999.0
            sensor_reading.confidence = 0.0
            sensor_reading.quality_grade = 'D'
            
        elif anomaly_type == 'drift':
            # Dérive progressive - biais multiplicatif
            drift_factor = 1 + random.uniform(-0.3, 0.8)
            sensor_reading.value *= drift_factor
            sensor_reading.confidence = 0.7
            sensor_reading.quality_grade = 'C'
            
        elif anomaly_type == 'pollution_spike':
            # Pic pollution - augmentation brutale COD, turbidité
            if sensor_reading.sensor_type in [SensorType.COD, SensorType.TURBIDITY, SensorType.SUSPENDED_SOLIDS]:
                sensor_reading.value *= random.uniform(2.5, 5.0)
                sensor_reading.confidence = 0.9
                sensor_reading.quality_grade = 'B'
                
        elif anomaly_type == 'process_malfunction':
            # Dysfonctionnement process - corrélations anormales
            if sensor_reading.sensor_type == SensorType.OXYGEN_DISSOLVED:
                sensor_reading.value *= 0.3  # Chute O2
            elif sensor_reading.sensor_type == SensorType.PH:
                sensor_reading.value += random.uniform(-1.5, 1.5)
            sensor_reading.confidence = 0.8
            sensor_reading.quality_grade = 'B'
            
        elif anomaly_type == 'cyber_attack':
            # Cyberattaque - manipulation données
            sensor_reading.value *= random.uniform(0.5, 2.0)
            sensor_reading.confidence = 0.6
            sensor_reading.quality_grade = 'C'
        
        sensor_reading.is_anomaly = True
        sensor_reading.anomaly_type = anomaly_type
        
        # Compteur Prometheus
        self.anomaly_counter.inc()
        
        logger.warning(f"🚨 Anomalie injectée: {anomaly_type} sur capteur {sensor_reading.sensor_id}")
        
        return sensor_reading

    async def generate_sensor_reading(self, sensor_config: Dict[str, Any]) -> SensorReading:
        """Génération lecture réaliste d'un capteur"""
        start_time = time.perf_counter()
        
        # Données météo
        weather = await self.get_weather_data()
        
        # Valeur corrélée
        value = self.calculate_correlated_values(sensor_config, weather)
        
        # Qualité signal (simulation ISA/IEC 62443)
        quality_grades = ['A', 'B', 'C', 'D']
        quality_weights = [0.85, 0.10, 0.04, 0.01]  # 85% grade A
        quality_grade = random.choices(quality_grades, weights=quality_weights)[0]
        
        # Création lecture capteur
        reading = SensorReading(
            sensor_id=sensor_config['id'],
            sensor_type=sensor_config['type'],
            process_stage=sensor_config['stage'],
            value=value,
            unit=self._get_unit_by_type(sensor_config['type']),
            timestamp=datetime.now(),
            location=sensor_config['location'],
            quality_grade=quality_grade,
            confidence=1.0 if quality_grade == 'A' else 0.8 if quality_grade == 'B' else 0.6 if quality_grade == 'C' else 0.3
        )
        
        # Injection éventuelle anomalies
        reading = self.inject_anomaly(reading)
        
        # Métriques Prometheus
        sensor_type_str = reading.sensor_type.value
        if f'{sensor_type_str}_current' in self.prometheus_gauges:
            self.prometheus_gauges[f'{sensor_type_str}_current'].labels(
                sensor_id=reading.sensor_id,
                process_stage=reading.process_stage.value,
                location=reading.location
            ).set(reading.value)
            
            self.prometheus_gauges[f'{sensor_type_str}_quality'].labels(
                sensor_id=reading.sensor_id,
                process_stage=reading.process_stage.value,
                location=reading.location
            ).set(reading.confidence)
        
        # Latence génération
        generation_time = time.perf_counter() - start_time
        self.data_generation_latency.observe(generation_time)
        
        return reading

    async def generate_all_sensors_data(self) -> List[SensorReading]:
        """Génération simultanée tous capteurs"""
        start_time = time.perf_counter()
        
        # Génération parallèle (simulation temps réel)
        tasks = [
            self.generate_sensor_reading(sensor_config) 
            for sensor_config in self.sensors_config
        ]
        
        readings = await asyncio.gather(*tasks)
        
        # Mise à jour métriques globales
        self.total_sensors.set(len(readings))
        
        # Calcul métriques process globaux
        inlet_flows = [r.value for r in readings if r.sensor_type == SensorType.FLOW_RATE and r.process_stage == ProcessStage.PRETREATMENT]
        if inlet_flows:
            self.inlet_flow.set(sum(inlet_flows))
        
        # Efficacité traitement (simulation)
        cod_inlet = [r.value for r in readings if r.sensor_type == SensorType.COD and r.process_stage == ProcessStage.PRETREATMENT]
        cod_outlet = [r.value for r in readings if r.sensor_type == SensorType.COD and r.process_stage == ProcessStage.OUTLET]
        
        if cod_inlet and cod_outlet:
            efficiency = (1 - sum(cod_outlet) / sum(cod_inlet)) * 100
            self.treatment_efficiency.set(max(0, min(100, efficiency)))
        
        # Consommation énergie
        energy_readings = [r.value for r in readings if r.sensor_type == SensorType.ENERGY_CONSUMPTION]
        if energy_readings:
            self.energy_consumption.set(sum(energy_readings))
        
        # Score conformité DERU (simulation)
        conformity_score = self.calculate_deru_compliance(readings)
        self.compliance_score.set(conformity_score)
        
        total_time = time.perf_counter() - start_time
        logger.info(f"📊 Génération {len(readings)} capteurs en {total_time:.3f}s")
        
        return readings

    def calculate_deru_compliance(self, readings: List[SensorReading]) -> float:
        """Calcul score conformité Directive DERU"""
        outlet_readings = [r for r in readings if r.process_stage == ProcessStage.OUTLET]
        
        compliant_readings = 0
        total_readings = len(outlet_readings)
        
        if total_readings == 0:
            return 100.0
        
        for reading in outlet_readings:
            is_compliant = False
            
            if reading.sensor_type == SensorType.COD and reading.value <= 125:  # mg/L
                is_compliant = True
            elif reading.sensor_type == SensorType.BOD and reading.value <= 25:  # mg/L
                is_compliant = True
            elif reading.sensor_type == SensorType.SUSPENDED_SOLIDS and reading.value <= 35:  # mg/L
                is_compliant = True
            elif reading.sensor_type == SensorType.NITROGEN and reading.value <= 15:  # mg/L
                is_compliant = True
            elif reading.sensor_type == SensorType.PHOSPHORUS and reading.value <= 2:  # mg/L
                is_compliant = True
            elif reading.sensor_type == SensorType.PH and 6.0 <= reading.value <= 9.0:
                is_compliant = True
            else:
                is_compliant = True  # Autres paramètres OK par défaut
                
            if is_compliant:
                compliant_readings += 1
        
        return round((compliant_readings / total_readings) * 100, 1)

    async def run_continuous_simulation(self, interval_seconds: int = 5):
        """Simulation continue avec intervalle configurable"""
        logger.info(f"🚀 Démarrage simulation continue - intervalle {interval_seconds}s")
        
        cycle_count = 0
        start_time = datetime.now()
        
        try:
            while True:
                cycle_start = time.perf_counter()
                
                # Génération cycle complet
                readings = await self.generate_all_sensors_data()
                
                # Stockage historique (limité aux dernières 1000 mesures)
                self.current_readings = {r.sensor_id: r for r in readings}
                self.historical_data.extend(readings)
                if len(self.historical_data) > 127000:  # 1000 cycles max
                    self.historical_data = self.historical_data[-127000:]
                
                cycle_count += 1
                cycle_time = time.perf_counter() - cycle_start
                
                # Stats toutes les 100 cycles
                if cycle_count % 100 == 0:
                    runtime = datetime.now() - start_time
                    avg_cycle_time = cycle_time
                    anomalies_count = len([r for r in readings if r.is_anomaly])
                    
                    logger.info(
                        f"📈 Cycle {cycle_count} | "
                        f"Runtime: {runtime} | "
                        f"Cycle time: {avg_cycle_time:.3f}s | "
                        f"Anomalies: {anomalies_count}/127 | "
                        f"Data points: {len(self.historical_data):,}"
                    )
                
                # Attente jusqu'au prochain cycle
                sleep_time = max(0, interval_seconds - cycle_time)
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt simulation demandé")
        except Exception as e:
            logger.error(f"❌ Erreur simulation: {e}")
        finally:
            logger.info(f"📊 Simulation terminée - {cycle_count} cycles, {len(self.historical_data):,} mesures")

    def export_to_json(self, filename: str = None) -> str:
        """Export données au format JSON"""
        if filename is None:
            filename = f"station_traffeyere_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'metadata': {
                'station_name': 'Station Épuration Traffeyère',
                'sensors_count': len(self.sensors_config),
                'generation_time': datetime.now().isoformat(),
                'weather_data': self.weather_data,
                'process_parameters': self.process_parameters
            },
            'current_readings': [
                asdict(reading) for reading in self.current_readings.values()
            ],
            'sensors_config': [
                {
                    **config,
                    'type': config['type'].value,
                    'stage': config['stage'].value
                }
                for config in self.sensors_config
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Données exportées vers {filename}")
        return filename

async def main():
    """Fonction principale - démarrage simulateur"""
    print("🏭 GÉNÉRATEUR IoT STATION TRAFFEYÈRE")
    print("=" * 50)
    print("127 capteurs - Données temps réel")
    print("Compatible Prometheus + Grafana")
    print("Anomalies + Corrélations physico-chimiques")
    print("=" * 50)
    
    # Démarrage serveur Prometheus
    start_http_server(8090)
    logger.info("📊 Serveur métriques Prometheus démarré sur http://localhost:8090")
    
    # Initialisation simulateur
    simulator = StationTraffeyereSimulator()
    
    # Test génération unique
    print("\n🧪 Test génération données...")
    readings = await simulator.generate_all_sensors_data()
    
    print(f"✅ {len(readings)} lectures générées")
    print(f"✅ Anomalies détectées: {len([r for r in readings if r.is_anomaly])}")
    print(f"✅ Qualité moyenne: {sum(r.confidence for r in readings)/len(readings):.2f}")
    
    # Export test
    filename = simulator.export_to_json()
    print(f"✅ Export test: {filename}")
    
    # Simulation continue
    print(f"\n🚀 Démarrage simulation continue...")
    print(f"📊 Métriques Prometheus: http://localhost:8090")
    print(f"⏹️ Arrêt: Ctrl+C")
    
    await simulator.run_continuous_simulation(interval_seconds=5)

if __name__ == "__main__":
    asyncio.run(main())
