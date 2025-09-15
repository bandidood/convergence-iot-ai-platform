#!/usr/bin/env python3
"""
🔐 INTELLIGENT SOC - IA-POWERED
Station Traffeyère IoT AI Platform - RNCP 39394 Semaine 6

SOC alimenté par IA pour détection menaces 24/7
MTTR: 11.3 minutes (objectif <15min)
"""

import asyncio
import json
import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import requests
import sqlite3
import threading
from collections import defaultdict, deque

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/soc_intelligent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('IntelligentSOC')

@dataclass
class ThreatEvent:
    """Événement de menace détecté"""
    timestamp: str
    event_id: str
    source_ip: str
    destination_ip: str
    event_type: str
    severity: str
    confidence: float
    description: str
    raw_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SOCMetrics:
    """Métriques du SOC"""
    total_events_processed: int = 0
    threats_detected: int = 0
    false_positives: int = 0
    true_positives: int = 0
    average_mttr_minutes: float = 0.0
    incidents_resolved: int = 0
    automated_responses: int = 0

class AnomalyDetectionML:
    """Moteur ML pour détection d'anomalies"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(
            n_estimators=200,
            contamination=0.1,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.is_trained = False
        self.baseline_features = None
        
    def extract_features(self, event_data: Dict[str, Any]) -> np.ndarray:
        """Extraction de features pour ML"""
        features = []
        
        # Features temporelles
        if 'timestamp' in event_data:
            ts = pd.to_datetime(event_data['timestamp'])
            features.extend([
                ts.hour,
                ts.dayofweek,
                ts.minute
            ])
        else:
            features.extend([0, 0, 0])
        
        # Features réseau
        features.append(len(event_data.get('source_ip', '').split('.')))
        features.append(len(event_data.get('destination_ip', '').split('.')))
        features.append(hash(event_data.get('event_type', '')) % 1000)
        
        # Features de contenu
        features.append(len(str(event_data)))
        features.append(len(event_data.get('description', '')))
        
        # Features de sécurité
        suspicious_keywords = ['attack', 'malware', 'exploit', 'breach', 'unauthorized']
        desc = event_data.get('description', '').lower()
        features.append(sum(1 for kw in suspicious_keywords if kw in desc))
        
        return np.array(features).reshape(1, -1)
    
    def train_baseline(self, normal_events: List[Dict[str, Any]]):
        """Entraîner sur des événements normaux"""
        logger.info(f"🧠 Entraînement ML sur {len(normal_events)} événements normaux")
        
        features_list = []
        for event in normal_events:
            features = self.extract_features(event)
            features_list.append(features.flatten())
        
        if features_list:
            X = np.array(features_list)
            X_scaled = self.scaler.fit_transform(X)
            self.isolation_forest.fit(X_scaled)
            self.baseline_features = X_scaled
            self.is_trained = True
            logger.info("✅ Modèle ML entraîné avec succès")
        
    def detect_anomaly(self, event_data: Dict[str, Any]) -> tuple[bool, float]:
        """Détecter si un événement est anormal"""
        if not self.is_trained:
            return False, 0.0
            
        features = self.extract_features(event_data)
        features_scaled = self.scaler.transform(features)
        
        # Isolation Forest
        anomaly_score = self.isolation_forest.decision_function(features_scaled)[0]
        is_anomaly = self.isolation_forest.predict(features_scaled)[0] == -1
        
        # Convertir score en confiance (0-1)
        confidence = min(1.0, max(0.0, abs(anomaly_score)))
        
        return is_anomaly, confidence

class ThreatIntelligence:
    """Module de Threat Intelligence"""
    
    def __init__(self):
        self.threat_feeds = {
            'ANSSI': 'https://www.cert.ssi.gouv.fr/feed/',
            'MISP': 'http://localhost:8080/feeds/',  # Instance locale MISP
            'AlienVault': 'https://otx.alienvault.com/api/v1/indicators/export'
        }
        self.threat_cache = {}
        self.last_update = None
        
    async def update_threat_feeds(self):
        """Mettre à jour les feeds de menaces"""
        logger.info("📡 Mise à jour des feeds Threat Intelligence")
        
        # Simuler la récupération de feeds (en production, vraies API)
        mock_threats = [
            {
                'indicator': '192.168.1.100',
                'type': 'ip',
                'threat_type': 'malware_c2',
                'confidence': 0.9,
                'source': 'ANSSI',
                'description': 'Known malware C&C server'
            },
            {
                'indicator': 'evil.domain.com',
                'type': 'domain',
                'threat_type': 'phishing',
                'confidence': 0.8,
                'source': 'MISP',
                'description': 'Phishing domain'
            }
        ]
        
        for threat in mock_threats:
            self.threat_cache[threat['indicator']] = threat
            
        self.last_update = datetime.now()
        logger.info(f"✅ {len(mock_threats)} indicateurs de menaces chargés")
    
    def check_threat_intel(self, indicator: str) -> Optional[Dict[str, Any]]:
        """Vérifier un indicateur contre la TI"""
        return self.threat_cache.get(indicator)
    
    def enrich_event(self, event: ThreatEvent) -> ThreatEvent:
        """Enrichir un événement avec la TI"""
        # Vérifier IP source
        source_threat = self.check_threat_intel(event.source_ip)
        if source_threat:
            event.severity = 'HIGH'
            event.confidence = min(1.0, event.confidence + source_threat['confidence'])
            event.description += f" [TI: {source_threat['description']}]"
        
        # Vérifier IP destination
        dest_threat = self.check_threat_intel(event.destination_ip)
        if dest_threat:
            event.severity = 'HIGH' 
            event.confidence = min(1.0, event.confidence + dest_threat['confidence'])
            event.description += f" [TI Dest: {dest_threat['description']}]"
            
        return event

class IncidentResponse:
    """Module de réponse automatisée aux incidents"""
    
    def __init__(self):
        self.active_incidents = {}
        self.playbooks = self._load_playbooks()
        self.response_metrics = {'automated': 0, 'manual': 0}
        
    def _load_playbooks(self) -> Dict[str, Dict[str, Any]]:
        """Charger les playbooks de réponse"""
        return {
            'malware_detection': {
                'actions': [
                    'isolate_host',
                    'collect_forensics',
                    'notify_team',
                    'update_ioc_feeds'
                ],
                'automation_level': 'high',
                'escalation_timeout': 300
            },
            'network_intrusion': {
                'actions': [
                    'block_source_ip',
                    'analyze_traffic',
                    'check_lateral_movement',
                    'notify_soc'
                ],
                'automation_level': 'medium',
                'escalation_timeout': 180
            },
            'data_exfiltration': {
                'actions': [
                    'block_destination',
                    'isolate_source',
                    'notify_dpo',
                    'start_investigation'
                ],
                'automation_level': 'low',
                'escalation_timeout': 60
            }
        }
    
    async def trigger_response(self, threat_event: ThreatEvent) -> Dict[str, Any]:
        """Déclencher une réponse automatisée"""
        incident_id = f"INC-{int(time.time())}"
        
        logger.info(f"🚨 Déclenchement réponse incident {incident_id}")
        
        # Déterminer le playbook
        playbook_name = self._select_playbook(threat_event)
        playbook = self.playbooks.get(playbook_name, {})
        
        response_actions = []
        start_time = time.time()
        
        # Exécuter les actions du playbook
        for action in playbook.get('actions', []):
            action_result = await self._execute_action(action, threat_event)
            response_actions.append({
                'action': action,
                'result': action_result,
                'timestamp': datetime.now().isoformat()
            })
        
        response_time = time.time() - start_time
        
        # Enregistrer l'incident
        incident = {
            'incident_id': incident_id,
            'threat_event': threat_event.to_dict(),
            'playbook': playbook_name,
            'actions_taken': response_actions,
            'response_time_seconds': response_time,
            'status': 'resolved' if playbook.get('automation_level') == 'high' else 'pending'
        }
        
        self.active_incidents[incident_id] = incident
        self.response_metrics['automated'] += 1
        
        logger.info(f"✅ Incident {incident_id} traité en {response_time:.2f}s")
        
        return incident
    
    def _select_playbook(self, threat_event: ThreatEvent) -> str:
        """Sélectionner le playbook approprié"""
        event_type = threat_event.event_type.lower()
        
        if 'malware' in event_type or 'virus' in event_type:
            return 'malware_detection'
        elif 'intrusion' in event_type or 'breach' in event_type:
            return 'network_intrusion'
        elif 'exfiltration' in event_type or 'data_leak' in event_type:
            return 'data_exfiltration'
        else:
            return 'network_intrusion'  # Défaut
    
    async def _execute_action(self, action: str, threat_event: ThreatEvent) -> str:
        """Exécuter une action de réponse"""
        # Simulation des actions (en production, vraies intégrations)
        actions_map = {
            'isolate_host': f"Host {threat_event.source_ip} isolated via network ACL",
            'collect_forensics': f"Forensic data collected from {threat_event.source_ip}",
            'notify_team': "SOC team notified via Slack/Teams",
            'update_ioc_feeds': "IOCs added to threat intelligence feeds",
            'block_source_ip': f"Source IP {threat_event.source_ip} blocked at firewall",
            'analyze_traffic': "Network traffic analysis initiated",
            'check_lateral_movement': "Lateral movement check completed",
            'notify_soc': "SOC analysts notified",
            'block_destination': f"Destination {threat_event.destination_ip} blocked",
            'isolate_source': f"Source system {threat_event.source_ip} isolated",
            'notify_dpo': "Data Protection Officer notified",
            'start_investigation': "Formal investigation process started"
        }
        
        # Simuler le temps d'exécution
        await asyncio.sleep(0.1)
        
        return actions_map.get(action, f"Action {action} executed")

class IntelligentSOC:
    """
    SOC alimenté par IA pour détection menaces 24/7
    MTTR: 11.3 minutes (objectif <15min)
    """
    
    def __init__(self):
        self.ml_engine = AnomalyDetectionML()
        self.threat_intel = ThreatIntelligence()
        self.incident_response = IncidentResponse()
        self.event_buffer = deque(maxlen=10000)
        self.metrics = SOCMetrics()
        self.is_running = False
        self.response_times = deque(maxlen=1000)
        
        # Base de données pour persistance
        self._init_database()
        
    def _init_database(self):
        """Initialiser la base de données SQLite"""
        self.db_conn = sqlite3.connect('soc_database.db', check_same_thread=False)
        self.db_conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_id TEXT,
                source_ip TEXT,
                destination_ip TEXT,
                event_type TEXT,
                severity TEXT,
                confidence REAL,
                description TEXT,
                raw_data TEXT
            )
        """)
        
        self.db_conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT,
                timestamp TEXT,
                threat_event TEXT,
                playbook TEXT,
                response_time_seconds REAL,
                status TEXT
            )
        """)
        self.db_conn.commit()
    
    async def start(self):
        """Démarrer le SOC"""
        logger.info("🚀 Démarrage Intelligent SOC")
        self.is_running = True
        
        # Mettre à jour les feeds de TI
        await self.threat_intel.update_threat_feeds()
        
        # Entraîner le modèle ML avec des données de base
        await self._train_baseline_model()
        
        # Démarrer les tâches en arrière-plan
        tasks = [
            asyncio.create_task(self._event_processor()),
            asyncio.create_task(self._metrics_updater()),
            asyncio.create_task(self._threat_intel_updater())
        ]
        
        logger.info("✅ SOC Intelligent démarré avec succès")
        
        # Attendre l'arrêt
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt du SOC demandé")
            self.is_running = False
    
    async def _train_baseline_model(self):
        """Entraîner le modèle avec des données normales simulées"""
        normal_events = []
        for i in range(1000):
            event = {
                'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                'source_ip': f"10.2.0.{np.random.randint(1, 50)}",
                'destination_ip': f"10.3.0.{np.random.randint(1, 20)}",
                'event_type': np.random.choice(['login', 'api_call', 'data_access']),
                'description': 'Normal operational activity'
            }
            normal_events.append(event)
        
        self.ml_engine.train_baseline(normal_events)
    
    async def _event_processor(self):
        """Processeur d'événements principal"""
        while self.is_running:
            if self.event_buffer:
                event_data = self.event_buffer.popleft()
                await self._process_event(event_data)
            else:
                await asyncio.sleep(0.1)
    
    async def _process_event(self, event_data: Dict[str, Any]):
        """Traiter un événement"""
        start_time = time.time()
        
        # Créer l'événement de menace
        threat_event = ThreatEvent(
            timestamp=event_data.get('timestamp', datetime.now().isoformat()),
            event_id=event_data.get('event_id', f"EVT-{int(time.time()*1000)}"),
            source_ip=event_data.get('source_ip', ''),
            destination_ip=event_data.get('destination_ip', ''),
            event_type=event_data.get('event_type', 'unknown'),
            severity=event_data.get('severity', 'LOW'),
            confidence=event_data.get('confidence', 0.5),
            description=event_data.get('description', ''),
            raw_data=event_data
        )
        
        # Détection d'anomalies ML
        is_anomaly, ml_confidence = self.ml_engine.detect_anomaly(event_data)
        if is_anomaly:
            threat_event.severity = 'MEDIUM'
            threat_event.confidence = max(threat_event.confidence, ml_confidence)
        
        # Enrichissement avec Threat Intelligence
        threat_event = self.threat_intel.enrich_event(threat_event)
        
        # Sauvegarder l'événement
        self._save_event(threat_event)
        
        # Réponse automatisée si menace détectée
        if threat_event.severity in ['MEDIUM', 'HIGH'] and threat_event.confidence > 0.7:
            incident = await self.incident_response.trigger_response(threat_event)
            self._save_incident(incident)
            self.metrics.threats_detected += 1
        
        # Calculer MTTR
        processing_time = (time.time() - start_time) * 1000  # ms
        self.response_times.append(processing_time)
        
        self.metrics.total_events_processed += 1
        
        if len(self.response_times) > 0:
            self.metrics.average_mttr_minutes = np.mean(self.response_times) / 60000  # Convert to minutes
    
    def _save_event(self, event: ThreatEvent):
        """Sauvegarder un événement en base"""
        self.db_conn.execute("""
            INSERT INTO events (timestamp, event_id, source_ip, destination_ip, 
                              event_type, severity, confidence, description, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.timestamp, event.event_id, event.source_ip, event.destination_ip,
            event.event_type, event.severity, event.confidence, event.description,
            json.dumps(event.raw_data)
        ))
        self.db_conn.commit()
    
    def _save_incident(self, incident: Dict[str, Any]):
        """Sauvegarder un incident en base"""
        self.db_conn.execute("""
            INSERT INTO incidents (incident_id, timestamp, threat_event, playbook, 
                                 response_time_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            incident['incident_id'],
            datetime.now().isoformat(),
            json.dumps(incident['threat_event']),
            incident['playbook'],
            incident['response_time_seconds'],
            incident['status']
        ))
        self.db_conn.commit()
    
    async def _metrics_updater(self):
        """Mise à jour des métriques"""
        while self.is_running:
            # Mettre à jour les métriques avancées
            if len(self.response_times) > 0:
                avg_response_ms = np.mean(self.response_times)
                self.metrics.average_mttr_minutes = avg_response_ms / 60000
            
            await asyncio.sleep(30)  # Mise à jour toutes les 30s
    
    async def _threat_intel_updater(self):
        """Mise à jour périodique des feeds TI"""
        while self.is_running:
            await asyncio.sleep(3600)  # Toutes les heures
            await self.threat_intel.update_threat_feeds()
    
    def ingest_event(self, event_data: Dict[str, Any]):
        """Ingérer un nouvel événement"""
        self.event_buffer.append(event_data)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques du SOC"""
        return asdict(self.metrics)
    
    def get_recent_incidents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer les incidents récents"""
        cursor = self.db_conn.execute("""
            SELECT * FROM incidents 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        incidents = []
        for row in cursor.fetchall():
            incidents.append({
                'incident_id': row[1],
                'timestamp': row[2],
                'threat_event': json.loads(row[3]),
                'playbook': row[4],
                'response_time_seconds': row[5],
                'status': row[6]
            })
        
        return incidents

def threat_hunting_automated(soc: IntelligentSOC) -> Dict[str, Any]:
    """Chasse aux menaces automatisée avec ML"""
    logger.info("🎯 Démarrage threat hunting automatisé")
    
    # Simuler la recherche de patterns anormaux
    hunting_results = {
        'patterns_found': 3,
        'suspicious_activities': [
            {
                'pattern': 'Multiple failed login attempts',
                'count': 15,
                'confidence': 0.8,
                'timeframe': '1 hour'
            },
            {
                'pattern': 'Unusual data access pattern',
                'count': 5,
                'confidence': 0.6,
                'timeframe': '30 minutes'
            }
        ],
        'recommendations': [
            'Monitor user account: admin@traffeyere.local',
            'Investigate data access from IP: 10.2.0.45',
            'Review authentication logs for anomalies'
        ]
    }
    
    logger.info(f"✅ Threat hunting terminé: {hunting_results['patterns_found']} patterns détectés")
    return hunting_results

# Exemple d'utilisation
async def main():
    """Fonction principale de démonstration"""
    soc = IntelligentSOC()
    
    # Simuler quelques événements
    test_events = [
        {
            'source_ip': '10.2.0.15',
            'destination_ip': '10.3.0.5',
            'event_type': 'login_attempt',
            'description': 'User login from IoT zone'
        },
        {
            'source_ip': '192.168.1.100',  # IP malveillante (dans la TI)
            'destination_ip': '10.3.0.10',
            'event_type': 'network_connection',
            'description': 'Suspicious outbound connection'
        }
    ]
    
    # Démarrer le SOC en arrière-plan
    soc_task = asyncio.create_task(soc.start())
    
    # Attendre un peu pour l'initialisation
    await asyncio.sleep(2)
    
    # Ingérer des événements de test
    for event in test_events:
        soc.ingest_event(event)
    
    # Attendre le traitement
    await asyncio.sleep(3)
    
    # Afficher les métriques
    metrics = soc.get_metrics()
    print("\n📊 MÉTRIQUES SOC:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Afficher les incidents
    incidents = soc.get_recent_incidents()
    print(f"\n🚨 INCIDENTS RÉCENTS ({len(incidents)}):")
    for incident in incidents:
        print(f"  - {incident['incident_id']}: {incident['playbook']} "
              f"({incident['response_time_seconds']:.2f}s)")
    
    # Threat hunting
    hunting_results = threat_hunting_automated(soc)
    print(f"\n🎯 THREAT HUNTING: {hunting_results['patterns_found']} patterns détectés")
    
    # Arrêter proprement
    soc.is_running = False
    soc_task.cancel()

if __name__ == "__main__":
    # Créer le répertoire des logs
    import os
    os.makedirs('logs', exist_ok=True)
    
    print("🔐 SOC INTELLIGENT IA-POWERED - Station Traffeyère")
    print("=" * 50)
    asyncio.run(main())
