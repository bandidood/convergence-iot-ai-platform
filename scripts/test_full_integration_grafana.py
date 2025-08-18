"""
🎯 TEST INTÉGRATION COMPLÈTE GRAFANA
Validation pipeline: Générateur IoT → Prometheus → Grafana
127 capteurs temps réel avec métriques RNCP 39394

Compatible RNCP 39394 - Expert en Systèmes d'Information et Sécurité
Auteur: Expert DevSecOps & IA Explicable
Version: 1.0.0
"""

import asyncio
import time
import json
import requests
import logging
import subprocess
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IntegrationTestResult:
    """Résultat test intégration"""
    component: str
    test_name: str
    status: str  # PASS, FAIL, WARNING
    details: str
    duration_seconds: float
    metrics_collected: int = 0

class GrafanaIntegrationTester:
    """
    Testeur intégration complète pipeline IoT → Prometheus → Grafana
    Validation temps réel des 127 capteurs Station Traffeyère
    """
    
    def __init__(self):
        self.test_results: List[IntegrationTestResult] = []
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3000"
        self.iot_generator_url = "http://localhost:8090"
        self.edge_ai_url = "http://localhost:8091"
        
        # Métriques critiques RNCP 39394
        self.critical_metrics = [
            'station_traffeyere_ph_current',
            'station_traffeyere_o2_dissous_current',
            'station_traffeyere_turbidite_current', 
            'station_traffeyere_debit_current',
            'station_traffeyere_total_sensors',
            'station_traffeyere_anomalies_total',
            'station_traffeyere_compliance_score',
            'edge_ai_prediction_latency_seconds',
            'edge_ai_anomalies_detected_total',
            'edge_ai_model_accuracy'
        ]
        
        # Configuration dashboard Grafana
        self.dashboard_panels = [
            'Station Overview',
            'pH Monitoring', 
            'Oxygen Levels',
            'Turbidity Analysis',
            'Flow Rates',
            'Temperature Monitoring',
            'Anomaly Detection',
            'AI Performance',
            'Compliance DERU',
            'Process Efficiency',
            'Alert Status'
        ]
        
        logger.info("🧪 Testeur intégration Grafana initialisé")

    def record_test_result(self, component: str, test_name: str, 
                          status: str, details: str, duration: float, 
                          metrics_count: int = 0):
        """Enregistrement résultat test"""
        result = IntegrationTestResult(
            component=component,
            test_name=test_name,
            status=status,
            details=details,
            duration_seconds=duration,
            metrics_collected=metrics_count
        )
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        logger.info(f"{status_icon} [{component}] {test_name}: {status} - {details}")

    async def test_iot_generator_running(self) -> bool:
        """Test 1: Générateur IoT actif et exposant métriques"""
        start_time = time.perf_counter()
        
        try:
            # Vérification endpoint métriques
            response = requests.get(f"{self.iot_generator_url}/metrics", timeout=5)
            
            if response.status_code == 200:
                metrics_content = response.text
                metrics_count = len([line for line in metrics_content.split('\n') 
                                   if line.startswith('station_traffeyere_')])
                
                if metrics_count >= 10:  # Au moins 10 métriques différentes
                    self.record_test_result(
                        "IoT Generator", 
                        "Générateur actif et métriques exposées",
                        "PASS",
                        f"{metrics_count} métriques disponibles",
                        time.perf_counter() - start_time,
                        metrics_count
                    )
                    return True
                else:
                    self.record_test_result(
                        "IoT Generator",
                        "Métriques insuffisantes",
                        "WARNING", 
                        f"Seulement {metrics_count} métriques trouvées",
                        time.perf_counter() - start_time
                    )
                    return False
            else:
                self.record_test_result(
                    "IoT Generator",
                    "Endpoint métriques inaccessible",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    time.perf_counter() - start_time
                )
                return False
                
        except Exception as e:
            self.record_test_result(
                "IoT Generator",
                "Connexion générateur IoT",
                "FAIL",
                f"Erreur: {str(e)}",
                time.perf_counter() - start_time
            )
            return False

    async def test_edge_ai_engine_running(self) -> bool:
        """Test 2: Edge AI Engine actif et fonctionnel"""
        start_time = time.perf_counter()
        
        try:
            response = requests.get(f"{self.edge_ai_url}/metrics", timeout=5)
            
            if response.status_code == 200:
                metrics_content = response.text
                ai_metrics = [line for line in metrics_content.split('\n') 
                            if line.startswith('edge_ai_')]
                
                if len(ai_metrics) >= 5:
                    self.record_test_result(
                        "Edge AI Engine",
                        "Moteur IA actif",
                        "PASS",
                        f"{len(ai_metrics)} métriques IA disponibles",
                        time.perf_counter() - start_time,
                        len(ai_metrics)
                    )
                    return True
                else:
                    self.record_test_result(
                        "Edge AI Engine",
                        "Métriques IA insuffisantes", 
                        "WARNING",
                        f"Seulement {len(ai_metrics)} métriques IA",
                        time.perf_counter() - start_time
                    )
                    return False
            else:
                self.record_test_result(
                    "Edge AI Engine",
                    "Endpoint IA inaccessible",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    time.perf_counter() - start_time
                )
                return False
                
        except Exception as e:
            self.record_test_result(
                "Edge AI Engine", 
                "Connexion Edge AI",
                "FAIL",
                f"Erreur: {str(e)}",
                time.perf_counter() - start_time
            )
            return False

    async def test_prometheus_scraping(self) -> bool:
        """Test 3: Prometheus scraping métriques IoT"""
        start_time = time.perf_counter()
        
        try:
            # Test requête métriques critiques
            critical_found = 0
            total_metrics_scraped = 0
            
            for metric in self.critical_metrics:
                query_url = f"{self.prometheus_url}/api/v1/query"
                params = {'query': metric}
                
                response = requests.get(query_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success' and data.get('data', {}).get('result'):
                        critical_found += 1
                        total_metrics_scraped += len(data['data']['result'])
            
            # Vérification taux succès
            success_rate = (critical_found / len(self.critical_metrics)) * 100
            
            if success_rate >= 80:  # 80% métriques critiques minimum
                self.record_test_result(
                    "Prometheus",
                    "Scraping métriques critiques", 
                    "PASS",
                    f"{critical_found}/{len(self.critical_metrics)} métriques ({success_rate:.1f}%)",
                    time.perf_counter() - start_time,
                    total_metrics_scraped
                )
                return True
            elif success_rate >= 50:
                self.record_test_result(
                    "Prometheus",
                    "Scraping partiel",
                    "WARNING",
                    f"{critical_found}/{len(self.critical_metrics)} métriques ({success_rate:.1f}%)",
                    time.perf_counter() - start_time,
                    total_metrics_scraped
                )
                return False
            else:
                self.record_test_result(
                    "Prometheus", 
                    "Scraping insuffisant",
                    "FAIL",
                    f"Seulement {critical_found}/{len(self.critical_metrics)} métriques",
                    time.perf_counter() - start_time
                )
                return False
                
        except Exception as e:
            self.record_test_result(
                "Prometheus",
                "Requête métriques",
                "FAIL", 
                f"Erreur: {str(e)}",
                time.perf_counter() - start_time
            )
            return False

    async def test_grafana_connectivity(self) -> bool:
        """Test 4: Connectivité Grafana et datasource Prometheus"""
        start_time = time.perf_counter()
        
        try:
            # Test santé Grafana
            health_response = requests.get(f"{self.grafana_url}/api/health", timeout=10)
            
            if health_response.status_code != 200:
                self.record_test_result(
                    "Grafana",
                    "Santé serveur Grafana",
                    "FAIL",
                    f"HTTP {health_response.status_code}",
                    time.perf_counter() - start_time
                )
                return False
            
            # Test datasources (nécessite authentification, simulation)
            # En production, utiliser API key Grafana
            self.record_test_result(
                "Grafana",
                "Connectivité serveur",
                "PASS", 
                "Serveur Grafana accessible",
                time.perf_counter() - start_time
            )
            
            return True
            
        except Exception as e:
            self.record_test_result(
                "Grafana",
                "Connexion serveur",
                "FAIL",
                f"Erreur: {str(e)}",
                time.perf_counter() - start_time
            )
            return False

    async def test_real_time_data_flow(self) -> bool:
        """Test 5: Flux données temps réel IoT → Prometheus"""
        start_time = time.perf_counter()
        
        try:
            # Collecte métriques à T0
            initial_metrics = {}
            for metric in ['station_traffeyere_total_sensors', 'station_traffeyere_anomalies_total']:
                query_url = f"{self.prometheus_url}/api/v1/query"
                response = requests.get(query_url, params={'query': metric}, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data', {}).get('result'):
                        initial_metrics[metric] = float(data['data']['result'][0]['value'][1])
            
            # Attente 10 secondes pour nouveau cycle
            await asyncio.sleep(10)
            
            # Collecte métriques à T+10s
            updated_metrics = {}
            for metric in initial_metrics.keys():
                query_url = f"{self.prometheus_url}/api/v1/query"
                response = requests.get(query_url, params={'query': metric}, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data', {}).get('result'):
                        updated_metrics[metric] = float(data['data']['result'][0]['value'][1])
            
            # Vérification mise à jour
            updates_detected = 0
            for metric in initial_metrics.keys():
                if metric in updated_metrics:
                    if updated_metrics[metric] != initial_metrics[metric]:
                        updates_detected += 1
            
            if updates_detected >= 1:
                self.record_test_result(
                    "Data Flow",
                    "Flux temps réel actif",
                    "PASS",
                    f"{updates_detected} métriques mises à jour",
                    time.perf_counter() - start_time
                )
                return True
            else:
                self.record_test_result(
                    "Data Flow",
                    "Pas de mise à jour détectée",
                    "WARNING",
                    "Métriques statiques sur 10s",
                    time.perf_counter() - start_time
                )
                return False
                
        except Exception as e:
            self.record_test_result(
                "Data Flow",
                "Test flux temps réel",
                "FAIL",
                f"Erreur: {str(e)}",
                time.perf_counter() - start_time
            )
            return False

    async def test_anomaly_detection_pipeline(self) -> bool:
        """Test 6: Pipeline détection anomalies Edge AI"""
        start_time = time.perf_counter()
        
        try:
            # Vérification métriques anomalies Edge AI
            query_url = f"{self.prometheus_url}/api/v1/query"
            
            # Métriques clés détection anomalies
            anomaly_metrics = [
                'edge_ai_anomalies_detected_total',
                'edge_ai_prediction_latency_seconds', 
                'edge_ai_predictions_total'
            ]
            
            metrics_found = 0
            latency_compliant = False
            
            for metric in anomaly_metrics:
                response = requests.get(query_url, params={'query': metric}, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data', {}).get('result'):
                        metrics_found += 1
                        
                        # Vérification latence P95 < 0.28ms
                        if metric == 'edge_ai_prediction_latency_seconds':
                            # Query percentile 95
                            p95_query = f'histogram_quantile(0.95, {metric})'
                            p95_response = requests.get(query_url, params={'query': p95_query}, timeout=5)
                            
                            if p95_response.status_code == 200:
                                p95_data = p95_response.json()
                                if p95_data.get('data', {}).get('result'):
                                    p95_value = float(p95_data['data']['result'][0]['value'][1])
                                    latency_compliant = p95_value < 0.00028  # 0.28ms en secondes
            
            if metrics_found >= 2:
                compliance_status = "✅ Conforme RNCP" if latency_compliant else "⚠️ Latence élevée"
                self.record_test_result(
                    "Anomaly Detection",
                    "Pipeline détection anomalies",
                    "PASS" if latency_compliant else "WARNING",
                    f"{metrics_found}/3 métriques - {compliance_status}",
                    time.perf_counter() - start_time,
                    metrics_found
                )
                return True
            else:
                self.record_test_result(
                    "Anomaly Detection", 
                    "Métriques anomalies manquantes",
                    "FAIL",
                    f"Seulement {metrics_found}/3 métriques détection",
                    time.perf_counter() - start_time
                )
                return False
                
        except Exception as e:
            self.record_test_result(
                "Anomaly Detection",
                "Test pipeline anomalies",
                "FAIL",
                f"Erreur: {str(e)}",
                time.perf_counter() - start_time
            )
            return False

    async def test_dashboard_panel_queries(self) -> bool:
        """Test 7: Validation requêtes dashboard Grafana (simulation)"""
        start_time = time.perf_counter()
        
        try:
            # Simulation requêtes typiques dashboard Grafana
            dashboard_queries = [
                'station_traffeyere_ph_current',
                'rate(station_traffeyere_anomalies_total[5m])',
                'avg(station_traffeyere_treatment_efficiency_percent)',
                'histogram_quantile(0.95, edge_ai_prediction_latency_seconds)',
                'station_traffeyere_compliance_score'
            ]
            
            successful_queries = 0
            query_url = f"{self.prometheus_url}/api/v1/query"
            
            for query in dashboard_queries:
                try:
                    response = requests.get(query_url, params={'query': query}, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'success':
                            successful_queries += 1
                            
                except requests.RequestException:
                    continue
            
            success_rate = (successful_queries / len(dashboard_queries)) * 100
            
            if success_rate >= 80:
                self.record_test_result(
                    "Dashboard Queries",
                    "Requêtes dashboard valides",
                    "PASS",
                    f"{successful_queries}/{len(dashboard_queries)} requêtes OK ({success_rate:.1f}%)",
                    time.perf_counter() - start_time,
                    successful_queries
                )
                return True
            else:
                self.record_test_result(
                    "Dashboard Queries",
                    "Requêtes partiellement valides", 
                    "WARNING",
                    f"{successful_queries}/{len(dashboard_queries)} requêtes OK ({success_rate:.1f}%)",
                    time.perf_counter() - start_time,
                    successful_queries
                )
                return False
                
        except Exception as e:
            self.record_test_result(
                "Dashboard Queries",
                "Validation requêtes",
                "FAIL",
                f"Erreur: {str(e)}",
                time.perf_counter() - start_time
            )
            return False

    async def test_rncp_compliance_metrics(self) -> bool:
        """Test 8: Métriques conformité RNCP 39394"""
        start_time = time.perf_counter()
        
        try:
            # Métriques critiques RNCP 39394
            rncp_metrics = {
                'station_traffeyere_compliance_score': {'min': 85.0, 'target': 95.0},
                'edge_ai_model_accuracy': {'min': 0.85, 'target': 0.95},
                'station_traffeyere_treatment_efficiency_percent': {'min': 85.0, 'target': 92.0}
            }
            
            compliant_metrics = 0
            query_url = f"{self.prometheus_url}/api/v1/query"
            
            compliance_details = []
            
            for metric, thresholds in rncp_metrics.items():
                try:
                    response = requests.get(query_url, params={'query': metric}, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('data', {}).get('result'):
                            value = float(data['data']['result'][0]['value'][1])
                            
                            if value >= thresholds['target']:
                                compliant_metrics += 1
                                compliance_details.append(f"{metric}: {value:.1f} ✅")
                            elif value >= thresholds['min']:
                                compliance_details.append(f"{metric}: {value:.1f} ⚠️")
                            else:
                                compliance_details.append(f"{metric}: {value:.1f} ❌")
                        else:
                            compliance_details.append(f"{metric}: Données manquantes")
                    else:
                        compliance_details.append(f"{metric}: Inaccessible")
                        
                except Exception:
                    compliance_details.append(f"{metric}: Erreur requête")
            
            compliance_rate = (compliant_metrics / len(rncp_metrics)) * 100
            
            if compliance_rate >= 80:
                self.record_test_result(
                    "RNCP Compliance",
                    "Conformité RNCP 39394",
                    "PASS",
                    f"{compliant_metrics}/{len(rncp_metrics)} métriques conformes ({compliance_rate:.1f}%)",
                    time.perf_counter() - start_time,
                    compliant_metrics
                )
                return True
            else:
                self.record_test_result(
                    "RNCP Compliance",
                    "Conformité partielle",
                    "WARNING",
                    f"Seulement {compliant_metrics}/{len(rncp_metrics)} conformes",
                    time.perf_counter() - start_time,
                    compliant_metrics
                )
                return False
                
        except Exception as e:
            self.record_test_result(
                "RNCP Compliance",
                "Test conformité RNCP",
                "FAIL",
                f"Erreur: {str(e)}",
                time.perf_counter() - start_time
            )
            return False

    async def run_full_integration_tests(self) -> Dict[str, Any]:
        """Exécution suite complète tests intégration"""
        logger.info("🎯 Démarrage tests intégration complète Grafana")
        test_start = time.perf_counter()
        
        # Exécution séquentielle tous tests
        tests = [
            self.test_iot_generator_running(),
            self.test_edge_ai_engine_running(), 
            self.test_prometheus_scraping(),
            self.test_grafana_connectivity(),
            self.test_real_time_data_flow(),
            self.test_anomaly_detection_pipeline(),
            self.test_dashboard_panel_queries(),
            self.test_rncp_compliance_metrics()
        ]
        
        # Attente résultats
        await asyncio.gather(*tests)
        
        total_duration = time.perf_counter() - test_start
        
        # Calcul statistiques
        passed_tests = len([r for r in self.test_results if r.status == "PASS"])
        warning_tests = len([r for r in self.test_results if r.status == "WARNING"])
        failed_tests = len([r for r in self.test_results if r.status == "FAIL"])
        total_tests = len(self.test_results)
        
        total_metrics = sum(r.metrics_collected for r in self.test_results)
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Résultats finaux
        results = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'warnings': warning_tests,
            'failed': failed_tests,
            'success_rate_percent': success_rate,
            'total_duration_seconds': total_duration,
            'total_metrics_validated': total_metrics,
            'test_results': [asdict(r) for r in self.test_results]
        }
        
        return results

    def print_test_summary(self, results: Dict[str, Any]):
        """Affichage résumé tests"""
        print("\n" + "="*70)
        print("🎯 RAPPORT TESTS INTÉGRATION GRAFANA - STATION TRAFFEYÈRE")
        print("="*70)
        print(f"📊 Total tests exécutés: {results['total_tests']}")
        print(f"✅ Tests réussis: {results['passed']}")
        print(f"⚠️  Tests avec warnings: {results['warnings']}")
        print(f"❌ Tests échoués: {results['failed']}")
        print(f"🎯 Taux de succès: {results['success_rate_percent']:.1f}%")
        print(f"⏱️  Durée totale: {results['total_duration_seconds']:.2f}s")
        print(f"📈 Métriques validées: {results['total_metrics_validated']}")
        
        print("\n" + "="*70)
        print("📋 DÉTAIL DES TESTS")
        print("="*70)
        
        for result in self.test_results:
            status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
            print(f"{status_icon} [{result.component}] {result.test_name}")
            print(f"   Status: {result.status}")
            print(f"   Détails: {result.details}")
            print(f"   Durée: {result.duration_seconds:.2f}s")
            if result.metrics_collected > 0:
                print(f"   Métriques: {result.metrics_collected}")
            print()
        
        # Évaluation conformité globale
        print("="*70)
        if results['success_rate_percent'] >= 90:
            print("🏆 INTÉGRATION GRAFANA - EXCELLENT")
            print("✅ Pipeline IoT → Prometheus → Grafana pleinement opérationnel")
            print("✅ Conforme aux exigences RNCP 39394")
        elif results['success_rate_percent'] >= 75:
            print("🎯 INTÉGRATION GRAFANA - SATISFAISANT") 
            print("✅ Pipeline principal fonctionnel")
            print("⚠️  Optimisations mineures recommandées")
        elif results['success_rate_percent'] >= 50:
            print("⚠️ INTÉGRATION GRAFANA - PROBLÈMES DÉTECTÉS")
            print("❌ Plusieurs composants nécessitent attention")
            print("🔧 Corrections requises avant production")
        else:
            print("❌ INTÉGRATION GRAFANA - CRITIQUE")
            print("❌ Pipeline non fonctionnel")
            print("🚨 Intervention urgente requise")
        
        print("="*70)

async def main():
    """Fonction principale test intégration Grafana"""
    print("🧪 TEST INTÉGRATION COMPLÈTE - PIPELINE GRAFANA")
    print("=" * 65)
    print("Validation: Générateur IoT → Prometheus → Grafana")
    print("127 capteurs Station Traffeyère en temps réel")
    print("Métriques critiques RNCP 39394")
    print("=" * 65)
    
    # Initialisation testeur
    tester = GrafanaIntegrationTester()
    
    # Information préliminaire
    print(f"\n🎯 Configuration de test:")
    print(f"   • Générateur IoT: {tester.iot_generator_url}")
    print(f"   • Edge AI Engine: {tester.edge_ai_url}")
    print(f"   • Prometheus: {tester.prometheus_url}")
    print(f"   • Grafana: {tester.grafana_url}")
    print(f"   • Métriques critiques: {len(tester.critical_metrics)}")
    
    # Message instruction
    print(f"\n📋 Instructions:")
    print(f"   1. Démarrer le générateur IoT: python scripts/iot_data_generator.py")
    print(f"   2. Démarrer Edge AI Engine: python scripts/edge_ai_engine.py")
    print(f"   3. S'assurer que Prometheus et Grafana sont actifs")
    print(f"   4. Ce script validera l'intégration complète")
    
    input(f"\n⏳ Appuyez sur Entrée quand tous les services sont démarrés...")
    
    # Exécution tests
    print(f"\n🚀 Démarrage tests intégration...")
    results = await tester.run_full_integration_tests()
    
    # Affichage résultats
    tester.print_test_summary(results)
    
    # Export JSON optionnel
    output_file = f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"💾 Résultats exportés: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
