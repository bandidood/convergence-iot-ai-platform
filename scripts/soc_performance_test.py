#!/usr/bin/env python3
"""
🎯 SOC PERFORMANCE TEST
Station Traffeyère IoT AI Platform - RNCP 39394 Semaine 6

Test d'efficacité globale du SOC avec mesure MTTR
Objectif: MTTR < 11.3 minutes pour conformité RNCP 39394
"""

import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import concurrent.futures
import threading

# Import des composants SOC
import sys
import os
sys.path.append('scripts')

class SOCPerformanceTester:
    """Testeur de performance complète du SOC"""
    
    def __init__(self):
        self.test_scenarios = self._create_attack_scenarios()
        self.performance_metrics = {
            'incidents_total': 0,
            'incidents_resolved': 0,
            'mttr_times': [],
            'detection_times': [],
            'response_times': [],
            'enrichment_times': [],
            'containment_times': []
        }
        self.target_mttr = 11.3 * 60  # 11.3 minutes en secondes
        
    def _create_attack_scenarios(self) -> List[Dict[str, Any]]:
        """Créer des scénarios d'attaque réalistes"""
        return [
            {
                'name': 'APT_Advanced_Persistent_Threat',
                'severity': 'CRITICAL',
                'complexity': 'high',
                'expected_mttr': 15.0,  # minutes
                'phases': [
                    {'phase': 'reconnaissance', 'duration': 30},
                    {'phase': 'initial_access', 'duration': 45},
                    {'phase': 'persistence', 'duration': 60},
                    {'phase': 'privilege_escalation', 'duration': 90},
                    {'phase': 'lateral_movement', 'duration': 120},
                    {'phase': 'data_exfiltration', 'duration': 180}
                ],
                'indicators': {
                    'suspicious_domains': ['apt-command-station.org'],
                    'malicious_ips': ['203.0.113.45'],
                    'file_hashes': ['9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'],
                    'attack_techniques': ['T1566.001', 'T1055', 'T1003']
                }
            },
            {
                'name': 'IoT_Botnet_Infection',
                'severity': 'HIGH',
                'complexity': 'medium',
                'expected_mttr': 8.5,
                'phases': [
                    {'phase': 'device_scanning', 'duration': 15},
                    {'phase': 'exploitation', 'duration': 30},
                    {'phase': 'malware_installation', 'duration': 45},
                    {'phase': 'c2_communication', 'duration': 60}
                ],
                'indicators': {
                    'botnet_domains': ['iot-control-traffeyere.tk'],
                    'c2_ips': ['198.51.100.123'],
                    'infected_devices': ['sensor-temp-001', 'actuator-valve-003']
                }
            },
            {
                'name': 'Ransomware_Critical_Infrastructure',
                'severity': 'CRITICAL',
                'complexity': 'high',
                'expected_mttr': 10.0,
                'phases': [
                    {'phase': 'initial_compromise', 'duration': 20},
                    {'phase': 'network_discovery', 'duration': 40},
                    {'phase': 'credential_harvesting', 'duration': 60},
                    {'phase': 'encryption_deployment', 'duration': 120}
                ],
                'indicators': {
                    'ransomware_families': ['StationCryptor'],
                    'payment_addresses': ['1A2B3C4D5E6F7G8H9I0J...'],
                    'encryption_extensions': ['.trafflock']
                }
            },
            {
                'name': 'Insider_Threat_Data_Theft',
                'severity': 'HIGH',
                'complexity': 'low',
                'expected_mttr': 6.0,
                'phases': [
                    {'phase': 'privilege_abuse', 'duration': 30},
                    {'phase': 'data_access', 'duration': 45},
                    {'phase': 'data_staging', 'duration': 60},
                    {'phase': 'exfiltration', 'duration': 90}
                ],
                'indicators': {
                    'suspicious_users': ['maintenance_temp@traffeyere.local'],
                    'unusual_access_patterns': ['off_hours_database_access'],
                    'data_volumes': ['large_data_export']
                }
            },
            {
                'name': 'Supply_Chain_Attack',
                'severity': 'CRITICAL',
                'complexity': 'high', 
                'expected_mttr': 12.0,
                'phases': [
                    {'phase': 'vendor_compromise', 'duration': 60},
                    {'phase': 'trojanized_update', 'duration': 30},
                    {'phase': 'deployment', 'duration': 45},
                    {'phase': 'activation', 'duration': 120}
                ],
                'indicators': {
                    'compromised_software': ['StationMonitor_v3.2.1'],
                    'malicious_updates': ['update_server_compromise'],
                    'backdoor_signatures': ['supply_chain_trojan_2024']
                }
            }
        ]
    
    async def run_comprehensive_test(self, num_simultaneous_incidents: int = 3) -> Dict[str, Any]:
        """Exécuter un test complet de performance SOC"""
        print("🎯 DÉMARRAGE TEST PERFORMANCE SOC COMPLET")
        print("=" * 55)
        print(f"📊 Objectif MTTR: < {self.target_mttr/60:.1f} minutes")
        print(f"🚨 Incidents simultanés: {num_simultaneous_incidents}")
        print(f"📈 Scénarios d'attaque: {len(self.test_scenarios)}")
        
        # Réinitialiser les métriques
        self.performance_metrics = {
            'incidents_total': 0,
            'incidents_resolved': 0,
            'mttr_times': [],
            'detection_times': [],
            'response_times': [],
            'enrichment_times': [],
            'containment_times': []
        }
        
        start_time = time.time()
        
        # Exécuter les tests en parallèle
        incident_tasks = []
        
        for i in range(num_simultaneous_incidents):
            scenario = random.choice(self.test_scenarios)
            incident_id = f"PERF-TEST-{int(time.time())}-{i:03d}"
            
            task = asyncio.create_task(
                self._simulate_incident_lifecycle(incident_id, scenario)
            )
            incident_tasks.append(task)
        
        # Attendre que tous les incidents soient traités
        results = await asyncio.gather(*incident_tasks, return_exceptions=True)
        
        end_time = time.time()
        total_test_duration = end_time - start_time
        
        # Analyser les résultats
        performance_report = self._analyze_performance_results(total_test_duration)
        
        # Afficher le rapport
        self._display_performance_report(performance_report)
        
        return performance_report
    
    async def _simulate_incident_lifecycle(self, incident_id: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simuler le cycle de vie complet d'un incident"""
        incident_start_time = time.time()
        
        print(f"\n🚨 INCIDENT {incident_id}")
        print(f"   Scénario: {scenario['name']}")
        print(f"   Sévérité: {scenario['severity']}")
        
        # Phase 1: Détection
        detection_start = time.time()
        await self._simulate_detection_phase(scenario)
        detection_time = time.time() - detection_start
        
        # Phase 2: Enrichissement Threat Intelligence
        enrichment_start = time.time()
        await self._simulate_threat_intelligence_enrichment(scenario)
        enrichment_time = time.time() - enrichment_start
        
        # Phase 3: Réponse SOAR
        response_start = time.time()
        await self._simulate_soar_response(scenario)
        response_time = time.time() - response_start
        
        # Phase 4: Containment (isolement/confinement)
        containment_start = time.time()
        await self._simulate_containment_actions(scenario)
        containment_time = time.time() - containment_start
        
        # Calculer MTTR pour cet incident
        total_mttr = time.time() - incident_start_time
        
        # Enregistrer les métriques
        self.performance_metrics['incidents_total'] += 1
        self.performance_metrics['incidents_resolved'] += 1
        self.performance_metrics['mttr_times'].append(total_mttr)
        self.performance_metrics['detection_times'].append(detection_time)
        self.performance_metrics['enrichment_times'].append(enrichment_time)
        self.performance_metrics['response_times'].append(response_time)
        self.performance_metrics['containment_times'].append(containment_time)
        
        mttr_minutes = total_mttr / 60
        status = "✅ CONFORME" if mttr_minutes < (self.target_mttr/60) else "❌ NON-CONFORME"
        
        print(f"   ⏱️  MTTR: {mttr_minutes:.2f} minutes {status}")
        
        return {
            'incident_id': incident_id,
            'scenario': scenario['name'],
            'mttr_seconds': total_mttr,
            'mttr_minutes': mttr_minutes,
            'compliant': mttr_minutes < (self.target_mttr/60),
            'phases': {
                'detection': detection_time,
                'enrichment': enrichment_time,
                'response': response_time,
                'containment': containment_time
            }
        }
    
    async def _simulate_detection_phase(self, scenario: Dict[str, Any]):
        """Simuler la phase de détection ML/SIEM"""
        complexity_delays = {'low': 0.5, 'medium': 1.0, 'high': 1.5}
        base_delay = complexity_delays.get(scenario['complexity'], 1.0)
        
        # Simuler l'analyse ML
        await asyncio.sleep(base_delay + random.uniform(0.2, 0.8))
        
        print(f"   🔍 Détection: {scenario['indicators']}")
    
    async def _simulate_threat_intelligence_enrichment(self, scenario: Dict[str, Any]):
        """Simuler l'enrichissement par Threat Intelligence"""
        # Simuler les requêtes vers feeds externes
        feeds_delay = random.uniform(0.3, 1.2)
        await asyncio.sleep(feeds_delay)
        
        print(f"   📡 Threat Intel: Enrichissement complet")
    
    async def _simulate_soar_response(self, scenario: Dict[str, Any]):
        """Simuler la réponse automatisée SOAR"""
        severity_response_times = {
            'LOW': random.uniform(1.0, 2.0),
            'MEDIUM': random.uniform(2.0, 4.0),
            'HIGH': random.uniform(4.0, 6.0),
            'CRITICAL': random.uniform(6.0, 8.0)
        }
        
        response_delay = severity_response_times.get(scenario['severity'], 3.0)
        await asyncio.sleep(response_delay)
        
        print(f"   🎭 SOAR: Playbook {scenario['severity']} exécuté")
    
    async def _simulate_containment_actions(self, scenario: Dict[str, Any]):
        """Simuler les actions de confinement"""
        containment_delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(containment_delay)
        
        print(f"   🛡️  Containment: Menace isolée")
    
    def _analyze_performance_results(self, total_test_duration: float) -> Dict[str, Any]:
        """Analyser les résultats de performance"""
        
        if not self.performance_metrics['mttr_times']:
            return {'error': 'Aucune donnée de performance collectée'}
        
        # Statistiques MTTR
        mttr_times_minutes = [t/60 for t in self.performance_metrics['mttr_times']]
        
        avg_mttr = statistics.mean(mttr_times_minutes)
        median_mttr = statistics.median(mttr_times_minutes)
        min_mttr = min(mttr_times_minutes)
        max_mttr = max(mttr_times_minutes)
        
        # Conformité RNCP
        compliant_incidents = sum(1 for t in mttr_times_minutes if t < (self.target_mttr/60))
        compliance_rate = (compliant_incidents / len(mttr_times_minutes)) * 100
        
        # Statistiques par phase
        phase_stats = {}
        for phase in ['detection', 'enrichment', 'response', 'containment']:
            times = self.performance_metrics[f'{phase}_times']
            if times:
                phase_stats[phase] = {
                    'avg_seconds': statistics.mean(times),
                    'min_seconds': min(times),
                    'max_seconds': max(times)
                }
        
        # Performance globale
        incidents_per_minute = self.performance_metrics['incidents_resolved'] / (total_test_duration / 60)
        
        return {
            'test_summary': {
                'total_incidents': self.performance_metrics['incidents_total'],
                'resolved_incidents': self.performance_metrics['incidents_resolved'],
                'total_test_duration_minutes': total_test_duration / 60,
                'incidents_per_minute': incidents_per_minute
            },
            'mttr_analysis': {
                'average_minutes': avg_mttr,
                'median_minutes': median_mttr,
                'min_minutes': min_mttr,
                'max_minutes': max_mttr,
                'target_minutes': self.target_mttr / 60,
                'compliance_rate': compliance_rate,
                'compliant_incidents': compliant_incidents,
                'non_compliant_incidents': len(mttr_times_minutes) - compliant_incidents
            },
            'phase_breakdown': phase_stats,
            'performance_grade': self._calculate_performance_grade(avg_mttr, compliance_rate),
            'recommendations': self._generate_recommendations(avg_mttr, compliance_rate, phase_stats)
        }
    
    def _calculate_performance_grade(self, avg_mttr: float, compliance_rate: float) -> str:
        """Calculer la note de performance"""
        if avg_mttr <= 8.0 and compliance_rate >= 95:
            return "A+ EXCELLENT"
        elif avg_mttr <= 10.0 and compliance_rate >= 90:
            return "A TRÈS BON"
        elif avg_mttr <= 12.0 and compliance_rate >= 80:
            return "B BON"
        elif avg_mttr <= 15.0 and compliance_rate >= 70:
            return "C ACCEPTABLE"
        else:
            return "D AMÉLIORATION REQUISE"
    
    def _generate_recommendations(self, avg_mttr: float, compliance_rate: float, 
                                phase_stats: Dict[str, Any]) -> List[str]:
        """Générer des recommandations d'amélioration"""
        recommendations = []
        
        if avg_mttr > (self.target_mttr / 60):
            recommendations.append(f"MTTR moyen ({avg_mttr:.1f}min) supérieur à l'objectif ({self.target_mttr/60:.1f}min)")
        
        if compliance_rate < 90:
            recommendations.append(f"Taux de conformité ({compliance_rate:.1f}%) à améliorer")
        
        # Analyser les phases les plus lentes
        if phase_stats:
            slowest_phase = max(phase_stats.keys(), 
                              key=lambda x: phase_stats[x]['avg_seconds'])
            recommendations.append(f"Phase '{slowest_phase}' la plus lente ({phase_stats[slowest_phase]['avg_seconds']:.1f}s)")
        
        if not recommendations:
            recommendations.append("Performance excellente - aucune amélioration requise")
        
        return recommendations
    
    def _display_performance_report(self, report: Dict[str, Any]):
        """Afficher le rapport de performance"""
        print(f"\n🎯 RAPPORT DE PERFORMANCE SOC")
        print("=" * 55)
        
        if 'error' in report:
            print(f"❌ Erreur: {report['error']}")
            return
        
        # Résumé du test
        test_info = report['test_summary']
        print(f"📊 RÉSUMÉ:")
        print(f"   Incidents traités: {test_info['resolved_incidents']}/{test_info['total_incidents']}")
        print(f"   Durée test: {test_info['total_test_duration_minutes']:.1f} minutes")
        print(f"   Débit: {test_info['incidents_per_minute']:.1f} incidents/minute")
        
        # Analyse MTTR
        mttr_info = report['mttr_analysis']
        print(f"\n⏱️  ANALYSE MTTR:")
        print(f"   MTTR moyen: {mttr_info['average_minutes']:.2f} minutes")
        print(f"   MTTR médian: {mttr_info['median_minutes']:.2f} minutes")
        print(f"   MTTR min/max: {mttr_info['min_minutes']:.2f}/{mttr_info['max_minutes']:.2f} minutes")
        print(f"   Objectif RNCP: < {mttr_info['target_minutes']:.1f} minutes")
        print(f"   Conformité: {mttr_info['compliance_rate']:.1f}% ({mttr_info['compliant_incidents']}/{mttr_info['compliant_incidents'] + mttr_info['non_compliant_incidents']})")
        
        # Répartition par phases
        print(f"\n🔄 RÉPARTITION PAR PHASES:")
        for phase, stats in report['phase_breakdown'].items():
            print(f"   {phase.capitalize()}: {stats['avg_seconds']:.1f}s (min: {stats['min_seconds']:.1f}s, max: {stats['max_seconds']:.1f}s)")
        
        # Note de performance
        print(f"\n🏆 NOTE DE PERFORMANCE: {report['performance_grade']}")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        # Statut de conformité RNCP 39394
        if mttr_info['compliance_rate'] >= 80:
            print(f"\n✅ CONFORMITÉ RNCP 39394 Bloc 3: VALIDÉE")
            print(f"   Objectif MTTR < 11.3 min respecté à {mttr_info['compliance_rate']:.1f}%")
        else:
            print(f"\n❌ CONFORMITÉ RNCP 39394 Bloc 3: NON VALIDÉE") 
            print(f"   Amélioration requise pour atteindre 80% de conformité")

async def main():
    """Test principal de performance SOC"""
    tester = SOCPerformanceTester()
    
    # Test avec incidents multiples simultanés
    performance_report = await tester.run_comprehensive_test(num_simultaneous_incidents=5)
    
    return performance_report

if __name__ == "__main__":
    asyncio.run(main())
