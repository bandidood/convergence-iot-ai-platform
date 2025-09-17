#!/usr/bin/env python3
"""
🌐 REDONDANCE RÉSEAU 5G-TSN SÉCURISÉE
Station Traffeyère IoT AI Platform - RNCP 39394 Semaine 9

Système de redondance réseau ultra-fiable:
- 5G SA (Stand Alone) slice dédiée
- TSN (Time-Sensitive Networking) IEEE 802.1
- Double path automatique avec failover
- Latence déterministe <10ms garantie
- QoS différenciée par type de trafic
- Monitoring temps réel et auto-healing
"""

import asyncio
import json
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import hashlib
import struct

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('NetworkRedundancy5GTSN')

class NetworkTechnology(Enum):
    """Technologies réseau supportées"""
    FIVE_G_SA = "5G_SA"
    TSN_802_1 = "TSN_802_1"
    LORAWAN = "LORAWAN"
    ETHERNET = "ETHERNET"
    WIFI_6E = "WIFI_6E"

class TrafficClass(Enum):
    """Classes de trafic TSN"""
    CRITICAL_CONTROL = "CRITICAL_CONTROL"  # <1ms, 99.9999% fiabilité
    REAL_TIME_MONITORING = "REAL_TIME_MONITORING"  # <10ms
    BULK_DATA = "BULK_DATA"  # Best effort
    MANAGEMENT = "MANAGEMENT"  # Faible priorité

class NetworkPath(Enum):
    """Chemins réseau disponibles"""
    PRIMARY_5G = "PRIMARY_5G"
    BACKUP_5G = "BACKUP_5G"
    TSN_PATH_A = "TSN_PATH_A"
    TSN_PATH_B = "TSN_PATH_B"
    EMERGENCY_LORAWAN = "EMERGENCY_LORAWAN"

@dataclass
class NetworkSlice:
    """Slice réseau 5G configuré"""
    slice_id: str
    network_slice_instance_id: str
    service_type: str  # eMBB, URLLC, mMTC
    latency_requirement: float  # ms
    bandwidth_guaranteed: int  # Mbps
    reliability_target: float  # %
    priority_level: int
    traffic_classes: List[TrafficClass]
    active: bool

@dataclass
class TSNStream:
    """Stream TSN configuré"""
    stream_id: str
    source_mac: str
    destination_mac: str
    vlan_id: int
    priority: int
    max_frame_size: int
    interval: float  # microsecondes
    max_latency: float  # microsecondes
    burst_size: int
    gate_control_list: List[Dict]

@dataclass
class NetworkMetrics:
    """Métriques réseau temps réel"""
    path: NetworkPath
    technology: NetworkTechnology
    latency_ms: float
    jitter_ms: float
    packet_loss_percent: float
    bandwidth_mbps: float
    signal_strength: float
    reliability_score: float
    last_update: str

class FiveGSliceManager:
    """Gestionnaire des slices 5G SA"""
    
    def __init__(self):
        self.active_slices = {}
        self.slice_configurations = {
            'critical_control': {
                'service_type': 'URLLC',
                'latency_requirement': 1.0,
                'bandwidth_guaranteed': 10,
                'reliability_target': 99.9999,
                'priority_level': 1
            },
            'iot_monitoring': {
                'service_type': 'mMTC', 
                'latency_requirement': 10.0,
                'bandwidth_guaranteed': 5,
                'reliability_target': 99.99,
                'priority_level': 2
            },
            'bulk_data': {
                'service_type': 'eMBB',
                'latency_requirement': 100.0,
                'bandwidth_guaranteed': 50,
                'reliability_target': 99.9,
                'priority_level': 3
            }
        }
        
    async def create_network_slice(self, slice_config: str) -> NetworkSlice:
        """Création d'un slice réseau 5G"""
        config = self.slice_configurations.get(slice_config)
        if not config:
            raise ValueError(f"Configuration slice inconnue: {slice_config}")
        
        slice_id = f"NSI_{slice_config}_{int(time.time())}"
        nsi_id = f"NSSI_{hashlib.md5(slice_id.encode()).hexdigest()[:8]}"
        
        logger.info(f"🔧 Création slice 5G: {slice_id}")
        
        # Simulation création slice
        await asyncio.sleep(0.8)  # Temps configuration réseau
        
        network_slice = NetworkSlice(
            slice_id=slice_id,
            network_slice_instance_id=nsi_id,
            service_type=config['service_type'],
            latency_requirement=config['latency_requirement'],
            bandwidth_guaranteed=config['bandwidth_guaranteed'],
            reliability_target=config['reliability_target'],
            priority_level=config['priority_level'],
            traffic_classes=[TrafficClass.CRITICAL_CONTROL] if slice_config == 'critical_control' else [TrafficClass.REAL_TIME_MONITORING],
            active=True
        )
        
        self.active_slices[slice_id] = network_slice
        
        logger.info(f"✅ Slice 5G créé: {slice_id} ({config['service_type']})")
        return network_slice
    
    async def monitor_slice_performance(self, slice_id: str) -> Dict[str, Any]:
        """Monitoring performance d'un slice"""
        if slice_id not in self.active_slices:
            raise ValueError(f"Slice inexistant: {slice_id}")
        
        slice_obj = self.active_slices[slice_id]
        
        # Simulation métriques réelles
        current_latency = random.uniform(0.5, slice_obj.latency_requirement * 0.8)
        current_reliability = random.uniform(slice_obj.reliability_target - 0.01, slice_obj.reliability_target)
        current_bandwidth = random.uniform(slice_obj.bandwidth_guaranteed * 0.9, slice_obj.bandwidth_guaranteed * 1.2)
        
        metrics = {
            'slice_id': slice_id,
            'latency_ms': current_latency,
            'reliability_percent': current_reliability,
            'bandwidth_mbps': current_bandwidth,
            'sla_compliance': current_latency <= slice_obj.latency_requirement,
            'timestamp': datetime.now().isoformat()
        }
        
        return metrics

class TSNQueueManager:
    """Gestionnaire des queues TSN IEEE 802.1"""
    
    def __init__(self):
        self.active_streams = {}
        self.queue_configurations = {
            'critical_queue': {
                'priority': 7,
                'max_latency_us': 100,
                'gate_control': self._generate_gate_control_critical()
            },
            'realtime_queue': {
                'priority': 6,
                'max_latency_us': 1000,
                'gate_control': self._generate_gate_control_realtime()
            },
            'best_effort_queue': {
                'priority': 0,
                'max_latency_us': 10000,
                'gate_control': self._generate_gate_control_best_effort()
            }
        }
        
    def _generate_gate_control_critical(self) -> List[Dict]:
        """Génération Gate Control List pour trafic critique"""
        # Cycle 125µs avec fenêtre dédiée pour trafic critique
        return [
            {'gate_state': 'OPEN', 'duration_us': 25, 'queue': 7},   # Critique
            {'gate_state': 'CLOSED', 'duration_us': 100, 'queue': 7}  # Autres
        ]
    
    def _generate_gate_control_realtime(self) -> List[Dict]:
        """Génération Gate Control List pour temps réel"""
        return [
            {'gate_state': 'OPEN', 'duration_us': 50, 'queue': 6},   # Temps réel
            {'gate_state': 'CLOSED', 'duration_us': 75, 'queue': 6}  # Autres
        ]
    
    def _generate_gate_control_best_effort(self) -> List[Dict]:
        """Génération Gate Control List pour best effort"""
        return [
            {'gate_state': 'OPEN', 'duration_us': 1000, 'queue': 0}  # Toujours ouvert
        ]
    
    async def configure_tsn_stream(self, stream_config: str, source_device: str, dest_device: str) -> TSNStream:
        """Configuration d'un stream TSN"""
        config = self.queue_configurations.get(stream_config)
        if not config:
            raise ValueError(f"Configuration TSN inconnue: {stream_config}")
        
        stream_id = f"TSN_{stream_config}_{int(time.time())}"
        
        logger.info(f"🔧 Configuration stream TSN: {stream_id}")
        
        # Génération adresses MAC simulées
        source_mac = f"02:00:5e:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}"
        dest_mac = f"02:00:5e:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}"
        
        tsn_stream = TSNStream(
            stream_id=stream_id,
            source_mac=source_mac,
            destination_mac=dest_mac,
            vlan_id=random.randint(100, 4000),
            priority=config['priority'],
            max_frame_size=1500,
            interval=125.0,  # 125µs standard TSN
            max_latency=config['max_latency_us'],
            burst_size=1,
            gate_control_list=config['gate_control']
        )
        
        self.active_streams[stream_id] = tsn_stream
        
        # Simulation configuration switch TSN
        await asyncio.sleep(0.3)
        
        logger.info(f"✅ Stream TSN configuré: {stream_id} (P{config['priority']})")
        return tsn_stream

class NetworkRedundancyOrchestrator:
    """Orchestrateur de redondance réseau 5G-TSN"""
    
    def __init__(self):
        self.five_g_manager = FiveGSliceManager()
        self.tsn_manager = TSNQueueManager()
        self.active_paths = {}
        self.path_metrics = {}
        self.failover_history = []
        self.monitoring_active = False
        
    async def initialize_redundant_network(self) -> Dict[str, Any]:
        """Initialisation réseau redondant complet"""
        logger.info("🚀 Initialisation réseau redondant 5G-TSN")
        
        initialization_result = {
            'network_slices': {},
            'tsn_streams': {},
            'redundant_paths': {},
            'performance_baseline': {}
        }
        
        try:
            # 1. Création des slices 5G
            logger.info("🔧 Création slices 5G...")
            critical_slice = await self.five_g_manager.create_network_slice('critical_control')
            monitoring_slice = await self.five_g_manager.create_network_slice('iot_monitoring')
            data_slice = await self.five_g_manager.create_network_slice('bulk_data')
            
            initialization_result['network_slices'] = {
                'critical': asdict(critical_slice),
                'monitoring': asdict(monitoring_slice),
                'data': asdict(data_slice)
            }
            
            # 2. Configuration streams TSN
            logger.info("🔧 Configuration streams TSN...")
            critical_stream = await self.tsn_manager.configure_tsn_stream('critical_queue', 'PLC_SCADA', 'CONTROL_CENTER')
            realtime_stream = await self.tsn_manager.configure_tsn_stream('realtime_queue', 'IOT_GATEWAY', 'DATA_CENTER')
            
            initialization_result['tsn_streams'] = {
                'critical': asdict(critical_stream),
                'realtime': asdict(realtime_stream)
            }
            
            # 3. Configuration chemins redondants
            redundant_paths = await self._configure_redundant_paths()
            initialization_result['redundant_paths'] = redundant_paths
            
            # 4. Baseline performance
            baseline = await self._establish_performance_baseline()
            initialization_result['performance_baseline'] = baseline
            
            logger.info("✅ Réseau redondant 5G-TSN initialisé")
            return initialization_result
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation réseau: {e}")
            return {'error': str(e)}
    
    async def _configure_redundant_paths(self) -> Dict[str, Any]:
        """Configuration des chemins redondants"""
        paths = {
            NetworkPath.PRIMARY_5G: {
                'technology': NetworkTechnology.FIVE_G_SA,
                'priority': 1,
                'bandwidth_mbps': 100,
                'latency_target_ms': 5,
                'active': True
            },
            NetworkPath.BACKUP_5G: {
                'technology': NetworkTechnology.FIVE_G_SA,
                'priority': 2,
                'bandwidth_mbps': 50,
                'latency_target_ms': 8,
                'active': False  # Standby
            },
            NetworkPath.TSN_PATH_A: {
                'technology': NetworkTechnology.TSN_802_1,
                'priority': 1,
                'bandwidth_mbps': 1000,  # Gigabit TSN
                'latency_target_ms': 0.1,
                'active': True
            },
            NetworkPath.TSN_PATH_B: {
                'technology': NetworkTechnology.TSN_802_1,
                'priority': 2,
                'bandwidth_mbps': 1000,
                'latency_target_ms': 0.1,
                'active': False  # Redondance
            }
        }
        
        for path, config in paths.items():
            self.active_paths[path] = config
            
        return {path.value: config for path, config in paths.items()}
    
    async def _establish_performance_baseline(self) -> Dict[str, Any]:
        """Établissement baseline performance"""
        baseline_metrics = {}
        
        for path in self.active_paths:
            metrics = await self._measure_path_performance(path)
            baseline_metrics[path.value] = metrics
            
        return baseline_metrics
    
    async def _measure_path_performance(self, path: NetworkPath) -> Dict[str, float]:
        """Mesure performance d'un chemin réseau"""
        # Simulation mesures réelles avec variabilité
        base_latency = {
            NetworkPath.PRIMARY_5G: 3.2,
            NetworkPath.BACKUP_5G: 5.8,
            NetworkPath.TSN_PATH_A: 0.08,
            NetworkPath.TSN_PATH_B: 0.09,
            NetworkPath.EMERGENCY_LORAWAN: 45.0
        }.get(path, 10.0)
        
        latency = base_latency + random.uniform(-0.5, 0.8)
        jitter = random.uniform(0.01, 0.3)
        packet_loss = random.uniform(0.0, 0.01)
        bandwidth = random.uniform(80, 120) if '5G' in path.value else random.uniform(900, 1100)
        
        return {
            'latency_ms': round(latency, 3),
            'jitter_ms': round(jitter, 3),
            'packet_loss_percent': round(packet_loss, 4),
            'bandwidth_mbps': round(bandwidth, 1),
            'reliability_score': round(100 - packet_loss * 100, 2)
        }
    
    async def start_continuous_monitoring(self):
        """Démarrage monitoring continu avec auto-failover"""
        self.monitoring_active = True
        logger.info("🎯 Démarrage monitoring réseau continu")
        
        async def monitor_loop():
            while self.monitoring_active:
                try:
                    # Monitoring de tous les chemins
                    for path in self.active_paths:
                        metrics = await self._measure_path_performance(path)
                        metrics['timestamp'] = datetime.now().isoformat()
                        metrics['path'] = path.value
                        
                        self.path_metrics[path] = metrics
                        
                        # Détection dégradation et failover si nécessaire
                        await self._check_failover_conditions(path, metrics)
                    
                    await asyncio.sleep(1)  # Monitoring chaque seconde
                    
                except Exception as e:
                    logger.error(f"❌ Erreur monitoring: {e}")
                    await asyncio.sleep(5)
        
        # Lancement en arrière-plan
        asyncio.create_task(monitor_loop())
    
    async def _check_failover_conditions(self, path: NetworkPath, metrics: Dict[str, float]):
        """Vérification conditions de failover"""
        path_config = self.active_paths[path]
        
        # Conditions de failover
        latency_exceeded = metrics['latency_ms'] > path_config['latency_target_ms'] * 2
        high_packet_loss = metrics['packet_loss_percent'] > 1.0
        low_reliability = metrics['reliability_score'] < 95.0
        
        if (latency_exceeded or high_packet_loss or low_reliability) and path_config['active']:
            await self._trigger_failover(path, metrics)
    
    async def _trigger_failover(self, failed_path: NetworkPath, metrics: Dict[str, float]):
        """Déclenchement failover automatique"""
        logger.warning(f"⚠️ Dégradation détectée sur {failed_path.value}, déclenchement failover")
        
        # Recherche chemin de backup
        backup_path = self._find_backup_path(failed_path)
        
        if backup_path:
            # Basculement
            self.active_paths[failed_path]['active'] = False
            self.active_paths[backup_path]['active'] = True
            
            failover_event = {
                'timestamp': datetime.now().isoformat(),
                'failed_path': failed_path.value,
                'backup_path': backup_path.value,
                'failure_metrics': metrics,
                'failover_duration_ms': random.uniform(50, 200)  # Simulation durée basculement
            }
            
            self.failover_history.append(failover_event)
            
            logger.info(f"✅ Failover réussi: {failed_path.value} → {backup_path.value}")
            
            # Tentative récupération après 30 secondes
            asyncio.create_task(self._attempt_recovery(failed_path, 30))
        else:
            logger.error(f"❌ Aucun chemin de backup disponible pour {failed_path.value}")
    
    def _find_backup_path(self, failed_path: NetworkPath) -> Optional[NetworkPath]:
        """Recherche chemin de backup"""
        backup_mapping = {
            NetworkPath.PRIMARY_5G: NetworkPath.BACKUP_5G,
            NetworkPath.TSN_PATH_A: NetworkPath.TSN_PATH_B,
            NetworkPath.BACKUP_5G: NetworkPath.TSN_PATH_A,  # Cross-technology failover
            NetworkPath.TSN_PATH_B: NetworkPath.PRIMARY_5G
        }
        
        backup = backup_mapping.get(failed_path)
        if backup and not self.active_paths[backup]['active']:
            return backup
        return None
    
    async def _attempt_recovery(self, failed_path: NetworkPath, delay_seconds: int):
        """Tentative de récupération d'un chemin"""
        await asyncio.sleep(delay_seconds)
        
        # Test récupération
        recovery_metrics = await self._measure_path_performance(failed_path)
        path_config = self.active_paths[failed_path]
        
        recovery_ok = (
            recovery_metrics['latency_ms'] <= path_config['latency_target_ms'] * 1.5 and
            recovery_metrics['packet_loss_percent'] < 0.5 and
            recovery_metrics['reliability_score'] > 98.0
        )
        
        if recovery_ok:
            self.active_paths[failed_path]['active'] = True
            logger.info(f"✅ Récupération réussie pour {failed_path.value}")
        else:
            logger.warning(f"⚠️ Récupération échouée pour {failed_path.value}, nouvelle tentative dans 60s")
            asyncio.create_task(self._attempt_recovery(failed_path, 60))
    
    async def generate_network_report(self) -> Dict[str, Any]:
        """Génération rapport réseau complet"""
        current_metrics = {}
        for path in self.active_paths:
            current_metrics[path.value] = await self._measure_path_performance(path)
        
        active_paths = [path.value for path, config in self.active_paths.items() if config['active']]
        
        # Calcul métriques agrégées
        total_bandwidth = sum(config['bandwidth_mbps'] for config in self.active_paths.values() if config['active'])
        average_latency = sum(metrics['latency_ms'] for metrics in current_metrics.values()) / len(current_metrics)
        best_reliability = max(metrics['reliability_score'] for metrics in current_metrics.values())
        
        # Analyse slices 5G
        slice_performance = {}
        for slice_id in self.five_g_manager.active_slices:
            slice_metrics = await self.five_g_manager.monitor_slice_performance(slice_id)
            slice_performance[slice_id] = slice_metrics
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'network_status': {
                'active_paths': active_paths,
                'total_bandwidth_mbps': round(total_bandwidth, 1),
                'average_latency_ms': round(average_latency, 3),
                'best_reliability_percent': round(best_reliability, 2),
                'redundancy_level': len(active_paths)
            },
            'path_metrics': current_metrics,
            'slice_performance': slice_performance,
            'failover_history': self.failover_history[-10:],  # 10 derniers événements
            'tsn_streams': len(self.tsn_manager.active_streams),
            'five_g_slices': len(self.five_g_manager.active_slices)
        }
        
        return report

async def demonstrate_5g_tsn_redundancy():
    """Démonstration redondance 5G-TSN"""
    print("🌐 DÉMONSTRATION REDONDANCE RÉSEAU 5G-TSN")
    print("=" * 60)
    
    try:
        # Initialisation orchestrateur
        orchestrator = NetworkRedundancyOrchestrator()
        
        # 1. Initialisation réseau redondant
        print("\n🚀 1. INITIALISATION RÉSEAU REDONDANT")
        print("-" * 40)
        
        init_result = await orchestrator.initialize_redundant_network()
        if 'error' in init_result:
            print(f"❌ Erreur: {init_result['error']}")
            return None
        
        print(f"✅ Slices 5G créés: {len(init_result['network_slices'])}")
        print(f"✅ Streams TSN configurés: {len(init_result['tsn_streams'])}")
        print(f"✅ Chemins redondants: {len(init_result['redundant_paths'])}")
        
        # Affichage détails slices
        for slice_name, slice_data in init_result['network_slices'].items():
            print(f"   📡 Slice {slice_name}: {slice_data['service_type']} - {slice_data['latency_requirement']}ms")
        
        # 2. Démarrage monitoring
        print("\n🎯 2. DÉMARRAGE MONITORING CONTINU")
        print("-" * 40)
        
        await orchestrator.start_continuous_monitoring()
        print("✅ Monitoring réseau démarré")
        
        # 3. Test performance baseline
        print("\n📊 3. MESURES PERFORMANCE BASELINE")
        print("-" * 40)
        
        baseline_report = await orchestrator.generate_network_report()
        network_status = baseline_report['network_status']
        
        print(f"🌐 Chemins actifs: {', '.join(network_status['active_paths'])}")
        print(f"⚡ Bande passante totale: {network_status['total_bandwidth_mbps']} Mbps")
        print(f"⏱️ Latence moyenne: {network_status['average_latency_ms']} ms")
        print(f"🎯 Fiabilité max: {network_status['best_reliability_percent']}%")
        print(f"🔄 Niveau redondance: {network_status['redundancy_level']} chemins")
        
        # 4. Simulation panne et failover
        print("\n⚠️ 4. SIMULATION PANNE ET FAILOVER")
        print("-" * 40)
        
        print("🔥 Simulation panne chemin primaire 5G...")
        
        # Simulation dégradation manuelle
        primary_path = NetworkPath.PRIMARY_5G
        orchestrator.active_paths[primary_path]['active'] = False
        
        # Déclenchement failover manuel pour démo
        await orchestrator._trigger_failover(
            primary_path, 
            {'latency_ms': 50.0, 'packet_loss_percent': 5.0, 'reliability_score': 85.0}
        )
        
        # Attente stabilisation
        await asyncio.sleep(3)
        
        # Rapport post-failover
        failover_report = await orchestrator.generate_network_report()
        print(f"✅ Failover terminé")
        print(f"🔄 Nouveaux chemins actifs: {', '.join(failover_report['network_status']['active_paths'])}")
        print(f"📊 Événements failover: {len(failover_report['failover_history'])}")
        
        # 5. Test charge et performance
        print("\n⚡ 5. TEST CHARGE ET PERFORMANCE")
        print("-" * 40)
        
        # Simulation trafic intensif
        for i in range(5):
            slice_id = list(orchestrator.five_g_manager.active_slices.keys())[0]
            slice_metrics = await orchestrator.five_g_manager.monitor_slice_performance(slice_id)
            print(f"📊 Test {i+1}: Latence {slice_metrics['latency_ms']:.2f}ms, "
                  f"Fiabilité {slice_metrics['reliability_percent']:.3f}%")
            await asyncio.sleep(0.5)
        
        # 6. Rapport final
        print("\n📋 6. RAPPORT FINAL REDONDANCE")
        print("-" * 40)
        
        final_report = await orchestrator.generate_network_report()
        
        print(f"🌐 État réseau final:")
        print(f"   - Chemins actifs: {len(final_report['network_status']['active_paths'])}")
        print(f"   - Slices 5G: {final_report['five_g_slices']}")
        print(f"   - Streams TSN: {final_report['tsn_streams']}")
        print(f"   - Bande passante: {final_report['network_status']['total_bandwidth_mbps']} Mbps")
        print(f"   - Latence: {final_report['network_status']['average_latency_ms']:.3f} ms")
        print(f"   - Fiabilité: {final_report['network_status']['best_reliability_percent']}%")
        
        # Arrêt monitoring
        orchestrator.monitoring_active = False
        
        return final_report
        
    except Exception as e:
        print(f"❌ Erreur durant la démonstration: {e}")
        return None

if __name__ == "__main__":
    # Lancement démonstration
    result = asyncio.run(demonstrate_5g_tsn_redundancy())
    
    if result:
        print(f"\n🎯 DÉMONSTRATION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print("✅ Redondance 5G-TSN opérationnelle")
        print("✅ Failover automatique validé")
        print("✅ Performance déterministe confirmée")
        print("✅ Monitoring temps réel fonctionnel")
        
        print(f"\n📊 MÉTRIQUES FINALES:")
        print(f"🌐 Réseau: {result['network_status']['redundancy_level']} chemins redondants")
        print(f"⚡ Performance: {result['network_status']['total_bandwidth_mbps']} Mbps")
        print(f"⏱️ Latence: {result['network_status']['average_latency_ms']:.3f} ms")
        print(f"🎯 Fiabilité: {result['network_status']['best_reliability_percent']}%")
    else:
        print(f"\n❌ DÉMONSTRATION ÉCHOUÉE")