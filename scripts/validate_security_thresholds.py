#!/usr/bin/env python3
# =============================================================================
# VALIDATION SEUILS SÉCURITÉ - RNCP 39394
# Expert en Systèmes d'Information et Sécurité
# 
# Validation robustesse sécuritaire modèles AI
# Conformité ISA/IEC 62443 + tests adversariaux
# =============================================================================

import sys
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# SEUILS DE SÉCURITÉ RNCP 39394
# =============================================================================
SECURITY_THRESHOLDS = {
    'evasion_robustness_score': {
        'threshold': 0.85,
        'operator': '>=',
        'description': 'Robustesse contre évasion',
        'unit': '',
        'critical': True,
        'isa_requirement': 'SL2-CM-4'
    },
    'poisoning_resistance_score': {
        'threshold': 0.80,
        'operator': '>=',
        'description': 'Résistance empoisonnement',
        'unit': '',
        'critical': True,
        'isa_requirement': 'SL2-CM-3'
    },
    'model_inversion_protection_score': {
        'threshold': 0.75,
        'operator': '>=',
        'description': 'Protection inversion modèle',
        'unit': '',
        'critical': True,
        'isa_requirement': 'SL2-CM-2'
    },
    'membership_inference_resistance': {
        'threshold': 0.70,
        'operator': '>=',
        'description': 'Résistance inférence appartenance',
        'unit': '',
        'critical': False,
        'isa_requirement': 'SL1-CM-1'
    },
    'adversarial_accuracy_drop_percentage': {
        'threshold': 5.0,
        'operator': '<',
        'description': 'Chute précision sous attaque',
        'unit': '%',
        'critical': True,
        'isa_requirement': 'SL2-CM-4'
    },
    'input_validation_effectiveness': {
        'threshold': 0.95,
        'operator': '>=',
        'description': 'Efficacité validation entrées',
        'unit': '',
        'critical': True,
        'isa_requirement': 'SL2-SI-1'
    },
    'anomaly_detection_sensitivity': {
        'threshold': 0.90,
        'operator': '>=',
        'description': 'Sensibilité détection anomalies',
        'unit': '',
        'critical': True,
        'isa_requirement': 'SL2-AN-3'
    }
}

# Mapping des niveaux de sécurité ISA/IEC 62443
ISA_SECURITY_LEVELS = {
    'SL1': 'Protection contre violations fortuites ou casual',
    'SL2': 'Protection contre violations intentionnelles avec ressources limitées',
    'SL3': 'Protection contre violations intentionnelles avec ressources sophistiquées',
    'SL4': 'Protection contre violations d\'État-nation ou équivalent'
}

class SecurityValidator:
    """Validateur de seuils sécuritaires pour RNCP 39394."""
    
    def __init__(self):
        self.results = {}
        self.failures = []
        self.warnings = []
        self.isa_compliance = {}
        
    def parse_security_report(self, file_path: str) -> Dict[str, float]:
        """Parse les résultats de tests de sécurité."""
        metrics = {}
        
        try:
            # Tentative de lecture JSON
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Extract metrics from JSON structure
                    if 'security_scores' in data:
                        metrics.update(data['security_scores'])
                    return metrics
            
            # Lecture fichier texte
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Patterns de parsing pour les rapports de sécurité
            patterns = {
                'evasion_robustness_score': [
                    r'Score de robustesse évasion:\s*([0-9.]+)',
                    r'Evasion robustness:\s*([0-9.]+)',
                    r'Robustesse contre évasion:\s*([0-9.]+)'
                ],
                'poisoning_resistance_score': [
                    r'Score de résistance empoisonnement:\s*([0-9.]+)',
                    r'Poisoning resistance:\s*([0-9.]+)',
                    r'Résistance empoisonnement:\s*([0-9.]+)'
                ],
                'model_inversion_protection_score': [
                    r'Score de protection inversion:\s*([0-9.]+)',
                    r'Model inversion protection:\s*([0-9.]+)',
                    r'Protection inversion modèle:\s*([0-9.]+)'
                ],
                'membership_inference_resistance': [
                    r'Résistance inférence appartenance:\s*([0-9.]+)',
                    r'Membership inference resistance:\s*([0-9.]+)'
                ],
                'adversarial_accuracy_drop_percentage': [
                    r'Chute de précision:\s*([0-9.]+)%',
                    r'Accuracy drop:\s*([0-9.]+)%',
                    r'Baisse précision adversariale:\s*([0-9.]+)%'
                ],
                'input_validation_effectiveness': [
                    r'Efficacité validation entrées:\s*([0-9.]+)',
                    r'Input validation effectiveness:\s*([0-9.]+)'
                ],
                'anomaly_detection_sensitivity': [
                    r'Sensibilité détection anomalies:\s*([0-9.]+)',
                    r'Anomaly detection sensitivity:\s*([0-9.]+)'
                ]
            }
            
            # Parse chaque métrique
            for metric, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        value = float(match.group(1))
                        # Conversion pourcentage si nécessaire
                        if 'percentage' not in metric and value > 1.0 and 'score' in metric:
                            value = value / 100.0
                        metrics[metric] = value
                        break
            
            logger.info(f"Métriques sécurité parsées: {metrics}")
            return metrics
            
        except FileNotFoundError:
            logger.error(f"Fichier rapport sécurité non trouvé: {file_path}")
            return {}
        except Exception as e:
            logger.error(f"Erreur parsing rapport sécurité: {e}")
            return {}
    
    def validate_threshold(self, metric: str, value: float, config: Dict[str, Any]) -> bool:
        """Valide une métrique de sécurité contre son seuil."""
        threshold = config['threshold']
        operator = config['operator']
        isa_req = config['isa_requirement']
        
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
            'critical': config['critical'],
            'isa_requirement': isa_req
        }
        
        self.results[metric] = result
        
        # Tracking conformité ISA/IEC 62443
        security_level = isa_req.split('-')[0]
        if security_level not in self.isa_compliance:
            self.isa_compliance[security_level] = {'total': 0, 'passed': 0}
        
        self.isa_compliance[security_level]['total'] += 1
        if valid:
            self.isa_compliance[security_level]['passed'] += 1
        
        if not valid:
            message = (f"{config['description']}: {value}{config['unit']} "
                      f"{operator} {threshold}{config['unit']} - ÉCHEC (ISA {isa_req})")
            
            if config['critical']:
                self.failures.append(message)
                logger.error(message)
            else:
                self.warnings.append(message)
                logger.warning(message)
        else:
            logger.info(f"{config['description']}: {value}{config['unit']} - OK (ISA {isa_req})")
        
        return valid
    
    def validate_all(self, metrics: Dict[str, float]) -> bool:
        """Valide toutes les métriques de sécurité."""
        all_valid = True
        
        for metric, config in SECURITY_THRESHOLDS.items():
            if metric in metrics:
                valid = self.validate_threshold(metric, metrics[metric], config)
                if not valid and config['critical']:
                    all_valid = False
            else:
                logger.warning(f"Métrique sécurité manquante: {metric}")
                # Considérer comme échec critique si métrique requise manquante
                if config['critical']:
                    self.failures.append(f"Métrique critique manquante: {config['description']}")
                    all_valid = False
        
        return all_valid
    
    def generate_isa_compliance_report(self) -> Dict[str, Any]:
        """Génère un rapport de conformité ISA/IEC 62443."""
        compliance_report = {
            'standard': 'ISA/IEC 62443',
            'security_levels': {},
            'overall_compliance': True
        }
        
        for level, stats in self.isa_compliance.items():
            compliance_percentage = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            compliance_report['security_levels'][level] = {
                'description': ISA_SECURITY_LEVELS.get(level, 'Unknown'),
                'requirements_total': stats['total'],
                'requirements_passed': stats['passed'],
                'compliance_percentage': compliance_percentage,
                'compliant': compliance_percentage == 100.0
            }
            
            if compliance_percentage < 100.0:
                compliance_report['overall_compliance'] = False
        
        return compliance_report
    
    def generate_report(self) -> Dict[str, Any]:
        """Génère un rapport complet de validation sécuritaire."""
        isa_compliance_report = self.generate_isa_compliance_report()
        
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'standard_compliance': isa_compliance_report,
            'total_metrics': len(self.results),
            'passed': sum(1 for r in self.results.values() if r['valid']),
            'failed': sum(1 for r in self.results.values() if not r['valid']),
            'critical_failures': len(self.failures),
            'warnings': len(self.warnings),
            'overall_status': 'PASS' if not self.failures else 'FAIL',
            'security_level_achieved': self.calculate_security_level(),
            'details': self.results,
            'failure_messages': self.failures,
            'warning_messages': self.warnings
        }
        
        return report
    
    def calculate_security_level(self) -> str:
        """Calcule le niveau de sécurité ISA/IEC 62443 atteint."""
        if not self.isa_compliance:
            return "Non évalué"
        
        # Détermine le niveau maximum atteint avec 100% de conformité
        max_level_achieved = "SL0"
        
        for level in ['SL1', 'SL2', 'SL3', 'SL4']:
            if level in self.isa_compliance:
                stats = self.isa_compliance[level]
                compliance = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                if compliance == 100.0:
                    max_level_achieved = level
        
        return max_level_achieved
    
    def save_report(self, report: Dict[str, Any], output_path: str):
        """Sauvegarde le rapport sécuritaire en JSON."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Rapport sécurité sauvegardé: {output_path}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde rapport sécurité: {e}")

def main():
    """Fonction principale de validation sécuritaire."""
    validator = SecurityValidator()
    
    # Chemins des fichiers
    security_report_file = "core/edge-ai-engine/models/security_summary.txt"
    output_report_file = "security-test-results.json"
    
    logger.info("🛡️ Démarrage validation seuils sécurité RNCP 39394")
    
    # Parse des résultats de sécurité
    metrics = validator.parse_security_report(security_report_file)
    
    if not metrics:
        logger.error("❌ Aucune métrique de sécurité trouvée")
        sys.exit(1)
    
    # Validation des seuils
    all_valid = validator.validate_all(metrics)
    
    # Génération du rapport
    report = validator.generate_report()
    validator.save_report(report, output_report_file)
    
    # Résumé des résultats
    print("\n" + "="*80)
    print("🛡️ RAPPORT DE VALIDATION SÉCURITÉ - RNCP 39394")
    print("="*80)
    print(f"Status global: {'✅ SUCCÈS' if report['overall_status'] == 'PASS' else '❌ ÉCHEC'}")
    print(f"Métriques validées: {report['passed']}/{report['total_metrics']}")
    print(f"Échecs critiques: {report['critical_failures']}")
    print(f"Avertissements: {report['warnings']}")
    print(f"Niveau sécurité ISA/IEC 62443: {report['security_level_achieved']}")
    
    # Détails conformité ISA
    print(f"\n📋 CONFORMITÉ ISA/IEC 62443:")
    for level, details in report['standard_compliance']['security_levels'].items():
        status = "✅" if details['compliant'] else "❌"
        print(f"  {status} {level}: {details['compliance_percentage']:.1f}% "
              f"({details['requirements_passed']}/{details['requirements_total']})")
    
    if report['failure_messages']:
        print(f"\n🚨 ÉCHECS CRITIQUES:")
        for failure in report['failure_messages']:
            print(f"  - {failure}")
    
    if report['warning_messages']:
        print(f"\n⚠️  AVERTISSEMENTS:")
        for warning in report['warning_messages']:
            print(f"  - {warning}")
    
    print(f"\n📄 Rapport détaillé: {output_report_file}")
    print("="*80)
    
    # Exit code pour CI/CD
    if all_valid:
        logger.info("✅ Tous les seuils de sécurité respectés")
        sys.exit(0)
    else:
        logger.error("❌ Seuils de sécurité non respectés")
        sys.exit(1)

if __name__ == "__main__":
    main()
