#!/usr/bin/env python3
# =============================================================================
# VALIDATION SEUILS PERFORMANCE - RNCP 39394
# Expert en Systèmes d'Information et Sécurité
# 
# Validation automatique des KPIs pour pipeline CI/CD
# Conformité objectifs: <0.28ms latence, 97.6% précision
# =============================================================================

import sys
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# SEUILS DE PERFORMANCE RNCP 39394
# =============================================================================
PERFORMANCE_THRESHOLDS = {
    'latency_p95_ms': {
        'threshold': 0.28,
        'operator': '<',
        'description': 'Latence P95 prédictions AI',
        'unit': 'ms',
        'critical': True
    },
    'accuracy_percentage': {
        'threshold': 97.6,
        'operator': '>=',
        'description': 'Précision modèle AI',
        'unit': '%',
        'critical': True
    },
    'throughput_predictions_per_sec': {
        'threshold': 100,
        'operator': '>=',
        'description': 'Throughput minimum',
        'unit': 'predictions/sec',
        'critical': False
    },
    'memory_usage_mb': {
        'threshold': 2048,
        'operator': '<',
        'description': 'Utilisation mémoire',
        'unit': 'MB',
        'critical': False
    },
    'cpu_usage_percentage': {
        'threshold': 80,
        'operator': '<',
        'description': 'Utilisation CPU',
        'unit': '%',
        'critical': False
    },
    'gpu_utilization_percentage': {
        'threshold': 95,
        'operator': '<',
        'description': 'Utilisation GPU',
        'unit': '%',
        'critical': False
    },
    'error_rate_percentage': {
        'threshold': 0.1,
        'operator': '<',
        'description': 'Taux d\'erreur',
        'unit': '%',
        'critical': True
    }
}

class PerformanceValidator:
    """Validateur de seuils de performance pour RNCP 39394."""
    
    def __init__(self):
        self.results = {}
        self.failures = []
        self.warnings = []
        
    def parse_benchmark_results(self, file_path: str) -> Dict[str, float]:
        """Parse les résultats de benchmark depuis un fichier texte."""
        metrics = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Patterns de parsing pour différents formats
            patterns = {
                'latency_p95_ms': [
                    r'Latence moyenne:\s*([0-9.]+)\s*ms',
                    r'Average latency:\s*([0-9.]+)\s*ms',
                    r'P95 latency:\s*([0-9.]+)\s*ms'
                ],
                'accuracy_percentage': [
                    r'Précision:\s*([0-9.]+)%',
                    r'Accuracy:\s*([0-9.]+)%',
                    r'Model accuracy:\s*([0-9.]+)%'
                ],
                'throughput_predictions_per_sec': [
                    r'Débit:\s*([0-9.]+)\s*prédictions/seconde',
                    r'Throughput:\s*([0-9.]+)\s*predictions/sec',
                    r'Rate:\s*([0-9.]+)\s*pred/s'
                ],
                'memory_usage_mb': [
                    r'Mémoire utilisée:\s*([0-9.]+)\s*MB',
                    r'Memory usage:\s*([0-9.]+)\s*MB'
                ],
                'cpu_usage_percentage': [
                    r'CPU:\s*([0-9.]+)%',
                    r'CPU usage:\s*([0-9.]+)%'
                ],
                'error_rate_percentage': [
                    r'Taux d\'erreur:\s*([0-9.]+)%',
                    r'Error rate:\s*([0-9.]+)%'
                ]
            }
            
            # Parse chaque métrique
            for metric, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        metrics[metric] = float(match.group(1))
                        break
            
            logger.info(f"Métriques parsées: {metrics}")
            return metrics
            
        except FileNotFoundError:
            logger.error(f"Fichier benchmark non trouvé: {file_path}")
            return {}
        except Exception as e:
            logger.error(f"Erreur parsing benchmark: {e}")
            return {}
    
    def validate_threshold(self, metric: str, value: float, config: Dict[str, Any]) -> bool:
        """Valide une métrique contre son seuil."""
        threshold = config['threshold']
        operator = config['operator']
        
        if operator == '<':
            valid = value < threshold
        elif operator == '<=':
            valid = value <= threshold
        elif operator == '>':
            valid = value > threshold
        elif operator == '>=':
            valid = value >= threshold
        elif operator == '==':
            valid = value == threshold
        else:
            logger.error(f"Opérateur inconnu: {operator}")
            return False
        
        result = {
            'metric': metric,
            'value': value,
            'threshold': threshold,
            'operator': operator,
            'valid': valid,
            'description': config['description'],
            'unit': config['unit'],
            'critical': config['critical']
        }
        
        self.results[metric] = result
        
        if not valid:
            message = (f"{config['description']}: {value}{config['unit']} "
                      f"{operator} {threshold}{config['unit']} - ÉCHEC")
            
            if config['critical']:
                self.failures.append(message)
                logger.error(message)
            else:
                self.warnings.append(message)
                logger.warning(message)
        else:
            logger.info(f"{config['description']}: {value}{config['unit']} - OK")
        
        return valid
    
    def validate_all(self, metrics: Dict[str, float]) -> bool:
        """Valide toutes les métriques contre les seuils."""
        all_valid = True
        
        for metric, config in PERFORMANCE_THRESHOLDS.items():
            if metric in metrics:
                valid = self.validate_threshold(metric, metrics[metric], config)
                if not valid and config['critical']:
                    all_valid = False
            else:
                logger.warning(f"Métrique manquante: {metric}")
        
        return all_valid
    
    def generate_report(self) -> Dict[str, Any]:
        """Génère un rapport de validation."""
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'total_metrics': len(self.results),
            'passed': sum(1 for r in self.results.values() if r['valid']),
            'failed': sum(1 for r in self.results.values() if not r['valid']),
            'critical_failures': len(self.failures),
            'warnings': len(self.warnings),
            'overall_status': 'PASS' if not self.failures else 'FAIL',
            'details': self.results,
            'failure_messages': self.failures,
            'warning_messages': self.warnings
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str):
        """Sauvegarde le rapport en JSON."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Rapport sauvegardé: {output_path}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde rapport: {e}")

def main():
    """Fonction principale de validation."""
    validator = PerformanceValidator()
    
    # Chemins des fichiers
    benchmark_file = "benchmark-results.txt"
    report_file = "performance-metrics.json"
    
    logger.info("🚀 Démarrage validation seuils performance RNCP 39394")
    
    # Parse des résultats de benchmark
    metrics = validator.parse_benchmark_results(benchmark_file)
    
    if not metrics:
        logger.error("❌ Aucune métrique trouvée dans le benchmark")
        sys.exit(1)
    
    # Validation des seuils
    all_valid = validator.validate_all(metrics)
    
    # Génération du rapport
    report = validator.generate_report()
    validator.save_report(report, report_file)
    
    # Résumé des résultats
    print("\n" + "="*80)
    print("📊 RAPPORT DE VALIDATION PERFORMANCE - RNCP 39394")
    print("="*80)
    print(f"Status global: {'✅ SUCCÈS' if report['overall_status'] == 'PASS' else '❌ ÉCHEC'}")
    print(f"Métriques validées: {report['passed']}/{report['total_metrics']}")
    print(f"Échecs critiques: {report['critical_failures']}")
    print(f"Avertissements: {report['warnings']}")
    
    if report['failure_messages']:
        print(f"\n🚨 ÉCHECS CRITIQUES:")
        for failure in report['failure_messages']:
            print(f"  - {failure}")
    
    if report['warning_messages']:
        print(f"\n⚠️  AVERTISSEMENTS:")
        for warning in report['warning_messages']:
            print(f"  - {warning}")
    
    print(f"\n📄 Rapport détaillé: {report_file}")
    print("="*80)
    
    # Exit code pour CI/CD
    if all_valid:
        logger.info("✅ Tous les seuils de performance respectés")
        sys.exit(0)
    else:
        logger.error("❌ Seuils de performance non respectés")
        sys.exit(1)

if __name__ == "__main__":
    main()
