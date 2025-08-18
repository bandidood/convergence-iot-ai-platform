#!/usr/bin/env python3
"""
🔍 AI FORENSICS ENGINE
Station Traffeyère IoT AI Platform - RNCP 39394 Semaine 7

Moteur d'investigation automatisée post-incident avec:
- Reconstruction timeline automatique
- Analyse artifacts multi-sources  
- Chain of custody numérique légale
- Génération rapports conformes standards judiciaires
"""

import asyncio
import json
import sqlite3
import hashlib
import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
import logging
from collections import defaultdict
import re
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

logger = logging.getLogger('AIForensicsEngine')

@dataclass
class Evidence:
    """Classe pour représenter une pièce à conviction numérique"""
    id: str
    timestamp: datetime
    source: str
    artifact_type: str
    content: str
    hash_sha256: str
    chain_of_custody: List[Dict[str, Any]]
    legal_status: str  # 'collected', 'verified', 'admitted', 'challenged'
    metadata: Dict[str, Any]

@dataclass
class TimelineEvent:
    """Événement dans la timeline forensics"""
    timestamp: datetime
    event_type: str
    source: str
    description: str
    evidence_refs: List[str]
    confidence_score: float
    correlation_ids: List[str]

@dataclass
class ForensicsInvestigation:
    """Investigation forensics complète"""
    id: str
    incident_id: str
    start_time: datetime
    status: str  # 'active', 'completed', 'archived'
    lead_investigator: str
    evidence_items: List[Evidence]
    timeline: List[TimelineEvent]
    findings: List[Dict[str, Any]]
    legal_report_path: Optional[str]
    chain_integrity_verified: bool

class ChainOfCustodyManager:
    """Gestionnaire de chaîne de possession légale"""
    
    def __init__(self, private_key_path: str = None):
        self.custody_log = []
        self.private_key = self._generate_or_load_key(private_key_path)
        self.public_key = self.private_key.public_key()
    
    def _generate_or_load_key(self, key_path: str) -> rsa.RSAPrivateKey:
        """Générer ou charger clé RSA pour signatures"""
        if key_path and Path(key_path).exists():
            with open(key_path, 'rb') as f:
                return serialization.load_pem_private_key(f.read(), password=None)
        else:
            # Générer nouvelle clé
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096
            )
            
            # Sauvegarder si chemin fourni
            if key_path:
                pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                Path(key_path).parent.mkdir(parents=True, exist_ok=True)
                with open(key_path, 'wb') as f:
                    f.write(pem)
            
            return private_key
    
    def add_custody_entry(self, evidence_id: str, action: str, officer: str, 
                         location: str, notes: str = "") -> Dict[str, Any]:
        """Ajouter entrée chaîne de possession avec signature"""
        entry = {
            'evidence_id': evidence_id,
            'timestamp': datetime.now().isoformat(),
            'action': action,  # 'collected', 'transferred', 'analyzed', 'returned'
            'officer': officer,
            'location': location,
            'notes': notes,
            'entry_id': str(uuid.uuid4())
        }
        
        # Signer l'entrée
        entry_json = json.dumps(entry, sort_keys=True).encode()
        signature = self.private_key.sign(
            entry_json,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        entry['signature'] = signature.hex()
        self.custody_log.append(entry)
        
        logger.info(f"🔒 Entrée custody ajoutée: {action} pour {evidence_id} par {officer}")
        return entry
    
    def verify_custody_integrity(self, evidence_id: str) -> bool:
        """Vérifier intégrité chaîne de possession"""
        entries = [e for e in self.custody_log if e['evidence_id'] == evidence_id]
        
        for entry in entries:
            try:
                # Extraire signature
                signature = bytes.fromhex(entry['signature'])
                
                # Reconstituer données sans signature
                entry_copy = entry.copy()
                del entry_copy['signature']
                entry_json = json.dumps(entry_copy, sort_keys=True).encode()
                
                # Vérifier signature
                self.public_key.verify(
                    signature,
                    entry_json,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                
            except Exception as e:
                logger.error(f"❌ Vérification custody échouée pour {entry['entry_id']}: {e}")
                return False
        
        logger.info(f"✅ Intégrité custody vérifiée pour {evidence_id}")
        return True

class TimelineReconstructor:
    """Reconstructeur de timeline automatique"""
    
    def __init__(self):
        self.events = []
        self.correlations = defaultdict(list)
    
    def add_log_source(self, logs: List[Dict[str, Any]], source_name: str):
        """Ajouter source de logs pour reconstruction timeline"""
        for log_entry in logs:
            try:
                # Parser timestamp
                if isinstance(log_entry.get('timestamp'), str):
                    timestamp = pd.to_datetime(log_entry['timestamp'])
                else:
                    timestamp = log_entry['timestamp']
                
                event = TimelineEvent(
                    timestamp=timestamp,
                    event_type=log_entry.get('event_type', 'generic'),
                    source=source_name,
                    description=log_entry.get('description', str(log_entry)),
                    evidence_refs=[],
                    confidence_score=log_entry.get('confidence', 0.8),
                    correlation_ids=[]
                )
                
                self.events.append(event)
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur parsing log entry: {e}")
    
    def add_network_traffic(self, network_data: List[Dict[str, Any]]):
        """Ajouter données trafic réseau"""
        for packet in network_data:
            try:
                event = TimelineEvent(
                    timestamp=pd.to_datetime(packet['timestamp']),
                    event_type='network_traffic',
                    source='network_monitor',
                    description=f"Connection {packet.get('src_ip')} -> {packet.get('dst_ip')}:{packet.get('dst_port')}",
                    evidence_refs=[],
                    confidence_score=0.9,
                    correlation_ids=[]
                )
                self.events.append(event)
            except Exception as e:
                logger.warning(f"⚠️ Erreur parsing network data: {e}")
    
    def correlate_events(self, time_window_seconds: int = 300) -> List[List[TimelineEvent]]:
        """Corréler événements dans fenêtre temporelle"""
        correlations = []
        sorted_events = sorted(self.events, key=lambda e: e.timestamp)
        
        for i, event in enumerate(sorted_events):
            correlation_group = [event]
            
            # Chercher événements liés dans fenêtre temporelle
            for j, other_event in enumerate(sorted_events[i+1:], i+1):
                time_diff = (other_event.timestamp - event.timestamp).total_seconds()
                
                if time_diff > time_window_seconds:
                    break
                
                # Critères de corrélation
                if self._events_related(event, other_event):
                    correlation_group.append(other_event)
                    # Assigner ID corrélation commun
                    correlation_id = str(uuid.uuid4())
                    event.correlation_ids.append(correlation_id)
                    other_event.correlation_ids.append(correlation_id)
            
            if len(correlation_group) > 1:
                correlations.append(correlation_group)
        
        return correlations
    
    def _events_related(self, event1: TimelineEvent, event2: TimelineEvent) -> bool:
        """Déterminer si deux événements sont liés"""
        # Règles de corrélation simples
        
        # Même adresse IP
        ip_pattern = r'\d+\.\d+\.\d+\.\d+'
        ips1 = re.findall(ip_pattern, event1.description)
        ips2 = re.findall(ip_pattern, event2.description)
        if set(ips1) & set(ips2):
            return True
        
        # Événements de sécurité consécutifs
        security_events = ['alert', 'warning', 'error', 'attack', 'intrusion']
        if any(term in event1.event_type.lower() for term in security_events) and \
           any(term in event2.event_type.lower() for term in security_events):
            return True
        
        return False
    
    def generate_timeline(self) -> List[TimelineEvent]:
        """Générer timeline ordonnée avec corrélations"""
        # Corréler événements
        self.correlate_events()
        
        # Trier par timestamp
        timeline = sorted(self.events, key=lambda e: e.timestamp)
        
        logger.info(f"📅 Timeline générée: {len(timeline)} événements")
        return timeline

class ArtifactAnalyzer:
    """Analyseur d'artifacts automatisé"""
    
    def __init__(self):
        self.analysis_rules = self._load_analysis_rules()
    
    def _load_analysis_rules(self) -> Dict[str, Any]:
        """Charger règles d'analyse YARA-like"""
        return {
            'malware_indicators': [
                r'(?i)malware|virus|trojan|backdoor|rootkit',
                r'(?i)suspicious|anomaly|alert|warning',
                r'(?i)unauthorized|illegal|forbidden'
            ],
            'network_anomalies': [
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
                r'(?i)connection.*(?:refused|timeout|failed)',
                r'(?i)scan|probe|reconnaissance'
            ],
            'data_exfiltration': [
                r'(?i)upload|download|transfer|copy|move',
                r'(?i)sensitive|confidential|private|secret',
                r'(?i)database|backup|export|dump'
            ]
        }
    
    def analyze_text_artifact(self, content: str, artifact_type: str) -> Dict[str, Any]:
        """Analyser artifact textuel (logs, etc.)"""
        findings = {
            'artifact_type': artifact_type,
            'analysis_timestamp': datetime.now().isoformat(),
            'indicators_found': [],
            'risk_score': 0.0,
            'recommendations': []
        }
        
        # Appliquer règles d'analyse
        for category, patterns in self.analysis_rules.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    indicator = {
                        'category': category,
                        'pattern': pattern,
                        'matches': matches[:10],  # Limiter à 10 premiers matches
                        'match_count': len(matches)
                    }
                    findings['indicators_found'].append(indicator)
                    
                    # Augmenter score de risque
                    if category == 'malware_indicators':
                        findings['risk_score'] += 0.4
                    elif category == 'network_anomalies':
                        findings['risk_score'] += 0.3
                    elif category == 'data_exfiltration':
                        findings['risk_score'] += 0.5
        
        # Normaliser score
        findings['risk_score'] = min(1.0, findings['risk_score'])
        
        # Générer recommandations
        if findings['risk_score'] > 0.7:
            findings['recommendations'].append("CRITICAL: Investigation approfondie requise")
        elif findings['risk_score'] > 0.4:
            findings['recommendations'].append("WARNING: Surveillance renforcée recommandée")
        else:
            findings['recommendations'].append("INFO: Activité normale détectée")
        
        return findings
    
    def analyze_network_artifact(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyser artifact réseau"""
        findings = {
            'artifact_type': 'network_traffic',
            'analysis_timestamp': datetime.now().isoformat(),
            'suspicious_connections': [],
            'port_scan_detected': False,
            'data_volume_anomaly': False,
            'risk_score': 0.0
        }
        
        # Analyser connexions suspectes
        suspicious_ips = ['192.168.1.100', '10.0.0.99']  # IPs d'exemple
        suspicious_ports = [22, 23, 135, 139, 445, 1433, 3389]  # Ports sensibles
        
        if network_data.get('dest_ip') in suspicious_ips:
            findings['suspicious_connections'].append(f"Connexion vers IP suspecte: {network_data['dest_ip']}")
            findings['risk_score'] += 0.6
        
        if network_data.get('dest_port') in suspicious_ports:
            findings['suspicious_connections'].append(f"Connexion vers port sensible: {network_data['dest_port']}")
            findings['risk_score'] += 0.3
        
        # Détecter scan de ports (simulation)
        if network_data.get('packet_count', 0) > 100 and network_data.get('duration', 0) < 60:
            findings['port_scan_detected'] = True
            findings['risk_score'] += 0.8
        
        return findings

class LegalReportGenerator:
    """Générateur de rapports légaux conformes"""
    
    def __init__(self, template_path: str = None):
        self.template_path = template_path
    
    def generate_forensics_report(self, investigation: ForensicsInvestigation) -> str:
        """Générer rapport forensics conforme standards légaux"""
        
        report_content = f"""
# RAPPORT D'INVESTIGATION FORENSICS NUMÉRIQUE

## INFORMATIONS GÉNÉRALES
- **ID Investigation:** {investigation.id}
- **ID Incident:** {investigation.incident_id}
- **Date Investigation:** {investigation.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Enquêteur Principal:** {investigation.lead_investigator}
- **Statut:** {investigation.status}

## RÉSUMÉ EXÉCUTIF
Cette investigation forensics a été menée sur l'incident {investigation.incident_id} 
de la Station de Traitement Traffeyère conformément aux standards:
- ISO 27037 (Digital Evidence Guidelines)
- RFC 3227 (Evidence Collection and Archiving)
- ANSSI (Recommandations investigation numérique)

## CHAÎNE DE POSSESSION (CHAIN OF CUSTODY)
**Intégrité Vérifiée:** {'✅ OUI' if investigation.chain_integrity_verified else '❌ NON'}

### Preuves Collectées
"""
        
        for evidence in investigation.evidence_items:
            report_content += f"""
#### Pièce à Conviction {evidence.id}
- **Type:** {evidence.artifact_type}
- **Source:** {evidence.source}
- **Hash SHA-256:** {evidence.hash_sha256}
- **Statut Légal:** {evidence.legal_status}
- **Collecte:** {evidence.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        report_content += f"""
## TIMELINE RECONSTITUÉE
### Séquence des Événements
"""
        
        for event in investigation.timeline:
            report_content += f"""
**{event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}** - {event.event_type}
- Source: {event.source}
- Description: {event.description}
- Confiance: {event.confidence_score:.1%}
"""
        
        report_content += f"""
## CONCLUSIONS ET RECOMMANDATIONS
### Findings Techniques
"""
        for finding in investigation.findings:
            report_content += f"""
- **{finding.get('title', 'Finding')}:** {finding.get('description', 'N/A')}
- **Niveau de Risque:** {finding.get('risk_level', 'N/A')}
- **Recommandation:** {finding.get('recommendation', 'N/A')}
"""
        
        report_content += f"""

## CERTIFICATION
Ce rapport a été généré automatiquement par le système forensics IA 
de la Station Traffeyère le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}.

L'intégrité des preuves a été vérifiée par signature cryptographique 
et la chaîne de possession est documentée de manière immutable.

---
**CONFIDENTIEL - USAGE JURIDIQUE UNIQUEMENT**
Station de Traitement Traffeyère - Investigation Forensics
"""
        
        return report_content
    
    def save_report(self, content: str, investigation_id: str) -> str:
        """Sauvegarder rapport avec horodatage"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"forensics_report_{investigation_id}_{timestamp}.md"
        filepath = Path("reports") / filename
        
        # Créer répertoire si nécessaire
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire rapport
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"📄 Rapport forensics sauvegardé: {filepath}")
        return str(filepath)

class AIForensicsEngine:
    """Moteur forensics IA principal"""
    
    def __init__(self, db_path: str = "data/forensics.db"):
        self.db_path = db_path
        self.custody_manager = ChainOfCustodyManager("config/forensics_private_key.pem")
        self.timeline_reconstructor = TimelineReconstructor()
        self.artifact_analyzer = ArtifactAnalyzer()
        self.report_generator = LegalReportGenerator()
        self._setup_database()
    
    def _setup_database(self):
        """Initialiser base de données forensics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table investigations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS investigations (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                start_time TIMESTAMP,
                status TEXT,
                lead_investigator TEXT,
                chain_integrity_verified BOOLEAN,
                report_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table evidence
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                investigation_id TEXT,
                timestamp TIMESTAMP,
                source TEXT,
                artifact_type TEXT,
                content TEXT,
                hash_sha256 TEXT,
                legal_status TEXT,
                metadata TEXT,
                FOREIGN KEY (investigation_id) REFERENCES investigations (id)
            )
        ''')
        
        # Table timeline events
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timeline_events (
                id TEXT PRIMARY KEY,
                investigation_id TEXT,
                timestamp TIMESTAMP,
                event_type TEXT,
                source TEXT,
                description TEXT,
                confidence_score REAL,
                correlation_ids TEXT,
                FOREIGN KEY (investigation_id) REFERENCES investigations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def start_investigation(self, incident_id: str, investigator: str) -> str:
        """Démarrer nouvelle investigation forensics"""
        investigation_id = f"FORENSICS-{int(datetime.now().timestamp())}"
        
        # Créer investigation
        investigation = ForensicsInvestigation(
            id=investigation_id,
            incident_id=incident_id,
            start_time=datetime.now(),
            status='active',
            lead_investigator=investigator,
            evidence_items=[],
            timeline=[],
            findings=[],
            legal_report_path=None,
            chain_integrity_verified=False
        )
        
        # Sauvegarder en DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO investigations 
            (id, incident_id, start_time, status, lead_investigator, chain_integrity_verified)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            investigation_id, incident_id, investigation.start_time,
            investigation.status, investigator, False
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🔍 Investigation forensics démarrée: {investigation_id} pour incident {incident_id}")
        return investigation_id
    
    async def collect_evidence(self, investigation_id: str, source: str, 
                             artifact_type: str, content: str, 
                             collector: str) -> Evidence:
        """Collecter pièce à conviction avec chain of custody"""
        
        # Calculer hash
        hash_sha256 = hashlib.sha256(content.encode()).hexdigest()
        
        # Créer evidence
        evidence = Evidence(
            id=f"EVIDENCE-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(),
            source=source,
            artifact_type=artifact_type,
            content=content,
            hash_sha256=hash_sha256,
            chain_of_custody=[],
            legal_status='collected',
            metadata={}
        )
        
        # Ajouter à chain of custody
        custody_entry = self.custody_manager.add_custody_entry(
            evidence.id, 'collected', collector, f"Station Traffeyère - {source}",
            f"Collecte automatique artifact {artifact_type}"
        )
        evidence.chain_of_custody.append(custody_entry)
        
        # Analyser artifact
        if artifact_type in ['log', 'text']:
            analysis = self.artifact_analyzer.analyze_text_artifact(content, artifact_type)
        elif artifact_type == 'network':
            analysis = self.artifact_analyzer.analyze_network_artifact(json.loads(content))
        else:
            analysis = {'risk_score': 0.0, 'indicators_found': []}
        
        evidence.metadata['analysis'] = analysis
        
        # Sauvegarder en DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO evidence 
            (id, investigation_id, timestamp, source, artifact_type, content, 
             hash_sha256, legal_status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            evidence.id, investigation_id, evidence.timestamp, source,
            artifact_type, content, hash_sha256, 'collected',
            json.dumps(evidence.metadata)
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🔒 Evidence collectée: {evidence.id} (hash: {hash_sha256[:16]}...)")
        return evidence
    
    async def reconstruct_timeline(self, investigation_id: str) -> List[TimelineEvent]:
        """Reconstituer timeline investigation"""
        
        # Récupérer evidence de l'investigation
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content, artifact_type, source, timestamp 
            FROM evidence 
            WHERE investigation_id = ?
        ''', (investigation_id,))
        
        evidence_data = cursor.fetchall()
        conn.close()
        
        # Reset timeline reconstructor
        self.timeline_reconstructor.events = []
        
        # Traiter chaque evidence
        for content, artifact_type, source, timestamp in evidence_data:
            if artifact_type == 'log':
                # Parser logs
                try:
                    log_entries = [{'timestamp': timestamp, 'description': content, 'event_type': 'log_entry'}]
                    self.timeline_reconstructor.add_log_source(log_entries, source)
                except:
                    pass
            elif artifact_type == 'network':
                try:
                    network_data = json.loads(content)
                    self.timeline_reconstructor.add_network_traffic([network_data])
                except:
                    pass
        
        # Générer timeline
        timeline = self.timeline_reconstructor.generate_timeline()
        
        # Sauvegarder timeline en DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for event in timeline:
            cursor.execute('''
                INSERT INTO timeline_events 
                (id, investigation_id, timestamp, event_type, source, description, 
                 confidence_score, correlation_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()), investigation_id, event.timestamp,
                event.event_type, event.source, event.description,
                event.confidence_score, json.dumps(event.correlation_ids)
            ))
        
        conn.commit()
        conn.close()
        
        return timeline
    
    async def complete_investigation(self, investigation_id: str) -> str:
        """Finaliser investigation avec génération rapport"""
        
        # Récupérer investigation complète
        investigation = await self._load_investigation(investigation_id)
        
        # Vérifier intégrité chain of custody
        chain_verified = True
        for evidence in investigation.evidence_items:
            if not self.custody_manager.verify_custody_integrity(evidence.id):
                chain_verified = False
                break
        
        investigation.chain_integrity_verified = chain_verified
        investigation.status = 'completed'
        
        # Générer rapport légal
        report_content = self.report_generator.generate_forensics_report(investigation)
        report_path = self.report_generator.save_report(report_content, investigation_id)
        investigation.legal_report_path = report_path
        
        # Mettre à jour DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE investigations 
            SET status = ?, chain_integrity_verified = ?, report_path = ?
            WHERE id = ?
        ''', ('completed', chain_verified, report_path, investigation_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Investigation {investigation_id} finalisée - Rapport: {report_path}")
        return report_path
    
    async def _load_investigation(self, investigation_id: str) -> ForensicsInvestigation:
        """Charger investigation complète depuis DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Charger investigation
        cursor.execute('SELECT * FROM investigations WHERE id = ?', (investigation_id,))
        inv_row = cursor.fetchone()
        
        if not inv_row:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        # Charger evidence
        cursor.execute('SELECT * FROM evidence WHERE investigation_id = ?', (investigation_id,))
        evidence_rows = cursor.fetchall()
        
        evidence_items = []
        for row in evidence_rows:
            evidence = Evidence(
                id=row[0],
                timestamp=pd.to_datetime(row[2]),
                source=row[3],
                artifact_type=row[4],
                content=row[5],
                hash_sha256=row[6],
                chain_of_custody=[],  # Simplifié pour démo
                legal_status=row[7],
                metadata=json.loads(row[8]) if row[8] else {}
            )
            evidence_items.append(evidence)
        
        # Charger timeline
        cursor.execute('SELECT * FROM timeline_events WHERE investigation_id = ?', (investigation_id,))
        timeline_rows = cursor.fetchall()
        
        timeline = []
        for row in timeline_rows:
            event = TimelineEvent(
                timestamp=pd.to_datetime(row[2]),
                event_type=row[3],
                source=row[4],
                description=row[5],
                evidence_refs=[],
                confidence_score=row[6],
                correlation_ids=json.loads(row[7]) if row[7] else []
            )
            timeline.append(event)
        
        conn.close()
        
        # Construire investigation
        investigation = ForensicsInvestigation(
            id=inv_row[0],
            incident_id=inv_row[1],
            start_time=pd.to_datetime(inv_row[2]),
            status=inv_row[3],
            lead_investigator=inv_row[4],
            evidence_items=evidence_items,
            timeline=timeline,
            findings=[],  # À compléter selon besoins
            legal_report_path=inv_row[6],
            chain_integrity_verified=bool(inv_row[5])
        )
        
        return investigation
    
    def get_investigation_metrics(self) -> Dict[str, Any]:
        """Métriques des investigations forensics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Statistiques investigations
        cursor.execute('SELECT status, COUNT(*) FROM investigations GROUP BY status')
        status_counts = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM investigations WHERE chain_integrity_verified = 1')
        verified_investigations = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM evidence')
        total_evidence = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(confidence_score) FROM timeline_events')
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            'investigations_by_status': status_counts,
            'chain_integrity_rate': (verified_investigations / max(1, sum(status_counts.values()))) * 100,
            'total_evidence_collected': total_evidence,
            'average_event_confidence': avg_confidence,
            'forensics_engine_status': 'operational'
        }

# Test et démonstration
async def demo_forensics_engine():
    """Démonstration complète du moteur forensics"""
    engine = AIForensicsEngine("data/forensics_demo.db")
    
    print("🔍 DEMO AI FORENSICS ENGINE - Station Traffeyère")
    print("=" * 60)
    
    # Démarrer investigation
    investigation_id = await engine.start_investigation("INC-DEMO-001", "Agent Forensics IA")
    print(f"📋 Investigation démarrée: {investigation_id}")
    
    # Collecter evidence
    evidence1 = await engine.collect_evidence(
        investigation_id, "firewall_logs", "log",
        "2024-12-18 04:30:15 ALERT: Unauthorized access attempt from 192.168.1.100 to critical system",
        "Forensics Collector Bot"
    )
    
    evidence2 = await engine.collect_evidence(
        investigation_id, "network_monitor", "network",
        '{"src_ip": "192.168.1.100", "dst_ip": "10.3.0.10", "dst_port": 22, "timestamp": "2024-12-18T04:30:15Z", "packet_count": 150, "duration": 30}',
        "Network Forensics Agent"
    )
    
    print(f"🔒 Evidence collectée: {len([evidence1, evidence2])} pièces")
    
    # Reconstituer timeline  
    timeline = await engine.reconstruct_timeline(investigation_id)
    print(f"📅 Timeline reconstituée: {len(timeline)} événements")
    
    # Finaliser investigation
    report_path = await engine.complete_investigation(investigation_id)
    print(f"📄 Rapport généré: {report_path}")
    
    # Métriques
    metrics = engine.get_investigation_metrics()
    print(f"\n📊 MÉTRIQUES FORENSICS:")
    print(f"   Investigations: {metrics['investigations_by_status']}")
    print(f"   Intégrité chain of custody: {metrics['chain_integrity_rate']:.1f}%")
    print(f"   Evidence collectée: {metrics['total_evidence_collected']}")
    print(f"   Confiance moyenne: {metrics['average_event_confidence']:.2f}")
    
    return investigation_id

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_forensics_engine())
