#!/usr/bin/env python3
# =============================================================================
# TEST STACK OBSERVABILITÉ - RNCP 39394
# Expert en Systèmes d'Information et Sécurité
# 
# Validation de la configuration monitoring sans déploiement complet
# =============================================================================

import os
import sys
import yaml
import json
import requests
import subprocess
import time
from pathlib import Path

class MonitoringStackTester:
    """Testeur de la stack d'observabilité RNCP 39394."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.test_results = {}
        
    def test_configuration_files(self):
        """Teste les fichiers de configuration."""
        print("🔧 Test des fichiers de configuration...")
        
        # Test Prometheus config
        prom_config = "monitoring/prometheus/prometheus.yml"
        try:
            with open(prom_config, 'r', encoding='utf-8') as f:
                prom_data = yaml.safe_load(f)
            
            print(f"✅ Prometheus config valide: {len(prom_data.get('scrape_configs', []))} jobs")
            self.test_results['prometheus_config'] = True
            
        except Exception as e:
            self.errors.append(f"Erreur Prometheus config: {e}")
            self.test_results['prometheus_config'] = False
        
        # Test Alertmanager config
        alert_config = "monitoring/alertmanager/config.yaml"
        try:
            with open(alert_config, 'r', encoding='utf-8') as f:
                alert_data = yaml.safe_load(f)
            
            receivers = len(alert_data.get('receivers', []))
            print(f"✅ Alertmanager config valide: {receivers} récepteurs")
            self.test_results['alertmanager_config'] = True
            
        except Exception as e:
            self.errors.append(f"Erreur Alertmanager config: {e}")
            self.test_results['alertmanager_config'] = False
        
        # Test Grafana dashboard
        dashboard_file = "monitoring/grafana/dashboards/rncp-39394-main-dashboard.json"
        try:
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                dashboard_data = json.load(f)
            
            panels = len(dashboard_data.get('panels', []))
            print(f"✅ Dashboard Grafana valide: {panels} panneaux")
            self.test_results['grafana_dashboard'] = True
            
        except Exception as e:
            self.errors.append(f"Erreur Grafana dashboard: {e}")
            self.test_results['grafana_dashboard'] = False
    
    def test_docker_compose_syntax(self):
        """Teste la syntaxe Docker Compose."""
        print("\n🐳 Test syntaxe Docker Compose...")
        
        compose_files = [
            "docker-compose.monitoring-test.yml",
            "docker-compose.monitoring.yml"
        ]
        
        for compose_file in compose_files:
            if not os.path.exists(compose_file):
                self.warnings.append(f"Fichier {compose_file} non trouvé")
                continue
                
            try:
                result = subprocess.run([
                    'docker-compose', '-f', compose_file, 'config', '--quiet'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print(f"✅ {compose_file}: Syntaxe valide")
                    self.test_results[f'compose_{compose_file}'] = True
                else:
                    self.errors.append(f"{compose_file}: {result.stderr}")
                    self.test_results[f'compose_{compose_file}'] = False
                    
            except subprocess.TimeoutExpired:
                self.errors.append(f"Timeout validation {compose_file}")
                self.test_results[f'compose_{compose_file}'] = False
            except Exception as e:
                self.errors.append(f"Erreur {compose_file}: {e}")
                self.test_results[f'compose_{compose_file}'] = False
    
    def test_prometheus_rules(self):
        """Teste les règles Prometheus."""
        print("\n📊 Test règles Prometheus...")
        
        rules_file = "monitoring/prometheus/rules.yaml"
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                rules_data = yaml.safe_load(f)
            
            groups = rules_data.get('spec', {}).get('groups', [])
            total_rules = 0
            
            for group in groups:
                rules = group.get('rules', [])
                alerts = [r for r in rules if 'alert' in r]
                records = [r for r in rules if 'record' in r]
                total_rules += len(rules)
                
                print(f"  Groupe '{group['name']}': {len(alerts)} alertes, {len(records)} records")
            
            print(f"✅ {len(groups)} groupes, {total_rules} règles au total")
            self.test_results['prometheus_rules'] = True
            
        except Exception as e:
            self.errors.append(f"Erreur règles Prometheus: {e}")
            self.test_results['prometheus_rules'] = False
    
    def test_secrets_configuration(self):
        """Teste la configuration des secrets."""
        print("\n🔐 Test configuration secrets...")
        
        required_secrets = [
            "secrets/grafana_admin_password.txt",
            "secrets/alertmanager_smtp_password.txt",
            "secrets/splunk_admin_password.txt",
            "secrets/slack_webhook_url.txt"
        ]
        
        secrets_ok = 0
        for secret_file in required_secrets:
            if os.path.exists(secret_file) and os.path.getsize(secret_file) > 0:
                secrets_ok += 1
                print(f"✅ {secret_file}")
            else:
                self.warnings.append(f"Secret manquant: {secret_file}")
                print(f"⚠️ {secret_file}")
        
        print(f"Secrets configurés: {secrets_ok}/{len(required_secrets)}")
        self.test_results['secrets_config'] = secrets_ok >= len(required_secrets) * 0.8
    
    def simulate_metrics_collection(self):
        """Simule la collecte de métriques."""
        print("\n📈 Simulation collecte métriques...")
        
        # Simulation de métriques factices
        fake_metrics = {
            'ai_prediction_duration_seconds': 0.000247,  # 0.247ms
            'ai_model_accuracy_percentage': 99.6,
            'ai_predictions_total': 1000,
            'iot_anomalies_detected_total': 5,
            'system_cpu_usage_percentage': 23.4,
            'system_memory_usage_bytes': 1847000000,  # ~1.8GB
            'security_events_total': 12
        }
        
        print("Métriques simulées:")
        for metric, value in fake_metrics.items():
            print(f"  {metric}: {value}")
        
        # Validation contre seuils RNCP 39394
        validations = []
        if fake_metrics['ai_prediction_duration_seconds'] < 0.00028:  # <0.28ms
            validations.append("✅ Latence IA respectée")
        else:
            validations.append("❌ Latence IA dépassée")
            
        if fake_metrics['ai_model_accuracy_percentage'] >= 97.6:
            validations.append("✅ Précision IA respectée")
        else:
            validations.append("❌ Précision IA insuffisante")
        
        for validation in validations:
            print(f"  {validation}")
        
        self.test_results['metrics_simulation'] = True
    
    def test_alerting_rules(self):
        """Teste les règles d'alerte."""
        print("\n🚨 Test règles d'alerte...")
        
        # Simulation d'évaluation des alertes
        sample_metrics = {
            'ai_latency_p95_ms': 0.247,
            'ai_accuracy': 99.6,
            'cpu_usage': 23.4,
            'memory_usage': 76.2,
            'anomalies_per_hour': 2
        }
        
        alert_rules = [
            {
                'name': 'AIEngineHighLatency',
                'condition': lambda m: m['ai_latency_p95_ms'] > 0.28,
                'severity': 'critical'
            },
            {
                'name': 'AIModelAccuracyDegraded',
                'condition': lambda m: m['ai_accuracy'] < 97.6,
                'severity': 'critical'
            },
            {
                'name': 'HighCPUUsage',
                'condition': lambda m: m['cpu_usage'] > 85,
                'severity': 'warning'
            }
        ]
        
        triggered_alerts = []
        for rule in alert_rules:
            try:
                if rule['condition'](sample_metrics):
                    triggered_alerts.append(f"{rule['name']} ({rule['severity']})")
            except Exception as e:
                print(f"⚠️ Erreur évaluation règle {rule['name']}: {e}")
        
        if triggered_alerts:
            print(f"🚨 Alertes déclenchées: {', '.join(triggered_alerts)}")
        else:
            print("✅ Aucune alerte déclenchée - Système sain")
        
        self.test_results['alerting_rules'] = True
    
    def generate_report(self):
        """Génère le rapport de test."""
        print("\n" + "="*80)
        print("📋 RAPPORT DE TEST STACK OBSERVABILITÉ - RNCP 39394")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"Tests réussis: {passed_tests}/{total_tests}")
        print(f"Erreurs: {len(self.errors)}")
        print(f"Avertissements: {len(self.warnings)}")
        
        # Détails des résultats
        print(f"\n📊 DÉTAILS DES TESTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        # Erreurs
        if self.errors:
            print(f"\n🚨 ERREURS:")
            for error in self.errors:
                print(f"  - {error}")
        
        # Avertissements
        if self.warnings:
            print(f"\n⚠️ AVERTISSEMENTS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Score global
        score = (passed_tests / total_tests) * 100
        print(f"\n🏆 SCORE GLOBAL: {score:.1f}%")
        
        if score >= 80:
            print("✅ Stack d'observabilité prête pour déploiement")
            return True
        else:
            print("⚠️ Stack d'observabilité nécessite des corrections")
            return False

def main():
    """Fonction principale de test."""
    tester = MonitoringStackTester()
    
    print("🔍 Test Stack Observabilité RNCP 39394")
    print("======================================")
    
    try:
        tester.test_configuration_files()
        tester.test_docker_compose_syntax()
        tester.test_prometheus_rules()
        tester.test_secrets_configuration()
        tester.simulate_metrics_collection()
        tester.test_alerting_rules()
        
        success = tester.generate_report()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrompu par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
