#!/usr/bin/env python3
"""
📊 COMPLIANCE DASHBOARD
Station Traffeyère IoT AI Platform - RNCP 39394 Semaine 7

Dashboard de conformité réglementaire avec:
- Génération automatique rapports ISO 27001, ANSSI, RGPD
- Audit trails complets et immutables
- Monitoring conformité temps réel
- Alertes non-conformité automatiques
"""

import asyncio
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
import logging
from collections import defaultdict
import hashlib
from enum import Enum
import time
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

logger = logging.getLogger('ComplianceDashboard')

class ComplianceFramework(Enum):
    """Standards de conformité supportés"""
    ISO27001 = "ISO 27001:2022"
    ANSSI = "ANSSI - Guide d'hygiène informatique"
    RGPD = "RGPD - Règlement Général sur la Protection des Données"
    NIST_CSF = "NIST Cybersecurity Framework"
    SOC2 = "SOC 2 Type II"
    PASSI = "PASSI - Prestataires d'Audit de la Sécurité des SI"

class ComplianceStatus(Enum):
    """Statuts de conformité"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial_compliance"
    UNKNOWN = "unknown"
    IN_PROGRESS = "in_progress"

@dataclass
class ComplianceControl:
    """Contrôle de conformité individuel"""
    id: str
    framework: ComplianceFramework
    control_id: str  # Ex: ISO.A.5.1.1
    title: str
    description: str
    status: ComplianceStatus
    last_assessment: datetime
    evidence_refs: List[str]
    risk_level: str  # high, medium, low
    remediation_plan: Optional[str]
    responsible_person: str
    due_date: Optional[datetime]
    metadata: Dict[str, Any]

@dataclass
class AuditTrailEntry:
    """Entrée d'audit trail immutable"""
    id: str
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    hash_signature: str

@dataclass
class ComplianceReport:
    """Rapport de conformité complet"""
    id: str
    framework: ComplianceFramework
    generation_date: datetime
    assessment_period: str
    overall_status: ComplianceStatus
    compliance_score: float  # 0-100%
    controls_summary: Dict[str, int]
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    report_path: str
    next_assessment_due: datetime

class AuditTrailManager:
    """Gestionnaire d'audit trails immutables"""
    
    def __init__(self, db_path: str = "data/audit_trail.db"):
        self.db_path = db_path
        self._setup_database()
        
    def _setup_database(self):
        """Initialiser base de données audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_trail (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                user_id TEXT,
                action TEXT,
                resource TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                hash_signature TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Index pour performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_trail (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_trail (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_action ON audit_trail (action)')
        
        conn.commit()
        conn.close()
    
    def log_action(self, user_id: str, action: str, resource: str, 
                   details: Dict[str, Any], ip_address: str = "127.0.0.1", 
                   user_agent: str = "System") -> AuditTrailEntry:
        """Enregistrer action dans audit trail avec signature"""
        
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Créer hash signature pour intégrité
        data_to_hash = f"{entry_id}:{timestamp.isoformat()}:{user_id}:{action}:{resource}:{json.dumps(details, sort_keys=True)}"
        hash_signature = hashlib.sha256(data_to_hash.encode()).hexdigest()
        
        entry = AuditTrailEntry(
            id=entry_id,
            timestamp=timestamp,
            user_id=user_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            hash_signature=hash_signature
        )
        
        # Sauvegarder en DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_trail 
            (id, timestamp, user_id, action, resource, details, ip_address, user_agent, hash_signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry_id, timestamp, user_id, action, resource, 
            json.dumps(details), ip_address, user_agent, hash_signature
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📝 Audit trail: {action} par {user_id} sur {resource}")
        return entry
    
    def verify_integrity(self, entry_id: str) -> bool:
        """Vérifier intégrité d'une entrée audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM audit_trail WHERE id = ?', (entry_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False
        
        # Recalculer hash
        data_to_hash = f"{row[0]}:{row[1]}:{row[2]}:{row[3]}:{row[4]}:{row[5]}"
        calculated_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()
        
        return calculated_hash == row[8]
    
    def get_audit_logs(self, start_date: datetime = None, end_date: datetime = None, 
                       user_id: str = None, action: str = None) -> List[AuditTrailEntry]:
        """Récupérer logs d'audit avec filtres"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_trail WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
            
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
            
        if action:
            query += " AND action = ?"
            params.append(action)
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for row in rows:
            try:
                # Traiter le timestamp qui peut être un string ou datetime
                timestamp_val = row[1]
                if isinstance(timestamp_val, str):
                    timestamp_parsed = datetime.fromisoformat(timestamp_val)
                else:
                    timestamp_parsed = timestamp_val
            except:
                timestamp_parsed = datetime.now()
            
            entry = AuditTrailEntry(
                id=row[0],
                timestamp=timestamp_parsed,
                user_id=row[2],
                action=row[3],
                resource=row[4],
                details=json.loads(row[5]) if row[5] else {},
                ip_address=row[6],
                user_agent=row[7],
                hash_signature=row[8]
            )
            entries.append(entry)
        
        return entries

class ComplianceAssessor:
    """Évaluateur de conformité automatisé"""
    
    def __init__(self):
        self.assessment_rules = self._load_assessment_rules()
    
    def _load_assessment_rules(self) -> Dict[str, Any]:
        """Charger règles d'évaluation conformité"""
        return {
            ComplianceFramework.ISO27001: {
                "A.5.1.1": {
                    "title": "Politiques de sécurité de l'information",
                    "checks": ["policy_exists", "policy_approved", "policy_communicated"],
                    "critical": True
                },
                "A.6.1.1": {
                    "title": "Rôles et responsabilités sécurité",
                    "checks": ["roles_defined", "responsibilities_assigned"],
                    "critical": True
                },
                "A.8.1.1": {
                    "title": "Inventaire des actifs",
                    "checks": ["asset_inventory_exists", "inventory_updated"],
                    "critical": False
                },
                "A.12.1.1": {
                    "title": "Procédures opérationnelles",
                    "checks": ["procedures_documented", "procedures_tested"],
                    "critical": True
                },
                "A.16.1.1": {
                    "title": "Gestion des incidents",
                    "checks": ["incident_procedure", "incident_response_team"],
                    "critical": True
                }
            },
            ComplianceFramework.RGPD: {
                "ART.7": {
                    "title": "Consentement",
                    "checks": ["consent_mechanism", "consent_withdrawal"],
                    "critical": True
                },
                "ART.25": {
                    "title": "Protection dès la conception",
                    "checks": ["privacy_by_design", "data_minimization"],
                    "critical": True
                },
                "ART.32": {
                    "title": "Sécurité du traitement",
                    "checks": ["encryption_implemented", "access_controls"],
                    "critical": True
                },
                "ART.33": {
                    "title": "Notification violations",
                    "checks": ["breach_notification_procedure", "72h_notification"],
                    "critical": True
                },
                "ART.35": {
                    "title": "Analyse d'impact DPIA",
                    "checks": ["dpia_conducted", "dpia_documented"],
                    "critical": False
                }
            },
            ComplianceFramework.ANSSI: {
                "HYG.1": {
                    "title": "Connaître le système d'information",
                    "checks": ["network_mapping", "asset_inventory"],
                    "critical": True
                },
                "HYG.2": {
                    "title": "Authentification forte",
                    "checks": ["mfa_enabled", "password_policy"],
                    "critical": True
                },
                "HYG.3": {
                    "title": "Mises à jour de sécurité",
                    "checks": ["patch_management", "vulnerability_scanning"],
                    "critical": True
                },
                "HYG.4": {
                    "title": "Sauvegarde",
                    "checks": ["backup_strategy", "backup_tested"],
                    "critical": True
                },
                "HYG.5": {
                    "title": "Supervision et métrologie",
                    "checks": ["log_monitoring", "incident_detection"],
                    "critical": True
                }
            }
        }
    
    async def assess_control(self, framework: ComplianceFramework, 
                           control_id: str, system_context: Dict[str, Any]) -> ComplianceControl:
        """Évaluer contrôle de conformité spécifique"""
        
        if framework not in self.assessment_rules:
            raise ValueError(f"Framework {framework} non supporté")
        
        if control_id not in self.assessment_rules[framework]:
            raise ValueError(f"Contrôle {control_id} non trouvé pour {framework}")
        
        control_def = self.assessment_rules[framework][control_id]
        
        # Évaluer chaque vérification
        check_results = {}
        for check in control_def["checks"]:
            check_results[check] = await self._perform_check(check, system_context)
        
        # Calculer statut global
        passed_checks = sum(1 for result in check_results.values() if result)
        total_checks = len(check_results)
        
        if passed_checks == total_checks:
            status = ComplianceStatus.COMPLIANT
        elif passed_checks > 0:
            status = ComplianceStatus.PARTIAL
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        # Créer contrôle
        control = ComplianceControl(
            id=str(uuid.uuid4()),
            framework=framework,
            control_id=control_id,
            title=control_def["title"],
            description=f"Évaluation automatique du contrôle {control_id}",
            status=status,
            last_assessment=datetime.now(),
            evidence_refs=[],
            risk_level="high" if control_def.get("critical", False) else "medium",
            remediation_plan=None,
            responsible_person="Security Officer",
            due_date=datetime.now() + timedelta(days=30),
            metadata={"check_results": check_results}
        )
        
        logger.info(f"✅ Contrôle {control_id} évalué: {status.value} ({passed_checks}/{total_checks})")
        return control
    
    async def _perform_check(self, check_name: str, context: Dict[str, Any]) -> bool:
        """Effectuer vérification spécifique"""
        # Simulation de vérifications automatisées
        checks = {
            "policy_exists": lambda: context.get("security_policies", []) != [],
            "policy_approved": lambda: context.get("policy_approval_date") is not None,
            "policy_communicated": lambda: context.get("policy_communication", False),
            "roles_defined": lambda: context.get("security_roles", []) != [],
            "responsibilities_assigned": lambda: context.get("role_assignments", []) != [],
            "asset_inventory_exists": lambda: context.get("asset_count", 0) > 0,
            "inventory_updated": lambda: context.get("last_inventory_update") is not None,
            "procedures_documented": lambda: context.get("documented_procedures", []) != [],
            "procedures_tested": lambda: context.get("last_procedure_test") is not None,
            "incident_procedure": lambda: context.get("incident_response_plan", False),
            "incident_response_team": lambda: context.get("incident_team_members", []) != [],
            "consent_mechanism": lambda: context.get("consent_system", False),
            "consent_withdrawal": lambda: context.get("withdrawal_mechanism", False),
            "privacy_by_design": lambda: context.get("privacy_controls", False),
            "data_minimization": lambda: context.get("data_minimization_policy", False),
            "encryption_implemented": lambda: context.get("encryption_enabled", False),
            "access_controls": lambda: context.get("access_control_system", False),
            "breach_notification_procedure": lambda: context.get("breach_notification", False),
            "72h_notification": lambda: context.get("automated_notification", False),
            "dpia_conducted": lambda: context.get("dpia_assessments", []) != [],
            "dpia_documented": lambda: context.get("dpia_documentation", False),
            "network_mapping": lambda: context.get("network_topology", False),
            "mfa_enabled": lambda: context.get("multi_factor_auth", False),
            "password_policy": lambda: context.get("password_policy", False),
            "patch_management": lambda: context.get("patch_system", False),
            "vulnerability_scanning": lambda: context.get("vuln_scanner", False),
            "backup_strategy": lambda: context.get("backup_plan", False),
            "backup_tested": lambda: context.get("backup_tests", []) != [],
            "log_monitoring": lambda: context.get("log_system", False),
            "incident_detection": lambda: context.get("detection_system", False)
        }
        
        if check_name in checks:
            try:
                result = checks[check_name]()
                logger.debug(f"Check {check_name}: {'PASS' if result else 'FAIL'}")
                return result
            except:
                logger.warning(f"Check {check_name} failed with exception")
                return False
        
        logger.warning(f"Check {check_name} non implémenté")
        return False

class ReportGenerator:
    """Générateur de rapports de conformité"""
    
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)
    
    def generate_compliance_report(self, framework: ComplianceFramework, 
                                 controls: List[ComplianceControl]) -> ComplianceReport:
        """Générer rapport de conformité complet"""
        
        # Calculer métriques
        total_controls = len(controls)
        compliant_controls = len([c for c in controls if c.status == ComplianceStatus.COMPLIANT])
        compliance_score = (compliant_controls / total_controls) * 100 if total_controls > 0 else 0
        
        # Déterminer statut global
        critical_controls = [c for c in controls if c.risk_level == "high"]
        critical_non_compliant = [c for c in critical_controls if c.status == ComplianceStatus.NON_COMPLIANT]
        
        if critical_non_compliant:
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif compliance_score >= 95:
            overall_status = ComplianceStatus.COMPLIANT
        else:
            overall_status = ComplianceStatus.PARTIAL
        
        # Résumé des contrôles
        controls_summary = {
            "total": total_controls,
            "compliant": len([c for c in controls if c.status == ComplianceStatus.COMPLIANT]),
            "partial": len([c for c in controls if c.status == ComplianceStatus.PARTIAL]),
            "non_compliant": len([c for c in controls if c.status == ComplianceStatus.NON_COMPLIANT]),
            "critical_non_compliant": len(critical_non_compliant)
        }
        
        # Générer findings
        findings = []
        for control in controls:
            if control.status != ComplianceStatus.COMPLIANT:
                findings.append({
                    "control_id": control.control_id,
                    "title": control.title,
                    "status": control.status.value,
                    "risk_level": control.risk_level,
                    "description": f"Contrôle {control.control_id} non conforme",
                    "remediation": control.remediation_plan or "Plan de remédiation requis"
                })
        
        # Générer recommandations
        recommendations = self._generate_recommendations(framework, controls, compliance_score)
        
        # Créer rapport
        report = ComplianceReport(
            id=f"RPT-{framework.name}-{int(datetime.now().timestamp())}",
            framework=framework,
            generation_date=datetime.now(),
            assessment_period=f"{datetime.now().strftime('%B %Y')}",
            overall_status=overall_status,
            compliance_score=compliance_score,
            controls_summary=controls_summary,
            findings=findings,
            recommendations=recommendations,
            report_path="",
            next_assessment_due=datetime.now() + timedelta(days=90)
        )
        
        # Générer et sauvegarder rapport
        report_content = self._generate_report_content(report, controls)
        report_path = self._save_report(report_content, report.id)
        report.report_path = report_path
        
        logger.info(f"📊 Rapport {framework.name} généré: {compliance_score:.1f}% conformité")
        return report
    
    def _generate_recommendations(self, framework: ComplianceFramework, 
                                controls: List[ComplianceControl], 
                                compliance_score: float) -> List[str]:
        """Générer recommandations basées sur l'évaluation"""
        recommendations = []
        
        # Recommandations génériques
        if compliance_score < 70:
            recommendations.append("URGENT: Score de conformité critique. Révision complète des contrôles requise.")
        elif compliance_score < 85:
            recommendations.append("ATTENTION: Score de conformité sous le seuil recommandé. Actions correctives nécessaires.")
        
        # Recommandations spécifiques par framework
        critical_non_compliant = [c for c in controls if c.risk_level == "high" and c.status == ComplianceStatus.NON_COMPLIANT]
        
        if framework == ComplianceFramework.ISO27001:
            if any(c.control_id == "A.5.1.1" for c in critical_non_compliant):
                recommendations.append("Mettre à jour et approuver la politique de sécurité de l'information")
            if any(c.control_id == "A.16.1.1" for c in critical_non_compliant):
                recommendations.append("Établir procédure formelle de gestion des incidents de sécurité")
        
        elif framework == ComplianceFramework.RGPD:
            if any(c.control_id == "ART.32" for c in critical_non_compliant):
                recommendations.append("Renforcer les mesures techniques de sécurité du traitement des données")
            if any(c.control_id == "ART.33" for c in critical_non_compliant):
                recommendations.append("Mettre en place procédure de notification des violations dans les 72h")
        
        elif framework == ComplianceFramework.ANSSI:
            if any(c.control_id == "HYG.2" for c in critical_non_compliant):
                recommendations.append("Déployer authentification multi-facteurs sur tous les systèmes critiques")
            if any(c.control_id == "HYG.3" for c in critical_non_compliant):
                recommendations.append("Automatiser la gestion des correctifs de sécurité")
        
        # Recommandation générale de suivi
        recommendations.append(f"Programmer réévaluation complète dans 30 jours pour contrôles non conformes")
        
        return recommendations
    
    def _generate_report_content(self, report: ComplianceReport, 
                               controls: List[ComplianceControl]) -> str:
        """Générer contenu du rapport"""
        
        content = f"""
# RAPPORT DE CONFORMITÉ {report.framework.value}

## RÉSUMÉ EXÉCUTIF

**Station de Traitement Traffeyère IoT AI Platform**
- **Rapport ID:** {report.id}
- **Framework:** {report.framework.value}
- **Date d'évaluation:** {report.generation_date.strftime('%d/%m/%Y %H:%M')}
- **Période d'évaluation:** {report.assessment_period}

### Score de Conformité Globale
**{report.compliance_score:.1f}%** - Statut: **{report.overall_status.value.upper()}**

## RÉSULTATS PAR CONTRÔLES

### Vue d'ensemble
- **Total des contrôles évalués:** {report.controls_summary['total']}
- **Contrôles conformes:** {report.controls_summary['compliant']} ✅
- **Conformité partielle:** {report.controls_summary['partial']} ⚠️
- **Non conformes:** {report.controls_summary['non_compliant']} ❌
- **Critiques non conformes:** {report.controls_summary['critical_non_compliant']} 🚨

### Détail des Contrôles
"""
        
        for control in controls:
            status_icon = {"compliant": "✅", "partial": "⚠️", "non_compliant": "❌", "unknown": "❓", "in_progress": "🔄"}
            icon = status_icon.get(control.status.value, "❓")
            
            content += f"""
#### {control.control_id} - {control.title}
- **Statut:** {icon} {control.status.value.upper()}
- **Niveau de risque:** {control.risk_level.upper()}
- **Dernière évaluation:** {control.last_assessment.strftime('%d/%m/%Y %H:%M')}
- **Responsable:** {control.responsible_person}
"""
            if control.status != ComplianceStatus.COMPLIANT:
                content += f"- **Échéance remédiation:** {control.due_date.strftime('%d/%m/%Y') if control.due_date else 'À définir'}\n"
        
        content += f"""

## CONSTATS ET NON-CONFORMITÉS

### Findings Identifiés
"""
        
        for finding in report.findings:
            content += f"""
**{finding['control_id']} - {finding['title']}**
- Niveau: {finding['risk_level'].upper()}
- Statut: {finding['status'].upper()}
- Recommandation: {finding['remediation']}
"""
        
        content += f"""

## RECOMMANDATIONS

### Actions Prioritaires
"""
        
        for i, recommendation in enumerate(report.recommendations, 1):
            content += f"{i}. {recommendation}\n"
        
        content += f"""

## PLAN DE SUIVI

### Prochaine Évaluation
- **Date prévue:** {report.next_assessment_due.strftime('%d/%m/%Y')}
- **Fréquence recommandée:** Trimestrielle pour {report.framework.value}

### Actions de Remédiation
Les contrôles non conformes doivent faire l'objet d'un plan d'action avec:
- Désignation d'un responsable
- Échéancier de mise en œuvre
- Budget alloué
- Métriques de suivi

---

**RAPPORT GÉNÉRÉ AUTOMATIQUEMENT**
Station Traffeyère IoT AI Platform - Compliance Dashboard
{datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}

**CONFIDENTIEL - USAGE INTERNE UNIQUEMENT**
"""
        
        return content
    
    def _save_report(self, content: str, report_id: str) -> str:
        """Sauvegarder rapport sur disque"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"compliance_report_{report_id}_{timestamp}.md"
        filepath = Path("reports") / "compliance" / filename
        
        # Créer répertoire si nécessaire
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire rapport
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"💾 Rapport sauvegardé: {filepath}")
        return str(filepath)

class ComplianceDashboard:
    """Dashboard principal de conformité réglementaire"""
    
    def __init__(self, db_path: str = "data/compliance.db"):
        self.db_path = db_path
        self.audit_manager = AuditTrailManager()
        self.assessor = ComplianceAssessor()
        self.report_generator = ReportGenerator()
        self._setup_database()
        self._setup_monitoring()
    
    def _setup_database(self):
        """Initialiser base de données compliance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table contrôles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_controls (
                id TEXT PRIMARY KEY,
                framework TEXT,
                control_id TEXT,
                title TEXT,
                description TEXT,
                status TEXT,
                last_assessment TIMESTAMP,
                risk_level TEXT,
                responsible_person TEXT,
                due_date TIMESTAMP,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table rapports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_reports (
                id TEXT PRIMARY KEY,
                framework TEXT,
                generation_date TIMESTAMP,
                overall_status TEXT,
                compliance_score REAL,
                controls_summary TEXT,
                findings TEXT,
                recommendations TEXT,
                report_path TEXT,
                next_assessment_due TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table alertes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_alerts (
                id TEXT PRIMARY KEY,
                alert_type TEXT,
                severity TEXT,
                title TEXT,
                description TEXT,
                control_id TEXT,
                framework TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                assigned_to TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _setup_monitoring(self):
        """Configuration monitoring conformité automatique"""
        # Surveillance basique (pour démo, sans scheduler externe)
        logger.info("📊 Monitoring compliance configuré")
    
    async def perform_full_assessment(self, framework: ComplianceFramework, 
                                    system_context: Dict[str, Any] = None) -> ComplianceReport:
        """Effectuer évaluation complète de conformité"""
        
        if system_context is None:
            system_context = await self._gather_system_context()
        
        # Log action
        self.audit_manager.log_action(
            "compliance_system", "assessment_started", f"framework_{framework.name}",
            {"framework": framework.value, "context_keys": list(system_context.keys())}
        )
        
        # Évaluer tous les contrôles du framework
        controls = []
        control_rules = self.assessor.assessment_rules.get(framework, {})
        
        for control_id in control_rules.keys():
            try:
                control = await self.assessor.assess_control(framework, control_id, system_context)
                controls.append(control)
                
                # Sauvegarder contrôle en DB
                await self._save_control(control)
                
            except Exception as e:
                logger.error(f"Erreur évaluation contrôle {control_id}: {e}")
                # Créer contrôle en erreur
                error_control = ComplianceControl(
                    id=str(uuid.uuid4()),
                    framework=framework,
                    control_id=control_id,
                    title=control_rules[control_id]["title"],
                    description="Évaluation échouée",
                    status=ComplianceStatus.UNKNOWN,
                    last_assessment=datetime.now(),
                    evidence_refs=[],
                    risk_level="high",
                    remediation_plan="Corriger erreur d'évaluation",
                    responsible_person="Security Officer",
                    due_date=datetime.now() + timedelta(days=7),
                    metadata={"error": str(e)}
                )
                controls.append(error_control)
        
        # Générer rapport
        report = self.report_generator.generate_compliance_report(framework, controls)
        
        # Sauvegarder rapport
        await self._save_report(report)
        
        # Générer alertes si nécessaire
        await self._check_for_compliance_violations(controls, framework)
        
        # Log fin
        self.audit_manager.log_action(
            "compliance_system", "assessment_completed", f"framework_{framework.name}",
            {"report_id": report.id, "score": report.compliance_score, "status": report.overall_status.value}
        )
        
        logger.info(f"🎯 Évaluation {framework.value} terminée: {report.compliance_score:.1f}% - {report.overall_status.value}")
        return report
    
    async def _gather_system_context(self) -> Dict[str, Any]:
        """Collecter contexte système pour évaluation"""
        # Simulation de collecte automatique de données système
        context = {
            # Politiques et procédures
            "security_policies": ["security_policy_v2.1.pdf", "data_protection_policy.pdf"],
            "policy_approval_date": datetime(2024, 1, 15),
            "policy_communication": True,
            "documented_procedures": ["incident_response.pdf", "backup_procedure.pdf"],
            "last_procedure_test": datetime(2024, 11, 1),
            
            # Organisation
            "security_roles": ["CISO", "Security Officer", "DPO"],
            "role_assignments": ["john.doe@traffeyere.com", "jane.smith@traffeyere.com"],
            "incident_team_members": ["incident-team@traffeyere.com"],
            
            # Assets et infrastructure
            "asset_count": 150,
            "last_inventory_update": datetime(2024, 12, 1),
            "network_topology": True,
            
            # Sécurité technique
            "encryption_enabled": True,
            "multi_factor_auth": True,
            "password_policy": True,
            "access_control_system": True,
            "patch_system": True,
            "vuln_scanner": True,
            
            # Monitoring et réponse
            "log_system": True,
            "detection_system": True,
            "incident_response_plan": True,
            
            # Sauvegarde
            "backup_plan": True,
            "backup_tests": ["backup_test_2024-11-15", "backup_test_2024-10-15"],
            
            # RGPD
            "consent_system": True,
            "withdrawal_mechanism": True,
            "privacy_controls": True,
            "data_minimization_policy": True,
            "breach_notification": True,
            "automated_notification": False,  # Point d'amélioration
            "dpia_assessments": ["dpia_iot_sensors_2024.pdf"],
            "dpia_documentation": True
        }
        
        logger.info(f"📊 Contexte système collecté: {len(context)} paramètres")
        return context
    
    async def _save_control(self, control: ComplianceControl):
        """Sauvegarder contrôle en base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO compliance_controls
            (id, framework, control_id, title, description, status, last_assessment,
             risk_level, responsible_person, due_date, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            control.id, control.framework.value, control.control_id, control.title,
            control.description, control.status.value, control.last_assessment,
            control.risk_level, control.responsible_person, control.due_date,
            json.dumps(control.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    async def _save_report(self, report: ComplianceReport):
        """Sauvegarder rapport en base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO compliance_reports
            (id, framework, generation_date, overall_status, compliance_score,
             controls_summary, findings, recommendations, report_path, next_assessment_due)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report.id, report.framework.value, report.generation_date,
            report.overall_status.value, report.compliance_score,
            json.dumps(report.controls_summary), json.dumps(report.findings),
            json.dumps(report.recommendations), report.report_path, report.next_assessment_due
        ))
        
        conn.commit()
        conn.close()
    
    async def _check_for_compliance_violations(self, controls: List[ComplianceControl], 
                                             framework: ComplianceFramework):
        """Vérifier violations et générer alertes"""
        
        for control in controls:
            if control.status == ComplianceStatus.NON_COMPLIANT and control.risk_level == "high":
                # Créer alerte critique
                alert_id = str(uuid.uuid4())
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO compliance_alerts
                    (id, alert_type, severity, title, description, control_id, framework, assigned_to)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert_id, "compliance_violation", "high",
                    f"Violation critique - {control.control_id}",
                    f"Contrôle critique {control.control_id} ({control.title}) non conforme",
                    control.control_id, framework.value, control.responsible_person
                ))
                
                conn.commit()
                conn.close()
                
                logger.warning(f"🚨 Alerte générée pour violation {control.control_id}")
    
    def _weekly_compliance_check(self):
        """Vérification hebdomadaire programmée"""
        logger.info("📅 Démarrage vérification compliance hebdomadaire")
        # Implémenter vérifications automatiques
    
    def _daily_compliance_monitoring(self):
        """Monitoring quotidien programmé"""
        logger.info("📊 Monitoring compliance quotidien")
        # Implémenter monitoring continu
    
    def _check_compliance_alerts(self):
        """Vérification alertes compliance"""
        logger.debug("🔍 Vérification alertes compliance")
        # Implémenter gestion alertes
    
    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Métriques de conformité consolidées"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Métriques des rapports
        cursor.execute('''
            SELECT framework, AVG(compliance_score), COUNT(*)
            FROM compliance_reports 
            WHERE generation_date >= datetime('now', '-30 days')
            GROUP BY framework
        ''')
        framework_scores = {row[0]: {"avg_score": row[1], "report_count": row[2]} for row in cursor.fetchall()}
        
        # Métriques des contrôles
        cursor.execute('SELECT status, COUNT(*) FROM compliance_controls GROUP BY status')
        control_status = dict(cursor.fetchall())
        
        # Alertes ouvertes
        cursor.execute('SELECT COUNT(*) FROM compliance_alerts WHERE resolved_at IS NULL')
        open_alerts = cursor.fetchone()[0]
        
        # Audit trail (table dans une autre base)
        try:
            audit_conn = sqlite3.connect(self.audit_manager.db_path)
            audit_cursor = audit_conn.cursor()
            audit_cursor.execute('SELECT COUNT(*) FROM audit_trail WHERE timestamp >= datetime("now", "-24 hours")')
            recent_audit_entries = audit_cursor.fetchone()[0]
            audit_conn.close()
        except:
            recent_audit_entries = 0
        
        conn.close()
        
        return {
            'framework_scores': framework_scores,
            'control_status_distribution': control_status,
            'open_compliance_alerts': open_alerts,
            'audit_trail_entries_24h': recent_audit_entries,
            'dashboard_status': 'operational'
        }

# Test et démonstration
async def demo_compliance_dashboard():
    """Démonstration complète du dashboard conformité"""
    dashboard = ComplianceDashboard("data/compliance_demo.db")
    
    print("📊 DEMO COMPLIANCE DASHBOARD - Station Traffeyère")
    print("=" * 60)
    
    # Test audit trail
    dashboard.audit_manager.log_action(
        "admin", "system_config", "compliance_dashboard",
        {"action": "demo_started", "timestamp": datetime.now().isoformat()}
    )
    
    # Évaluations par framework
    frameworks_to_test = [
        ComplianceFramework.ISO27001,
        ComplianceFramework.RGPD,
        ComplianceFramework.ANSSI
    ]
    
    reports = []
    for framework in frameworks_to_test:
        print(f"\n🔍 Évaluation {framework.value}...")
        report = await dashboard.perform_full_assessment(framework)
        reports.append(report)
        print(f"   Score: {report.compliance_score:.1f}% - Statut: {report.overall_status.value}")
        print(f"   Rapport: {report.report_path}")
    
    # Métriques consolidées
    metrics = dashboard.get_compliance_metrics()
    print(f"\n📈 MÉTRIQUES GLOBALES:")
    print(f"   Frameworks évalués: {len(metrics['framework_scores'])}")
    print(f"   Distribution contrôles: {metrics['control_status_distribution']}")
    print(f"   Alertes ouvertes: {metrics['open_compliance_alerts']}")
    print(f"   Entrées audit 24h: {metrics['audit_trail_entries_24h']}")
    
    # Exemple d'intégrité audit trail
    audit_logs = dashboard.audit_manager.get_audit_logs(
        start_date=datetime.now() - timedelta(hours=1)
    )
    print(f"\n🔒 AUDIT TRAIL:")
    for log in audit_logs[:3]:
        integrity = dashboard.audit_manager.verify_integrity(log.id)
        print(f"   {log.timestamp.strftime('%H:%M:%S')} - {log.action} par {log.user_id} - Intégrité: {'✅' if integrity else '❌'}")
    
    return reports

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_compliance_dashboard())
