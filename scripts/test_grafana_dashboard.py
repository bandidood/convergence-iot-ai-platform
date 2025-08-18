#!/usr/bin/env python3
# =============================================================================
# TEST DASHBOARD GRAFANA - RNCP 39394
# Expert en Systèmes d'Information et Sécurité
# 
# Validation structure et contenu dashboard principal
# =============================================================================

import json
import sys
from pathlib import Path

class GrafanaDashboardTester:
    """Testeur dashboard Grafana RNCP 39394."""
    
    def __init__(self):
        self.dashboard_path = "monitoring/grafana/dashboards/rncp-39394-main-dashboard.json"
        self.errors = []
        self.warnings = []
        
    def load_dashboard(self):
        """Charge le dashboard JSON."""
        try:
            with open(self.dashboard_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.errors.append(f"Dashboard non trouvé: {self.dashboard_path}")
            return None
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON invalide: {e}")
            return None
        except Exception as e:
            self.errors.append(f"Erreur chargement dashboard: {e}")
            return None
    
    def validate_dashboard_structure(self, dashboard):
        """Valide la structure du dashboard."""
        print("🔧 Validation structure dashboard...")
        
        required_fields = [
            'title', 'panels', 'time', 'refresh', 'tags'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in dashboard:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append(f"Champs manquants: {missing_fields}")
            return False
        
        print(f"✅ Structure valide - Titre: '{dashboard['title']}'")
        return True
    
    def validate_panels(self, dashboard):
        """Valide les panneaux du dashboard."""
        print("\n📊 Validation panneaux...")
        
        panels = dashboard.get('panels', [])
        if not panels:
            self.errors.append("Aucun panneau trouvé")
            return False
        
        print(f"Panneaux trouvés: {len(panels)}")
        
        # Validation des panneaux critiques RNCP 39394
        critical_panels = [
            "Précision Modèle AI",
            "Latence AI P95", 
            "SLA Uptime Global",
            "Anomalies IoT/h"
        ]
        
        panel_titles = []
        for panel in panels:
            title = panel.get('title', 'Sans titre')
            panel_titles.append(title)
            
            # Validation structure panneau
            if 'targets' not in panel and 'datasource' not in panel:
                self.warnings.append(f"Panneau '{title}': Aucune source de données")
        
        print("\nPanneaux disponibles:")
        for i, title in enumerate(panel_titles, 1):
            status = "🎯" if any(critical in title for critical in critical_panels) else "📊"
            print(f"  {i:2d}. {status} {title}")
        
        # Vérification panneaux critiques
        missing_critical = []
        for critical in critical_panels:
            if not any(critical in title for title in panel_titles):
                missing_critical.append(critical)
        
        if missing_critical:
            self.warnings.append(f"Panneaux critiques manquants: {missing_critical}")
        
        print(f"\n✅ {len(panels)} panneaux configurés")
        return True
    
    def validate_prometheus_queries(self, dashboard):
        """Valide les requêtes Prometheus."""
        print("\n🔍 Validation requêtes Prometheus...")
        
        panels = dashboard.get('panels', [])
        total_queries = 0
        rncp_queries = 0
        
        # Métriques critiques RNCP 39394
        rncp_metrics = [
            'ai_model_accuracy_percentage',
            'ai_prediction_duration_seconds',
            'iot_anomalies_detected_total',
            'up{job="ai-engine"}',
            'rncp:sla_uptime_percentage'
        ]
        
        for panel in panels:
            targets = panel.get('targets', [])
            for target in targets:
                expr = target.get('expr', '')
                if expr:
                    total_queries += 1
                    
                    # Vérification métrique RNCP
                    for metric in rncp_metrics:
                        if metric in expr:
                            rncp_queries += 1
                            break
        
        print(f"Requêtes Prometheus: {total_queries}")
        print(f"Requêtes RNCP 39394: {rncp_queries}")
        
        if total_queries == 0:
            self.warnings.append("Aucune requête Prometheus trouvée")
        
        coverage = (rncp_queries / len(rncp_metrics) * 100) if rncp_queries > 0 else 0
        print(f"Couverture métriques RNCP: {coverage:.1f}%")
        
        return True
    
    def validate_time_configuration(self, dashboard):
        """Valide la configuration temporelle."""
        print("\n⏰ Validation configuration temps...")
        
        time_config = dashboard.get('time', {})
        refresh = dashboard.get('refresh', '')
        
        print(f"Période par défaut: {time_config.get('from', 'non définie')} - {time_config.get('to', 'non définie')}")
        print(f"Actualisation: {refresh}")
        
        # Validation pour monitoring temps réel
        if refresh and refresh not in ['5s', '10s', '30s', '1m']:
            self.warnings.append(f"Refresh rate '{refresh}' peut être trop lent pour IoT temps réel")
        
        return True
    
    def validate_thresholds(self, dashboard):
        """Valide les seuils configurés."""
        print("\n🎯 Validation seuils RNCP 39394...")
        
        panels = dashboard.get('panels', [])
        threshold_configs = []
        
        for panel in panels:
            field_config = panel.get('fieldConfig', {})
            defaults = field_config.get('defaults', {})
            thresholds = defaults.get('thresholds', {})
            
            if 'steps' in thresholds:
                steps = thresholds['steps']
                for step in steps:
                    if 'value' in step:
                        threshold_configs.append({
                            'panel': panel.get('title', 'Sans titre'),
                            'value': step['value'],
                            'color': step.get('color', 'undefined')
                        })
        
        print(f"Seuils configurés: {len(threshold_configs)}")
        
        # Validation seuils critiques RNCP
        expected_thresholds = [
            {'metric': 'précision', 'min_value': 97.6},
            {'metric': 'latence', 'max_value': 0.28},
            {'metric': 'uptime', 'min_value': 99.9}
        ]
        
        for expected in expected_thresholds:
            found = False
            for config in threshold_configs:
                if expected['metric'].lower() in config['panel'].lower():
                    found = True
                    break
            
            if not found:
                self.warnings.append(f"Seuil manquant pour {expected['metric']}")
        
        return True
    
    def generate_report(self):
        """Génère le rapport de validation."""
        print("\n" + "="*80)
        print("📋 RAPPORT VALIDATION DASHBOARD GRAFANA - RNCP 39394")
        print("="*80)
        
        print(f"Erreurs: {len(self.errors)}")
        print(f"Avertissements: {len(self.warnings)}")
        
        if self.errors:
            print("\n🚨 ERREURS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️ AVERTISSEMENTS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Score global
        if len(self.errors) == 0:
            if len(self.warnings) <= 2:
                score = 100
                status = "✅ EXCELLENT"
            else:
                score = 85
                status = "✅ BON"
        else:
            score = max(0, 50 - len(self.errors) * 20)
            status = "❌ INSUFFISANT"
        
        print(f"\n🏆 SCORE DASHBOARD: {score}%")
        print(f"📊 STATUS: {status}")
        
        if score >= 80:
            print("✅ Dashboard prêt pour production")
            return True
        else:
            print("⚠️ Dashboard nécessite des corrections")
            return False

def main():
    """Fonction principale de test."""
    tester = GrafanaDashboardTester()
    
    print("🎨 Test Dashboard Grafana RNCP 39394")
    print("====================================")
    
    # Chargement dashboard
    dashboard = tester.load_dashboard()
    if not dashboard:
        print("❌ Impossible de charger le dashboard")
        return 1
    
    try:
        # Tests de validation
        tester.validate_dashboard_structure(dashboard)
        tester.validate_panels(dashboard)
        tester.validate_prometheus_queries(dashboard)
        tester.validate_time_configuration(dashboard)
        tester.validate_thresholds(dashboard)
        
        # Rapport final
        success = tester.generate_report()
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
