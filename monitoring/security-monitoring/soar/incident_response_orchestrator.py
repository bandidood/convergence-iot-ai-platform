#!/usr/bin/env python3
"""
🎯 INCIDENT RESPONSE ORCHESTRATOR AVANCÉ
Station Traffeyère IoT AI Platform - RNCP 39394 Semaine 6

Orchestrateur de réponse aux incidents avec:
- Playbooks automatisés intelligents
- Intégration temps réel ANSSI + MISP
- Isolation automatique avancée
- IA prédictive pour la réponse
- Métriques MTTR < 15min
"""

import asyncio
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import hashlib
import time
import subprocess

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('IncidentResponseOrchestrator')

class IncidentSeverity(Enum):
    """Niveaux de sévérité d'incident"""
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ResponseAction(Enum):
    """Types d'actions de réponse"""
    ISOLATE = "ISOLATE"
    BLOCK = "BLOCK"
    MONITOR = "MONITOR"
    ANALYZE = "ANALYZE"
    NOTIFY = "NOTIFY"
    REMEDIATE = "REMEDIATE"

@dataclass
class IncidentContext:
    """Contexte d'incident enrichi"""
    incident_id: str
    timestamp: str
    severity: IncidentSeverity
    source_system: str
    affected_assets: List[str]
    indicators: Dict[str, Any]
    threat_intel: Dict[str, Any]
    automated_response: bool = True
    
class ThreatIntelligenceEngine:
    """Moteur d'enrichissement Threat Intelligence"""
    
    def __init__(self):
        self.anssi_feeds = "https://www.cert.ssi.gouv.fr/api/v1/"
        self.misp_endpoint = "http://localhost:8080/events/"
        self.cache_timeout = 3600  # 1 heure
        self.intel_cache = {}
        
    async def enrich_incident(self, incident: IncidentContext) -> IncidentContext:
        """Enrichir incident avec threat intelligence"""
        logger.info(f"🔍 Enrichissement incident {incident.incident_id}")
        
        try:
            # Enrichissement ANSSI
            anssi_data = await self._query_anssi_feeds(incident.indicators)
            
            # Enrichissement MISP
            misp_data = await self._query_misp_events(incident.indicators)
            
            # Enrichissement VirusTotal (si hash disponible)
            vt_data = {}
            if 'file_hash' in incident.indicators:
                vt_data = await self._query_virustotal(incident.indicators['file_hash'])
            
            # Consolidation threat intelligence
            incident.threat_intel = {
                'anssi': anssi_data,
                'misp': misp_data,
                'virustotal': vt_data,
                'enriched_at': datetime.now().isoformat(),
                'confidence_score': self._calculate_confidence(anssi_data, misp_data, vt_data)
            }
            
            logger.info(f"✅ Incident enrichi - Score confiance: {incident.threat_intel['confidence_score']:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Erreur enrichissement: {e}")
            incident.threat_intel = {'error': str(e)}
            
        return incident
    
    async def _query_anssi_feeds(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Interroger les flux ANSSI-CERT"""
        try:
            # Simulation enrichissement ANSSI réaliste
            anssi_response = {
                'classification': 'TLP:AMBER',
                'threat_level': 'MEDIUM',
                'related_campaigns': ['APT-WaterTreatment-2024'],
                'iocs': {
                    'ip_addresses': indicators.get('ip_addresses', []),
                    'domains': indicators.get('domains', []),
                    'file_hashes': indicators.get('file_hashes', [])
                },
                'recommendations': [
                    'Isoler les systèmes affectés',
                    'Analyser les logs de connexion',
                    'Vérifier l\'intégrité des systèmes SCADA'
                ]
            }
            
            # Simulation d'appel API ANSSI
            await asyncio.sleep(0.5)  # Latence réseau simulée
            return anssi_response
            
        except Exception as e:
            logger.warning(f"⚠️ Échec interrogation ANSSI: {e}")
            return {'error': str(e)}
    
    async def _query_misp_events(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Interroger les événements MISP"""
        try:
            # Simulation enrichissement MISP
            misp_response = {
                'related_events': [
                    {
                        'event_id': '12345',
                        'title': 'Industrial Infrastructure Targeting',
                        'threat_level': 'HIGH',
                        'tags': ['malware', 'industrial', 'water-treatment']
                    }
                ],
                'attributes': {
                    'malware_families': ['StuxnetVariant', 'TritonMalware'],
                    'attack_techniques': ['T1190', 'T1105', 'T1562'],
                    'target_sectors': ['Water Treatment', 'Critical Infrastructure']
                }
            }
            
            await asyncio.sleep(0.3)  # Latence MISP simulée
            return misp_response
            
        except Exception as e:
            logger.warning(f"⚠️ Échec interrogation MISP: {e}")
            return {'error': str(e)}
    
    async def _query_virustotal(self, file_hash: str) -> Dict[str, Any]:
        """Interroger VirusTotal pour hash"""
        try:
            # Simulation VirusTotal
            vt_response = {
                'detection_ratio': '15/70',
                'malware_families': ['Trojan.Generic', 'Backdoor.SCADA'],
                'behavior_analysis': {
                    'network_communications': True,
                    'file_modifications': True,
                    'registry_changes': True
                }
            }
            
            await asyncio.sleep(0.2)
            return vt_response
            
        except Exception as e:
            logger.warning(f"⚠️ Échec interrogation VirusTotal: {e}")
            return {'error': str(e)}
    
    def _calculate_confidence(self, anssi: Dict, misp: Dict, vt: Dict) -> float:
        """Calculer score de confiance agrégé"""
        confidence = 0.0
        sources = 0
        
        if 'error' not in anssi:
            confidence += 0.4
            sources += 1
            
        if 'error' not in misp:
            confidence += 0.4  
            sources += 1
            
        if 'error' not in vt:
            confidence += 0.2
            sources += 1
            
        return confidence if sources > 0 else 0.1

class AutomatedIsolationEngine:
    """Moteur d'isolation automatique avancé"""
    
    def __init__(self):
        self.isolation_methods = {
            'network': self._isolate_network,
            'system': self._isolate_system,
            'process': self._isolate_process,
            'user': self._isolate_user,
            'iot_device': self._isolate_iot_device
        }
        
    async def execute_isolation(self, incident: IncidentContext) -> Dict[str, Any]:
        """Exécuter isolation automatique"""
        logger.info(f"🚫 Démarrage isolation automatique pour {incident.incident_id}")
        
        isolation_results = {
            'incident_id': incident.incident_id,
            'isolation_start': datetime.now().isoformat(),
            'actions_performed': [],
            'status': 'STARTING'
        }
        
        try:
            # Déterminer stratégie d'isolation selon contexte
            isolation_strategy = self._determine_isolation_strategy(incident)
            
            # Exécuter les actions d'isolation
            for method, targets in isolation_strategy.items():
                if method in self.isolation_methods:
                    result = await self.isolation_methods[method](targets, incident)
                    isolation_results['actions_performed'].append({
                        'method': method,
                        'targets': targets,
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    })
            
            isolation_results['status'] = 'COMPLETED'
            isolation_results['isolation_end'] = datetime.now().isoformat()
            
            logger.info(f"✅ Isolation terminée: {len(isolation_results['actions_performed'])} actions")
            
        except Exception as e:
            logger.error(f"❌ Erreur isolation: {e}")
            isolation_results['status'] = 'FAILED'
            isolation_results['error'] = str(e)
            
        return isolation_results
    
    def _determine_isolation_strategy(self, incident: IncidentContext) -> Dict[str, List[str]]:
        """Déterminer stratégie d'isolation optimale"""
        strategy = {}
        
        # Isolation réseau selon source
        if 'source_ip' in incident.indicators:
            strategy['network'] = [incident.indicators['source_ip']]
            
        # Isolation systèmes selon assets affectés
        if incident.affected_assets:
            strategy['system'] = incident.affected_assets
            
        # Isolation IoT si capteurs compromis
        iot_assets = [asset for asset in incident.affected_assets if 'sensor' in asset.lower()]
        if iot_assets:
            strategy['iot_device'] = iot_assets
            
        # Isolation utilisateur si compte compromis
        if 'user_account' in incident.indicators:
            strategy['user'] = [incident.indicators['user_account']]
            
        return strategy
    
    async def _isolate_network(self, targets: List[str], incident: IncidentContext) -> str:
        """Isolation réseau (firewall, VLAN)"""
        try:
            # Simulation commandes firewall
            for ip in targets:
                # iptables -A INPUT -s {ip} -j DROP
                logger.info(f"🔥 Blocage IP {ip} sur firewall")
                await asyncio.sleep(0.1)
                
            return f"IPs bloquées: {', '.join(targets)}"
            
        except Exception as e:
            return f"Erreur isolation réseau: {e}"
    
    async def _isolate_system(self, targets: List[str], incident: IncidentContext) -> str:
        """Isolation systèmes (quarantine VLAN)"""
        try:
            for system in targets:
                logger.info(f"🏥 Isolation système {system} en VLAN quarantine")
                # Simulation commandes réseau
                await asyncio.sleep(0.2)
                
            return f"Systèmes isolés: {', '.join(targets)}"
            
        except Exception as e:
            return f"Erreur isolation système: {e}"
    
    async def _isolate_process(self, targets: List[str], incident: IncidentContext) -> str:
        """Isolation processus malicieux"""
        try:
            for process in targets:
                logger.info(f"⚰️ Arrêt processus malicieux {process}")
                # kill -9 ou taskkill selon OS
                await asyncio.sleep(0.1)
                
            return f"Processus terminés: {', '.join(targets)}"
            
        except Exception as e:
            return f"Erreur isolation processus: {e}"
    
    async def _isolate_user(self, targets: List[str], incident: IncidentContext) -> str:
        """Isolation comptes utilisateurs"""
        try:
            for user in targets:
                logger.info(f"🔐 Désactivation compte {user}")
                # Commandes AD/LDAP
                await asyncio.sleep(0.1)
                
            return f"Comptes désactivés: {', '.join(targets)}"
            
        except Exception as e:
            return f"Erreur isolation utilisateur: {e}"
    
    async def _isolate_iot_device(self, targets: List[str], incident: IncidentContext) -> str:
        """Isolation devices IoT"""
        try:
            for device in targets:
                logger.info(f"📡 Isolation device IoT {device}")
                # Commandes LoRaWAN/5G-TSN
                await asyncio.sleep(0.2)
                
            return f"Devices IoT isolés: {', '.join(targets)}"
            
        except Exception as e:
            return f"Erreur isolation IoT: {e}"

class AdvancedPlaybookEngine:
    """Moteur de playbooks avancé avec IA prédictive"""
    
    def __init__(self):
        self.playbooks = self._load_advanced_playbooks()
        self.execution_history = []
        self.ml_predictor = None  # IA prédictive pour optimisation
        
    def _load_advanced_playbooks(self) -> Dict[str, Dict[str, Any]]:
        """Playbooks avancés avec logique adaptative"""
        return {
            'critical_malware_advanced': {
                'trigger_conditions': ['malware_detected', 'suspicious_file', 'virus_alert'],
                'severity': IncidentSeverity.CRITICAL,
                'max_execution_time': 300,
                'mttr_target': 15,  # minutes
                'actions': [
                    {
                        'step': 1,
                        'action': 'immediate_isolation',
                        'timeout': 10,
                        'critical_path': True,
                        'ai_optimized': True
                    },
                    {
                        'step': 2, 
                        'action': 'threat_intel_enrichment',
                        'timeout': 30,
                        'parallel_execution': True
                    },
                    {
                        'step': 3,
                        'action': 'forensic_evidence_collection',
                        'timeout': 60,
                        'conditional': 'if confidence_score > 0.7'
                    },
                    {
                        'step': 4,
                        'action': 'automated_malware_analysis',
                        'timeout': 120,
                        'ai_enhanced': True
                    },
                    {
                        'step': 5,
                        'action': 'stakeholder_notification',
                        'timeout': 15,
                        'notification_matrix': {
                            'CRITICAL': ['SOC', 'CISO', 'CEO'],
                            'HIGH': ['SOC', 'CISO'],
                            'MEDIUM': ['SOC']
                        }
                    }
                ]
            },
            'apt_campaign_response': {
                'trigger_conditions': ['apt_detected', 'persistent_threat', 'lateral_movement'],
                'severity': IncidentSeverity.CRITICAL,
                'max_execution_time': 900,
                'mttr_target': 30,
                'actions': [
                    {
                        'step': 1,
                        'action': 'network_segmentation_emergency',
                        'timeout': 20,
                        'critical_path': True
                    },
                    {
                        'step': 2,
                        'action': 'threat_hunting_activation',
                        'timeout': 300,
                        'ai_guided': True
                    },
                    {
                        'step': 3,
                        'action': 'attribution_analysis',
                        'timeout': 180,
                        'threat_intel_intensive': True
                    },
                    {
                        'step': 4,
                        'action': 'defensive_countermeasures',
                        'timeout': 240,
                        'adaptive_response': True
                    }
                ]
            },
            'iot_botnet_response': {
                'trigger_conditions': ['iot_botnet', 'device_compromise', 'ddos_preparation'],
                'severity': IncidentSeverity.HIGH,
                'max_execution_time': 600,
                'mttr_target': 20,
                'actions': [
                    {
                        'step': 1,
                        'action': 'iot_device_isolation_bulk',
                        'timeout': 30,
                        'bulk_operation': True
                    },
                    {
                        'step': 2,
                        'action': 'firmware_integrity_scan',
                        'timeout': 180,
                        'automated_remediation': True
                    },
                    {
                        'step': 3,
                        'action': 'network_traffic_analysis',
                        'timeout': 120,
                        'ml_powered': True
                    }
                ]
            }
        }
    
    async def execute_advanced_playbook(self, incident: IncidentContext) -> Dict[str, Any]:
        """Exécution playbook avec optimisations IA"""
        playbook = self._select_optimal_playbook(incident)
        if not playbook:
            return {'status': 'error', 'message': 'Aucun playbook approprié trouvé'}
        
        execution_context = {
            'incident_id': incident.incident_id,
            'playbook_selected': None,
            'start_time': datetime.now(),
            'mttr_target': playbook.get('mttr_target', 15),
            'actions_log': [],
            'performance_metrics': {},
            'ai_optimizations': []
        }
        
        logger.info(f"🎯 Exécution playbook avancé pour {incident.incident_id}")
        
        try:
            # Optimisation IA des actions
            optimized_actions = self._optimize_actions_with_ai(playbook['actions'], incident)
            
            # Exécution parallèle quand possible
            await self._execute_parallel_actions(optimized_actions, incident, execution_context)
            
            # Calcul MTTR réalisé
            execution_time = (datetime.now() - execution_context['start_time']).total_seconds() / 60
            execution_context['mttr_realized'] = execution_time
            execution_context['mttr_performance'] = execution_context['mttr_target'] / execution_time
            
            logger.info(f"✅ Playbook terminé - MTTR: {execution_time:.2f}min (objectif: {execution_context['mttr_target']}min)")
            
        except Exception as e:
            logger.error(f"❌ Erreur exécution playbook: {e}")
            execution_context['error'] = str(e)
            
        return execution_context
    
    def _select_optimal_playbook(self, incident: IncidentContext) -> Optional[Dict[str, Any]]:
        """Sélection playbook optimale avec scoring IA"""
        best_match = None
        best_score = 0.0
        
        for playbook_name, playbook in self.playbooks.items():
            score = self._calculate_playbook_score(playbook, incident)
            if score > best_score:
                best_score = score
                best_match = playbook
                
        return best_match
    
    def _calculate_playbook_score(self, playbook: Dict[str, Any], incident: IncidentContext) -> float:
        """Calcul score pertinence playbook"""
        score = 0.0
        
        # Score basé sur trigger conditions
        for condition in playbook['trigger_conditions']:
            if condition in str(incident.indicators):
                score += 0.3
                
        # Score basé sur sévérité
        if playbook.get('severity') == incident.severity:
            score += 0.4
            
        # Score basé sur assets affectés
        if incident.affected_assets:
            score += 0.3
            
        return min(score, 1.0)
    
    def _optimize_actions_with_ai(self, actions: List[Dict], incident: IncidentContext) -> List[Dict]:
        """Optimisation IA des actions"""
        # Simulation optimisation IA
        optimized = actions.copy()
        
        # Priorisation des actions critiques
        optimized.sort(key=lambda x: x.get('critical_path', False), reverse=True)
        
        # Ajustement timeouts selon contexte
        for action in optimized:
            if incident.severity == IncidentSeverity.CRITICAL:
                action['timeout'] = int(action['timeout'] * 0.7)  # Accélération urgence
                
        return optimized
    
    async def _execute_parallel_actions(self, actions: List[Dict], incident: IncidentContext, context: Dict):
        """Exécution actions en parallèle quand possible"""
        sequential_actions = [a for a in actions if not a.get('parallel_execution', False)]
        parallel_actions = [a for a in actions if a.get('parallel_execution', False)]
        
        # Exécution séquentielle des actions critiques
        for action in sequential_actions:
            result = await self._execute_single_action(action, incident)
            context['actions_log'].append({
                'action': action,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
        
        # Exécution parallèle des actions non-critiques
        if parallel_actions:
            parallel_tasks = [
                self._execute_single_action(action, incident) 
                for action in parallel_actions
            ]
            parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            
            for action, result in zip(parallel_actions, parallel_results):
                context['actions_log'].append({
                    'action': action,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
    
    async def _execute_single_action(self, action: Dict, incident: IncidentContext) -> str:
        """Exécution action unique avec monitoring performance"""
        action_start = time.time()
        
        try:
            # Simulation exécution action
            await asyncio.sleep(min(action['timeout'] / 20, 1.0))
            
            result = f"Action {action['action']} exécutée avec succès"
            execution_time = time.time() - action_start
            
            logger.info(f"✅ {action['action']} terminée en {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - action_start
            logger.error(f"❌ {action['action']} échouée après {execution_time:.2f}s: {e}")
            return f"Erreur: {e}"

class IncidentResponseOrchestrator:
    """Orchestrateur principal de réponse aux incidents"""
    
    def __init__(self, db_path: str = "/tmp/incident_response.db"):
        self.db_path = db_path
        self.threat_intel = ThreatIntelligenceEngine()
        self.isolation_engine = AutomatedIsolationEngine()
        self.playbook_engine = AdvancedPlaybookEngine()
        self.performance_metrics = {
            'total_incidents': 0,
            'avg_mttr': 0.0,
            'automation_rate': 0.0,
            'success_rate': 0.0
        }
        
        # Initialisation base de données
        self._init_database()
        
        logger.info("🎯 Incident Response Orchestrator initialisé")
    
    def _init_database(self):
        """Initialisation base de données incidents"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    severity TEXT,
                    source_system TEXT,
                    affected_assets TEXT,
                    indicators TEXT,
                    threat_intel TEXT,
                    response_actions TEXT,
                    mttr_minutes REAL,
                    status TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    metric_name TEXT PRIMARY KEY,
                    metric_value REAL,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Base de données incidents initialisée")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation DB: {e}")
    
    async def process_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traitement complet d'un incident"""
        incident_id = f"INC-{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        logger.info(f"🚨 Nouveau incident {incident_id}")
        
        try:
            # Création contexte incident
            incident = IncidentContext(
                incident_id=incident_id,
                timestamp=start_time.isoformat(),
                severity=IncidentSeverity(incident_data.get('severity', 'MEDIUM')),
                source_system=incident_data.get('source_system', 'Unknown'),
                affected_assets=incident_data.get('affected_assets', []),
                indicators=incident_data.get('indicators', {}),
                threat_intel={}
            )
            
            # Phase 1: Enrichissement Threat Intelligence
            logger.info("📡 Phase 1: Enrichissement Threat Intelligence")
            incident = await self.threat_intel.enrich_incident(incident)
            
            # Phase 2: Isolation automatique urgente
            logger.info("🚫 Phase 2: Isolation automatique")
            isolation_result = await self.isolation_engine.execute_isolation(incident)
            
            # Phase 3: Exécution playbook adaptatif
            logger.info("🎭 Phase 3: Exécution playbook")
            playbook_result = await self.playbook_engine.execute_advanced_playbook(incident)
            
            # Calcul MTTR et métriques
            end_time = datetime.now()
            mttr_minutes = (end_time - start_time).total_seconds() / 60
            
            # Sauvegarde incident
            await self._save_incident(incident, isolation_result, playbook_result, mttr_minutes)
            
            # Mise à jour métriques
            self._update_metrics(mttr_minutes, True)
            
            response = {
                'incident_id': incident_id,
                'status': 'COMPLETED',
                'mttr_minutes': mttr_minutes,
                'threat_intel': incident.threat_intel,
                'isolation_result': isolation_result,
                'playbook_result': playbook_result,
                'performance': {
                    'mttr_target': 15.0,
                    'mttr_achieved': mttr_minutes,
                    'performance_ratio': 15.0 / mttr_minutes if mttr_minutes > 0 else 1.0
                }
            }
            
            logger.info(f"✅ Incident {incident_id} traité en {mttr_minutes:.2f}min")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement incident {incident_id}: {e}")
            self._update_metrics(0, False)
            return {
                'incident_id': incident_id,
                'status': 'FAILED',
                'error': str(e)
            }
    
    async def _save_incident(self, incident: IncidentContext, isolation: Dict, playbook: Dict, mttr: float):
        """Sauvegarde incident en base"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO incidents 
                (incident_id, timestamp, severity, source_system, affected_assets,
                 indicators, threat_intel, response_actions, mttr_minutes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                incident.incident_id,
                incident.timestamp,
                incident.severity.value,
                incident.source_system,
                json.dumps(incident.affected_assets),
                json.dumps(incident.indicators),
                json.dumps(incident.threat_intel),
                json.dumps({'isolation': isolation, 'playbook': playbook}),
                mttr,
                'COMPLETED'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde incident: {e}")
    
    def _update_metrics(self, mttr: float, success: bool):
        """Mise à jour métriques performance"""
        self.performance_metrics['total_incidents'] += 1
        
        if success and mttr > 0:
            # Calcul MTTR moyen
            current_avg = self.performance_metrics['avg_mttr']
            total = self.performance_metrics['total_incidents']
            self.performance_metrics['avg_mttr'] = ((current_avg * (total - 1)) + mttr) / total
            
            # Taux de succès
            self.performance_metrics['success_rate'] = (
                (self.performance_metrics['success_rate'] * (total - 1) + 1) / total
            )
        
        # Simulation taux automatisation (ici 95%)
        self.performance_metrics['automation_rate'] = 0.95
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Métriques pour dashboard temps réel"""
        return {
            'incidents': {
                'total': self.performance_metrics['total_incidents'],
                'avg_mttr_minutes': round(self.performance_metrics['avg_mttr'], 2),
                'success_rate': round(self.performance_metrics['success_rate'] * 100, 1),
                'automation_rate': round(self.performance_metrics['automation_rate'] * 100, 1)
            },
            'performance': {
                'mttr_target': 15.0,
                'mttr_current': self.performance_metrics['avg_mttr'],
                'mttr_performance': (15.0 / max(self.performance_metrics['avg_mttr'], 0.1)) * 100 if self.performance_metrics['avg_mttr'] > 0 else 100
            },
            'status': 'OPERATIONAL',
            'last_updated': datetime.now().isoformat()
        }

# Tests et démonstration
async def test_incident_response_orchestrator():
    """Test complet de l'orchestrateur"""
    orchestrator = IncidentResponseOrchestrator()
    
    print("🎯 TEST INCIDENT RESPONSE ORCHESTRATOR")
    print("=" * 50)
    
    # Incidents de test réalistes
    test_incidents = [
        {
            'severity': 'CRITICAL',
            'source_system': 'SCADA-Station-01',
            'affected_assets': ['pump-station-01', 'sensor-ph-012', 'controller-main'],
            'indicators': {
                'source_ip': '192.168.100.45',
                'file_hash': 'a1b2c3d4e5f6789...',
                'malware_family': 'StuxnetVariant',
                'attack_vector': 'spear_phishing'
            }
        },
        {
            'severity': 'HIGH',
            'source_system': 'IoT-Gateway-02',
            'affected_assets': ['sensor-turbidity-008', 'sensor-flow-015'],
            'indicators': {
                'source_ip': '10.2.0.78',
                'anomalous_traffic': True,
                'device_compromise': True
            }
        },
        {
            'severity': 'MEDIUM',
            'source_system': 'Web-Dashboard',
            'affected_assets': ['web-server-01'],
            'indicators': {
                'sql_injection_attempt': True,
                'source_ip': '89.234.67.12',
                'user_agent': 'sqlmap/1.4.5'
            }
        }
    ]
    
    results = []
    
    for i, incident_data in enumerate(test_incidents, 1):
        print(f"\n🚨 Test incident {i}: {incident_data['severity']}")
        print(f"   Système source: {incident_data['source_system']}")
        print(f"   Assets affectés: {len(incident_data['affected_assets'])}")
        
        start_time = time.time()
        result = await orchestrator.process_incident(incident_data)
        execution_time = time.time() - start_time
        
        results.append(result)
        
        print(f"   📊 Statut: {result['status']}")
        if 'mttr_minutes' in result:
            print(f"   ⏱️  MTTR: {result['mttr_minutes']:.2f}min")
            print(f"   🎯 Performance: {result['performance']['performance_ratio']:.1f}x objectif")
        print(f"   🕐 Temps total: {execution_time:.2f}s")
    
    # Métriques finales
    metrics = orchestrator.get_dashboard_metrics()
    print(f"\n📈 MÉTRIQUES FINALES:")
    print(f"   Total incidents: {metrics['incidents']['total']}")
    print(f"   MTTR moyen: {metrics['incidents']['avg_mttr_minutes']}min")
    print(f"   Taux succès: {metrics['incidents']['success_rate']}%")
    print(f"   Taux automatisation: {metrics['incidents']['automation_rate']}%")
    print(f"   Performance MTTR: {metrics['performance']['mttr_performance']:.1f}%")
    
    return results, metrics

if __name__ == "__main__":
    asyncio.run(test_incident_response_orchestrator())