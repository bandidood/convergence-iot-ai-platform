#!/usr/bin/env python3
"""
🕵️ ADVANCED THREAT HUNTER
Station Traffeyère IoT AI Platform - RNCP 39394 Semaine 7

Système de threat hunting proactif avec:
- Hypotheses-driven hunting avec techniques MITRE ATT&CK
- Behavioral analytics avancés avec machine learning
- Attribution APT sophistiquée avec signature matching
- Hunt campaigns automatisées avec IOC pivoting
"""

import asyncio
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
import logging
from collections import defaultdict, Counter
import hashlib
from enum import Enum
import re
import statistics
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import networkx as nx

logger = logging.getLogger('AdvancedThreatHunter')

class ThreatLevel(Enum):
    """Niveaux de menace"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class HuntStatus(Enum):
    """Statuts de campagne de chasse"""
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class TTPPhase(Enum):
    """Phases MITRE ATT&CK"""
    RECONNAISSANCE = "reconnaissance"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    EXFILTRATION = "exfiltration"
    COMMAND_CONTROL = "command_control"

@dataclass
class ThreatHypothesis:
    """Hypothèse de menace pour hunting"""
    id: str
    title: str
    description: str
    mitre_tactics: List[str]  # Ex: ["T1078", "T1021"]
    threat_actors: List[str]  # Ex: ["APT29", "Lazarus"]
    confidence_score: float  # 0-1
    priority: ThreatLevel
    hunt_queries: List[Dict[str, str]]  # Requêtes de recherche
    expected_indicators: List[str]
    created_by: str
    created_at: datetime
    last_tested: Optional[datetime]
    success_rate: float  # Historique de détection

@dataclass
class BehaviorProfile:
    """Profil comportemental d'entité"""
    entity_id: str  # IP, user, hostname
    entity_type: str  # "user", "host", "ip"
    baseline_metrics: Dict[str, float]
    current_metrics: Dict[str, float]
    anomaly_score: float  # 0-1, plus haut = plus anormal
    behavioral_patterns: List[str]
    risk_indicators: List[str]
    last_updated: datetime
    observation_period: timedelta

@dataclass
class APTSignature:
    """Signature d'attribution APT"""
    apt_group: str
    group_aliases: List[str]
    confidence: float  # 0-1
    ttps_matched: List[str]  # MITRE techniques matchées
    iocs_matched: List[str]  # IOCs correspondants
    behavioral_matches: List[str]
    timeline_correlation: float  # Corrélation temporelle
    geolocation_hints: List[str]
    campaign_references: List[str]
    last_seen: datetime

@dataclass
class HuntFindings:
    """Résultats de chasse"""
    finding_id: str
    hunt_campaign_id: str
    hypothesis_id: str
    threat_level: ThreatLevel
    title: str
    description: str
    affected_entities: List[str]
    iocs_discovered: List[Dict[str, str]]
    ttps_observed: List[str]
    timeline: List[Dict[str, Any]]
    evidence_artifacts: List[str]
    confidence_score: float
    apt_attribution: Optional[APTSignature]
    recommendations: List[str]
    discovered_at: datetime
    analyst: str

@dataclass
class HuntCampaign:
    """Campagne de threat hunting"""
    id: str
    name: str
    description: str
    hypotheses: List[str]  # IDs des hypothèses
    status: HuntStatus
    start_date: datetime
    end_date: Optional[datetime]
    lead_hunter: str
    team_members: List[str]
    scope: Dict[str, Any]  # Périmètre de la chasse
    findings: List[str]  # IDs des findings
    metrics: Dict[str, Any]  # Métriques de la campagne
    created_at: datetime

class MITREAttackMapping:
    """Mapping des techniques MITRE ATT&CK"""
    
    def __init__(self):
        self.techniques = self._load_mitre_techniques()
        self.tactics_map = self._build_tactics_mapping()
        self.apt_techniques = self._load_apt_techniques()
    
    def _load_mitre_techniques(self) -> Dict[str, Dict[str, Any]]:
        """Charger techniques MITRE ATT&CK (simulation)"""
        return {
            "T1078": {
                "name": "Valid Accounts",
                "tactic": "persistence",
                "description": "Adversaries may obtain and abuse credentials of existing accounts",
                "platforms": ["Windows", "Linux", "macOS"],
                "detection_queries": [
                    "SELECT * FROM auth_logs WHERE success=1 AND unusual_time=1",
                    "SELECT * FROM logins WHERE source_country != user_country"
                ]
            },
            "T1021": {
                "name": "Remote Services",
                "tactic": "lateral_movement", 
                "description": "Adversaries may use valid accounts to log into remote services",
                "platforms": ["Windows", "Linux"],
                "detection_queries": [
                    "SELECT * FROM network_auth WHERE protocol IN ('RDP', 'SSH', 'SMB')",
                    "SELECT * FROM process_creation WHERE process_name LIKE '%net use%'"
                ]
            },
            "T1055": {
                "name": "Process Injection",
                "tactic": "defense_evasion",
                "description": "Adversaries may inject code into processes",
                "platforms": ["Windows", "Linux"],
                "detection_queries": [
                    "SELECT * FROM process_creation WHERE parent_process != expected_parent",
                    "SELECT * FROM memory_allocation WHERE allocation_type = 'execute'"
                ]
            },
            "T1059": {
                "name": "Command and Scripting Interpreter",
                "tactic": "execution",
                "description": "Adversaries may abuse command and script interpreters",
                "platforms": ["Windows", "Linux", "macOS"],
                "detection_queries": [
                    "SELECT * FROM process_creation WHERE process_name IN ('cmd.exe', 'powershell.exe')",
                    "SELECT * FROM script_execution WHERE encoding = 'base64'"
                ]
            },
            "T1574": {
                "name": "Hijack Execution Flow",
                "tactic": "persistence",
                "description": "Adversaries may execute their own malicious payloads by hijacking execution flow",
                "platforms": ["Windows", "Linux", "macOS"],
                "detection_queries": [
                    "SELECT * FROM dll_load WHERE dll_path NOT IN (whitelist)",
                    "SELECT * FROM registry_modification WHERE key LIKE '%Run%'"
                ]
            }
        }
    
    def _build_tactics_mapping(self) -> Dict[str, List[str]]:
        """Construire mapping tactiques -> techniques"""
        mapping = defaultdict(list)
        for technique_id, details in self.techniques.items():
            mapping[details["tactic"]].append(technique_id)
        return dict(mapping)
    
    def _load_apt_techniques(self) -> Dict[str, List[str]]:
        """Charger techniques utilisées par groupes APT"""
        return {
            "APT29": ["T1078", "T1021", "T1055", "T1574"],
            "APT28": ["T1078", "T1021", "T1059"],
            "Lazarus": ["T1055", "T1059", "T1574"],
            "APT1": ["T1021", "T1078", "T1059"],
            "FIN7": ["T1055", "T1059", "T1574"],
            "Carbanak": ["T1021", "T1078", "T1055"],
            "APT40": ["T1078", "T1021", "T1059"],
            "Equation": ["T1055", "T1574", "T1078"]
        }
    
    def get_technique_info(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer informations sur une technique"""
        return self.techniques.get(technique_id)
    
    def get_apt_techniques(self, apt_group: str) -> List[str]:
        """Récupérer techniques d'un groupe APT"""
        return self.apt_techniques.get(apt_group, [])
    
    def find_related_techniques(self, technique_id: str) -> List[str]:
        """Trouver techniques liées (même tactique)"""
        if technique_id not in self.techniques:
            return []
        
        tactic = self.techniques[technique_id]["tactic"]
        return [t for t in self.tactics_map.get(tactic, []) if t != technique_id]

class BehaviorAnalytics:
    """Moteur d'analyse comportementale"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.clustering = DBSCAN(eps=0.5, min_samples=5)
        self.baselines = {}
        self.trained = False
    
    def build_behavior_profile(self, entity_data: List[Dict[str, Any]], 
                             entity_id: str, entity_type: str) -> BehaviorProfile:
        """Construire profil comportemental d'une entité"""
        
        if not entity_data:
            return BehaviorProfile(
                entity_id=entity_id,
                entity_type=entity_type,
                baseline_metrics={},
                current_metrics={},
                anomaly_score=0.0,
                behavioral_patterns=[],
                risk_indicators=[],
                last_updated=datetime.now(),
                observation_period=timedelta(days=30)
            )
        
        # Calculer métriques comportementales
        current_metrics = self._calculate_behavioral_metrics(entity_data, entity_type)
        
        # Récupérer baseline si disponible
        baseline_metrics = self.baselines.get(entity_id, current_metrics.copy())
        
        # Calculer score d'anomalie
        anomaly_score = self._calculate_anomaly_score(current_metrics, baseline_metrics)
        
        # Identifier patterns comportementaux
        patterns = self._identify_behavioral_patterns(entity_data, entity_type)
        
        # Déterminer indicateurs de risque
        risk_indicators = self._assess_risk_indicators(current_metrics, baseline_metrics, patterns)
        
        profile = BehaviorProfile(
            entity_id=entity_id,
            entity_type=entity_type,
            baseline_metrics=baseline_metrics,
            current_metrics=current_metrics,
            anomaly_score=anomaly_score,
            behavioral_patterns=patterns,
            risk_indicators=risk_indicators,
            last_updated=datetime.now(),
            observation_period=timedelta(days=30)
        )
        
        # Mettre à jour baseline si nécessaire
        if anomaly_score < 0.3:  # Comportement "normal"
            self.baselines[entity_id] = current_metrics.copy()
        
        return profile
    
    def _calculate_behavioral_metrics(self, data: List[Dict[str, Any]], entity_type: str) -> Dict[str, float]:
        """Calculer métriques comportementales"""
        if not data:
            return {}
        
        metrics = {}
        
        if entity_type == "user":
            # Métriques utilisateur
            login_times = [d.get('login_hour', 9) for d in data if 'login_hour' in d]
            login_countries = [d.get('country', 'US') for d in data if 'country' in d]
            failed_logins = [d for d in data if d.get('auth_result') == 'failed']
            
            metrics.update({
                'avg_login_hour': statistics.mean(login_times) if login_times else 9,
                'login_hour_stddev': statistics.stdev(login_times) if len(login_times) > 1 else 0,
                'unique_countries': len(set(login_countries)),
                'failed_login_rate': len(failed_logins) / len(data) if data else 0,
                'total_sessions': len(data),
                'weekend_activity_rate': len([d for d in data if d.get('is_weekend', False)]) / len(data)
            })
            
        elif entity_type == "host":
            # Métriques host
            processes = [d.get('process_count', 50) for d in data if 'process_count' in d]
            network_connections = [d.get('network_connections', 10) for d in data if 'network_connections' in d]
            cpu_usage = [d.get('cpu_usage', 20) for d in data if 'cpu_usage' in d]
            
            metrics.update({
                'avg_process_count': statistics.mean(processes) if processes else 50,
                'process_count_stddev': statistics.stdev(processes) if len(processes) > 1 else 0,
                'avg_network_connections': statistics.mean(network_connections) if network_connections else 10,
                'avg_cpu_usage': statistics.mean(cpu_usage) if cpu_usage else 20,
                'total_events': len(data)
            })
            
        elif entity_type == "ip":
            # Métriques IP
            ports_contacted = []
            bytes_transferred = []
            connection_counts = []
            
            for d in data:
                if 'dst_ports' in d:
                    ports_contacted.extend(d['dst_ports'])
                if 'bytes' in d:
                    bytes_transferred.append(d['bytes'])
                if 'connections' in d:
                    connection_counts.append(d['connections'])
            
            metrics.update({
                'unique_ports_contacted': len(set(ports_contacted)),
                'avg_bytes_transferred': statistics.mean(bytes_transferred) if bytes_transferred else 0,
                'total_connections': sum(connection_counts) if connection_counts else 0,
                'port_diversity': len(set(ports_contacted)) / len(ports_contacted) if ports_contacted else 0
            })
        
        return metrics
    
    def _calculate_anomaly_score(self, current: Dict[str, float], baseline: Dict[str, float]) -> float:
        """Calculer score d'anomalie basé sur déviation de la baseline"""
        if not current or not baseline:
            return 0.0
        
        deviations = []
        for metric, current_value in current.items():
            if metric in baseline and baseline[metric] > 0:
                deviation = abs(current_value - baseline[metric]) / baseline[metric]
                deviations.append(min(deviation, 2.0))  # Cap à 200% de déviation
        
        return statistics.mean(deviations) if deviations else 0.0
    
    def _identify_behavioral_patterns(self, data: List[Dict[str, Any]], entity_type: str) -> List[str]:
        """Identifier patterns comportementaux"""
        patterns = []
        
        if not data:
            return patterns
        
        # Patterns temporels
        timestamps = [datetime.fromisoformat(d['timestamp']) if isinstance(d.get('timestamp'), str) 
                     else d.get('timestamp', datetime.now()) for d in data]
        
        hours = [ts.hour for ts in timestamps if ts]
        if hours:
            night_activity = len([h for h in hours if h < 6 or h > 22]) / len(hours)
            if night_activity > 0.3:
                patterns.append("high_night_activity")
            
            weekend_activity = len([ts for ts in timestamps if ts.weekday() >= 5]) / len(timestamps)
            if weekend_activity > 0.4:
                patterns.append("high_weekend_activity")
        
        # Patterns spécifiques par type
        if entity_type == "user":
            # Pattern de connexion
            countries = [d.get('country', 'US') for d in data if 'country' in d]
            if len(set(countries)) > 3:
                patterns.append("multi_country_access")
            
            # Pattern de échecs d'authentification
            failed_rate = len([d for d in data if d.get('auth_result') == 'failed']) / len(data)
            if failed_rate > 0.2:
                patterns.append("high_auth_failure_rate")
                
        elif entity_type == "host":
            # Pattern de processus
            process_names = []
            for d in data:
                if 'processes' in d:
                    process_names.extend(d['processes'])
            
            suspicious_processes = ['cmd.exe', 'powershell.exe', 'wscript.exe', 'cscript.exe']
            suspicious_count = len([p for p in process_names if any(sus in p.lower() for sus in suspicious_processes)])
            
            if suspicious_count > len(process_names) * 0.1:
                patterns.append("suspicious_process_activity")
        
        return patterns
    
    def _assess_risk_indicators(self, current: Dict[str, float], baseline: Dict[str, float], 
                              patterns: List[str]) -> List[str]:
        """Évaluer indicateurs de risque"""
        indicators = []
        
        # Indicateurs basés sur anomalies métriques
        for metric, value in current.items():
            if metric in baseline and baseline[metric] > 0:
                ratio = value / baseline[metric]
                if ratio > 2.0:
                    indicators.append(f"high_{metric}")
                elif ratio < 0.5:
                    indicators.append(f"low_{metric}")
        
        # Indicateurs basés sur patterns
        risk_patterns = [
            "high_night_activity", "multi_country_access", 
            "high_auth_failure_rate", "suspicious_process_activity"
        ]
        
        for pattern in patterns:
            if pattern in risk_patterns:
                indicators.append(f"risky_pattern_{pattern}")
        
        return indicators

class APTAttributionEngine:
    """Moteur d'attribution APT"""
    
    def __init__(self):
        self.mitre_mapping = MITREAttackMapping()
        self.apt_profiles = self._load_apt_profiles()
        self.ioc_database = self._load_ioc_database()
    
    def _load_apt_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Charger profils APT connus"""
        return {
            "APT29": {
                "aliases": ["Cozy Bear", "The Dukes", "CozyDuke"],
                "origin": "Russia",
                "targets": ["Government", "Think Tanks", "Healthcare"],
                "preferred_ttps": ["T1078", "T1021", "T1055", "T1574"],
                "signature_indicators": [
                    "powershell encoded commands",
                    "legitimate tools misuse",
                    "memory-only payloads",
                    "cloud service abuse"
                ],
                "typical_timeline": {"initial_access": 1, "persistence": 2, "lateral_movement": 7},
                "behavioral_markers": [
                    "patient_reconnaissance", 
                    "living_off_the_land",
                    "minimal_malware_footprint"
                ]
            },
            "APT28": {
                "aliases": ["Fancy Bear", "Sofacy", "Pawn Storm"],
                "origin": "Russia", 
                "targets": ["Military", "Government", "Media"],
                "preferred_ttps": ["T1078", "T1021", "T1059"],
                "signature_indicators": [
                    "spear phishing attachments",
                    "credential harvesting",
                    "zero-day exploits",
                    "custom malware families"
                ],
                "typical_timeline": {"initial_access": 1, "persistence": 1, "lateral_movement": 3},
                "behavioral_markers": [
                    "aggressive_tactics",
                    "custom_tooling", 
                    "rapid_operations"
                ]
            },
            "Lazarus": {
                "aliases": ["Hidden Cobra", "Guardians of Peace"],
                "origin": "North Korea",
                "targets": ["Financial", "Cryptocurrency", "Entertainment"],
                "preferred_ttps": ["T1055", "T1059", "T1574"],
                "signature_indicators": [
                    "destructive attacks",
                    "financial motivation",
                    "supply chain attacks",
                    "cryptocurrency theft"
                ],
                "typical_timeline": {"initial_access": 1, "persistence": 3, "lateral_movement": 5},
                "behavioral_markers": [
                    "destructive_capability",
                    "financial_focus",
                    "supply_chain_targeting"
                ]
            }
        }
    
    def _load_ioc_database(self) -> Dict[str, List[Dict[str, str]]]:
        """Charger base IOCs par APT"""
        return {
            "APT29": [
                {"type": "domain", "value": "cozy-bear-c2.com", "context": "C2 domain"},
                {"type": "hash", "value": "a1b2c3d4e5f6...", "context": "CozyDuke malware"},
                {"type": "ip", "value": "192.168.100.50", "context": "Staging server"}
            ],
            "APT28": [
                {"type": "domain", "value": "fancy-bear-ops.net", "context": "Phishing domain"},
                {"type": "hash", "value": "f6e5d4c3b2a1...", "context": "Sofacy dropper"},
                {"type": "email", "value": "legit@fake-org.com", "context": "Spear phishing sender"}
            ],
            "Lazarus": [
                {"type": "domain", "value": "hidden-cobra-net.org", "context": "Command server"},
                {"type": "hash", "value": "123456789abc...", "context": "Destructive payload"},
                {"type": "btc_address", "value": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "context": "Ransom wallet"}
            ]
        }
    
    def analyze_attribution(self, findings: List[HuntFindings], 
                          behavior_profiles: List[BehaviorProfile]) -> List[APTSignature]:
        """Analyser attribution APT basée sur findings"""
        attribution_scores = defaultdict(float)
        attribution_evidence = defaultdict(list)
        
        # Analyser chaque finding
        for finding in findings:
            for apt_group in self.apt_profiles.keys():
                score, evidence = self._score_apt_match(finding, apt_group)
                attribution_scores[apt_group] += score
                attribution_evidence[apt_group].extend(evidence)
        
        # Analyser profils comportementaux  
        for profile in behavior_profiles:
            for apt_group in self.apt_profiles.keys():
                score, evidence = self._score_behavioral_match(profile, apt_group)
                attribution_scores[apt_group] += score * 0.5  # Poids moindre
                attribution_evidence[apt_group].extend(evidence)
        
        # Générer signatures APT
        signatures = []
        for apt_group, total_score in attribution_scores.items():
            if total_score > 0.3:  # Seuil minimum
                confidence = min(total_score, 1.0)
                
                signature = APTSignature(
                    apt_group=apt_group,
                    group_aliases=self.apt_profiles[apt_group]["aliases"],
                    confidence=confidence,
                    ttps_matched=self._extract_ttps_from_evidence(attribution_evidence[apt_group]),
                    iocs_matched=self._extract_iocs_from_evidence(attribution_evidence[apt_group]),
                    behavioral_matches=self._extract_behaviors_from_evidence(attribution_evidence[apt_group]),
                    timeline_correlation=self._calculate_timeline_correlation(findings, apt_group),
                    geolocation_hints=[self.apt_profiles[apt_group]["origin"]],
                    campaign_references=[],
                    last_seen=datetime.now()
                )
                signatures.append(signature)
        
        # Trier par confiance
        signatures.sort(key=lambda x: x.confidence, reverse=True)
        return signatures[:3]  # Top 3 candidats
    
    def _score_apt_match(self, finding: HuntFindings, apt_group: str) -> Tuple[float, List[str]]:
        """Scorer correspondance avec groupe APT"""
        score = 0.0
        evidence = []
        
        apt_profile = self.apt_profiles[apt_group]
        
        # Score basé sur TTPs
        apt_ttps = set(apt_profile["preferred_ttps"])
        finding_ttps = set(finding.ttps_observed)
        ttp_overlap = len(apt_ttps & finding_ttps)
        
        if apt_ttps:
            ttp_score = ttp_overlap / len(apt_ttps)
            score += ttp_score * 0.4
            if ttp_overlap > 0:
                evidence.append(f"TTP_match_{ttp_overlap}_techniques")
        
        # Score basé sur IOCs
        apt_iocs = {ioc["value"] for ioc in self.ioc_database.get(apt_group, [])}
        finding_iocs = {ioc.get("value", "") for ioc in finding.iocs_discovered}
        ioc_overlap = len(apt_iocs & finding_iocs)
        
        if ioc_overlap > 0:
            score += 0.6  # Fort indicateur
            evidence.append(f"IOC_match_{ioc_overlap}_indicators")
        
        # Score basé sur indicateurs de signature
        signature_matches = 0
        for indicator in apt_profile["signature_indicators"]:
            if any(indicator.lower() in desc.lower() 
                  for desc in [finding.title, finding.description]):
                signature_matches += 1
        
        if apt_profile["signature_indicators"]:
            signature_score = signature_matches / len(apt_profile["signature_indicators"])
            score += signature_score * 0.3
            if signature_matches > 0:
                evidence.append(f"Signature_match_{signature_matches}_indicators")
        
        return score, evidence
    
    def _score_behavioral_match(self, profile: BehaviorProfile, apt_group: str) -> Tuple[float, List[str]]:
        """Scorer correspondance comportementale"""
        score = 0.0
        evidence = []
        
        apt_profile = self.apt_profiles[apt_group]
        behavioral_markers = apt_profile.get("behavioral_markers", [])
        
        # Analyser patterns comportementaux
        matches = 0
        for marker in behavioral_markers:
            marker_keywords = marker.split("_")
            for pattern in profile.behavioral_patterns:
                if any(keyword in pattern for keyword in marker_keywords):
                    matches += 1
                    break
        
        if behavioral_markers:
            behavior_score = matches / len(behavioral_markers)
            score += behavior_score * 0.4
            if matches > 0:
                evidence.append(f"Behavioral_match_{matches}_markers")
        
        # Analyser indicateurs de risque
        risk_matches = 0
        for indicator in profile.risk_indicators:
            if any(marker in indicator for marker in behavioral_markers):
                risk_matches += 1
        
        if risk_matches > 0:
            score += 0.2
            evidence.append(f"Risk_pattern_match_{risk_matches}")
        
        return score, evidence
    
    def _extract_ttps_from_evidence(self, evidence: List[str]) -> List[str]:
        """Extraire TTPs de l'évidence"""
        ttps = []
        for item in evidence:
            if "TTP_match" in item:
                # Simuler extraction de TTPs
                ttps.extend(["T1078", "T1021", "T1055"])  # Exemple
        return list(set(ttps))
    
    def _extract_iocs_from_evidence(self, evidence: List[str]) -> List[str]:
        """Extraire IOCs de l'évidence"""
        iocs = []
        for item in evidence:
            if "IOC_match" in item:
                # Simuler extraction d'IOCs
                iocs.extend(["malicious.domain.com", "192.168.1.100"])  # Exemple
        return list(set(iocs))
    
    def _extract_behaviors_from_evidence(self, evidence: List[str]) -> List[str]:
        """Extraire comportements de l'évidence"""
        behaviors = []
        for item in evidence:
            if "Behavioral_match" in item or "Risk_pattern" in item:
                behaviors.append(item)
        return behaviors
    
    def _calculate_timeline_correlation(self, findings: List[HuntFindings], apt_group: str) -> float:
        """Calculer corrélation temporelle avec profil APT"""
        if not findings:
            return 0.0
        
        apt_profile = self.apt_profiles[apt_group]
        typical_timeline = apt_profile.get("typical_timeline", {})
        
        # Simulation de corrélation temporelle
        # En réalité, analyserait la séquence et timing des attaques
        return 0.7  # Score exemple

class ThreatHuntingEngine:
    """Moteur principal de threat hunting"""
    
    def __init__(self, db_path: str = "data/threat_hunting.db"):
        self.db_path = db_path
        self.mitre_mapping = MITREAttackMapping()
        self.behavior_analytics = BehaviorAnalytics()
        self.attribution_engine = APTAttributionEngine()
        self.active_campaigns = {}
        self._setup_database()
    
    def _setup_database(self):
        """Initialiser base de données threat hunting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table hypothèses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hunt_hypotheses (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                mitre_tactics TEXT,
                threat_actors TEXT,
                confidence_score REAL,
                priority TEXT,
                hunt_queries TEXT,
                expected_indicators TEXT,
                created_by TEXT,
                created_at TIMESTAMP,
                last_tested TIMESTAMP,
                success_rate REAL
            )
        ''')
        
        # Table campagnes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hunt_campaigns (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                hypotheses TEXT,
                status TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                lead_hunter TEXT,
                team_members TEXT,
                scope TEXT,
                findings TEXT,
                metrics TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # Table findings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hunt_findings (
                finding_id TEXT PRIMARY KEY,
                hunt_campaign_id TEXT,
                hypothesis_id TEXT,
                threat_level TEXT,
                title TEXT,
                description TEXT,
                affected_entities TEXT,
                iocs_discovered TEXT,
                ttps_observed TEXT,
                timeline TEXT,
                evidence_artifacts TEXT,
                confidence_score REAL,
                apt_attribution TEXT,
                recommendations TEXT,
                discovered_at TIMESTAMP,
                analyst TEXT
            )
        ''')
        
        # Table profils comportementaux
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_profiles (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT,
                baseline_metrics TEXT,
                current_metrics TEXT,
                anomaly_score REAL,
                behavioral_patterns TEXT,
                risk_indicators TEXT,
                last_updated TIMESTAMP,
                observation_period TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def create_threat_hypothesis(self, title: str, description: str, 
                                     mitre_tactics: List[str], threat_actors: List[str],
                                     priority: ThreatLevel, created_by: str) -> ThreatHypothesis:
        """Créer nouvelle hypothèse de menace"""
        
        hypothesis_id = f"HYPO-{int(datetime.now().timestamp())}"
        
        # Générer requêtes de chasse basées sur TTPs MITRE
        hunt_queries = []
        expected_indicators = []
        
        for tactic in mitre_tactics:
            technique_info = self.mitre_mapping.get_technique_info(tactic)
            if technique_info:
                hunt_queries.extend([
                    {"query": q, "platform": "multi", "technique": tactic}
                    for q in technique_info.get("detection_queries", [])
                ])
                expected_indicators.append(f"Activity_related_to_{tactic}")
        
        hypothesis = ThreatHypothesis(
            id=hypothesis_id,
            title=title,
            description=description,
            mitre_tactics=mitre_tactics,
            threat_actors=threat_actors,
            confidence_score=0.5,  # Score initial neutre
            priority=priority,
            hunt_queries=hunt_queries,
            expected_indicators=expected_indicators,
            created_by=created_by,
            created_at=datetime.now(),
            last_tested=None,
            success_rate=0.0
        )
        
        # Sauvegarder en DB
        await self._save_hypothesis(hypothesis)
        
        logger.info(f"🎯 Hypothèse créée: {title} avec {len(hunt_queries)} requêtes")
        return hypothesis
    
    async def launch_hunt_campaign(self, name: str, description: str,
                                 hypothesis_ids: List[str], lead_hunter: str,
                                 team_members: List[str], scope: Dict[str, Any]) -> HuntCampaign:
        """Lancer campagne de chasse"""
        
        campaign_id = f"HUNT-{int(datetime.now().timestamp())}"
        
        campaign = HuntCampaign(
            id=campaign_id,
            name=name,
            description=description,
            hypotheses=hypothesis_ids,
            status=HuntStatus.ACTIVE,
            start_date=datetime.now(),
            end_date=None,
            lead_hunter=lead_hunter,
            team_members=team_members,
            scope=scope,
            findings=[],
            metrics={
                "queries_executed": 0,
                "entities_analyzed": 0,
                "findings_discovered": 0,
                "hypotheses_tested": len(hypothesis_ids)
            },
            created_at=datetime.now()
        )
        
        self.active_campaigns[campaign_id] = campaign
        
        # Sauvegarder en DB
        await self._save_campaign(campaign)
        
        logger.info(f"🚀 Campagne lancée: {name} avec {len(hypothesis_ids)} hypothèses")
        return campaign
    
    async def execute_hunt_queries(self, campaign_id: str, 
                                 data_sources: Dict[str, List[Dict[str, Any]]]) -> List[HuntFindings]:
        """Exécuter requêtes de chasse sur sources de données"""
        
        if campaign_id not in self.active_campaigns:
            raise ValueError(f"Campagne {campaign_id} non trouvée")
        
        campaign = self.active_campaigns[campaign_id]
        findings = []
        
        # Charger hypothèses de la campagne
        hypotheses = []
        for hypo_id in campaign.hypotheses:
            hypothesis = await self._load_hypothesis(hypo_id)
            if hypothesis:
                hypotheses.append(hypothesis)
        
        # Exécuter requêtes pour chaque hypothèse
        for hypothesis in hypotheses:
            logger.info(f"🔍 Test hypothèse: {hypothesis.title}")
            
            hypothesis_findings = await self._test_hypothesis(
                hypothesis, data_sources, campaign_id
            )
            findings.extend(hypothesis_findings)
            
            # Mettre à jour métriques campagne
            campaign.metrics["queries_executed"] += len(hypothesis.hunt_queries)
        
        # Mettre à jour findings de campagne
        campaign.findings.extend([f.finding_id for f in findings])
        campaign.metrics["findings_discovered"] = len(campaign.findings)
        
        logger.info(f"🎯 Campagne {campaign_id}: {len(findings)} nouveaux findings")
        return findings
    
    async def _test_hypothesis(self, hypothesis: ThreatHypothesis, 
                             data_sources: Dict[str, List[Dict[str, Any]]],
                             campaign_id: str) -> List[HuntFindings]:
        """Tester une hypothèse sur les données"""
        findings = []
        
        for query_info in hypothesis.hunt_queries:
            query = query_info["query"]
            technique = query_info.get("technique", "unknown")
            
            # Simuler exécution de requête sur sources
            matches = await self._execute_hunt_query(query, data_sources)
            
            if matches:
                # Créer finding
                finding = HuntFindings(
                    finding_id=f"FIND-{int(datetime.now().timestamp())}-{len(findings)}",
                    hunt_campaign_id=campaign_id,
                    hypothesis_id=hypothesis.id,
                    threat_level=hypothesis.priority,
                    title=f"Detection: {hypothesis.title}",
                    description=f"Query matched {len(matches)} events related to {technique}",
                    affected_entities=self._extract_entities_from_matches(matches),
                    iocs_discovered=self._extract_iocs_from_matches(matches),
                    ttps_observed=[technique],
                    timeline=self._build_timeline_from_matches(matches),
                    evidence_artifacts=[f"query_result_{technique}.json"],
                    confidence_score=min(0.8, len(matches) / 10.0),  # Score basé sur nombre de matches
                    apt_attribution=None,  # Sera rempli plus tard
                    recommendations=self._generate_recommendations(technique, matches),
                    discovered_at=datetime.now(),
                    analyst="AI Hunter Bot"
                )
                
                findings.append(finding)
                await self._save_finding(finding)
        
        # Mettre à jour statistiques hypothèse
        if findings:
            hypothesis.success_rate = min(1.0, hypothesis.success_rate + 0.1)
            hypothesis.last_tested = datetime.now()
            await self._save_hypothesis(hypothesis)
        
        return findings
    
    async def _execute_hunt_query(self, query: str, 
                                data_sources: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Exécuter requête de chasse (simulation)"""
        matches = []
        
        # Simulation d'exécution de requête SQL/KQL
        # En réalité, exécuterait sur SIEM, EDR, etc.
        
        for source_name, events in data_sources.items():
            for event in events:
                # Simulation de matching basique
                if self._query_matches_event(query, event):
                    match = event.copy()
                    match["source"] = source_name
                    match["matched_query"] = query
                    matches.append(match)
        
        return matches[:100]  # Limiter résultats
    
    def _query_matches_event(self, query: str, event: Dict[str, Any]) -> bool:
        """Vérifier si requête matche un événement (simulation)"""
        # Simulation très basique de matching
        query_lower = query.lower()
        
        # Recherche de mots-clés dans l'événement
        if "powershell" in query_lower:
            return "powershell" in str(event.get("process_name", "")).lower()
        elif "cmd.exe" in query_lower:
            return "cmd" in str(event.get("process_name", "")).lower()
        elif "auth" in query_lower:
            return event.get("event_type") == "authentication"
        elif "network" in query_lower:
            return event.get("event_type") == "network_connection"
        elif "rdp" in query_lower or "ssh" in query_lower:
            return event.get("protocol") in ["RDP", "SSH"]
        
        # Match par défaut pour démonstration
        return len(str(event)) > 50  # Événements "substantiels"
    
    def _extract_entities_from_matches(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Extraire entités affectées des matches"""
        entities = set()
        
        for match in matches:
            if "user" in match:
                entities.add(f"user:{match['user']}")
            if "hostname" in match:
                entities.add(f"host:{match['hostname']}")
            if "src_ip" in match:
                entities.add(f"ip:{match['src_ip']}")
            if "dst_ip" in match:
                entities.add(f"ip:{match['dst_ip']}")
        
        return list(entities)
    
    def _extract_iocs_from_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extraire IOCs des matches"""
        iocs = []
        
        for match in matches:
            # Extraire domaines
            if "domain" in match:
                iocs.append({"type": "domain", "value": match["domain"], "context": "Network connection"})
            
            # Extraire IPs suspectes
            if "dst_ip" in match and not match["dst_ip"].startswith("10."):
                iocs.append({"type": "ip", "value": match["dst_ip"], "context": "External connection"})
            
            # Extraire hashs de fichiers
            if "file_hash" in match:
                iocs.append({"type": "hash", "value": match["file_hash"], "context": "File execution"})
        
        return iocs
    
    def _build_timeline_from_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Construire timeline à partir des matches"""
        timeline = []
        
        for match in matches:
            timestamp = match.get("timestamp", datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            timeline.append({
                "timestamp": timestamp.isoformat(),
                "event_type": match.get("event_type", "unknown"),
                "description": match.get("description", "Hunt query match"),
                "source": match.get("source", "unknown"),
                "entities": [match.get("user", ""), match.get("hostname", "")]
            })
        
        # Trier par timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        return timeline
    
    def _generate_recommendations(self, technique: str, matches: List[Dict[str, Any]]) -> List[str]:
        """Générer recommandations basées sur technique MITRE"""
        recommendations = []
        
        technique_info = self.mitre_mapping.get_technique_info(technique)
        if technique_info:
            tactic = technique_info["tactic"]
            
            if tactic == "persistence":
                recommendations.extend([
                    "Review and harden persistence mechanisms",
                    "Implement application whitelisting",
                    "Monitor registry and startup locations"
                ])
            elif tactic == "lateral_movement":
                recommendations.extend([
                    "Implement network segmentation",
                    "Monitor lateral movement indicators",
                    "Strengthen authentication controls"
                ])
            elif tactic == "execution":
                recommendations.extend([
                    "Monitor script execution",
                    "Implement PowerShell logging",
                    "Review command-line activity"
                ])
        
        recommendations.append(f"Investigate {len(matches)} related events thoroughly")
        return recommendations
    
    async def analyze_behavioral_anomalies(self, data_sources: Dict[str, List[Dict[str, Any]]]) -> List[BehaviorProfile]:
        """Analyser anomalies comportementales"""
        profiles = []
        
        # Grouper données par entité
        entity_data = defaultdict(list)
        
        for source_name, events in data_sources.items():
            for event in events:
                # Grouper par utilisateur
                if "user" in event:
                    entity_data[f"user:{event['user']}"].append(event)
                
                # Grouper par host
                if "hostname" in event:
                    entity_data[f"host:{event['hostname']}"].append(event)
                
                # Grouper par IP
                if "src_ip" in event:
                    entity_data[f"ip:{event['src_ip']}"].append(event)
        
        # Construire profils comportementaux
        for entity_id, events in entity_data.items():
            if len(events) >= 5:  # Minimum d'événements pour profil
                entity_type = entity_id.split(":")[0]
                profile = self.behavior_analytics.build_behavior_profile(
                    events, entity_id, entity_type
                )
                profiles.append(profile)
                
                # Sauvegarder profil
                await self._save_behavior_profile(profile)
        
        # Trier par score d'anomalie
        profiles.sort(key=lambda x: x.anomaly_score, reverse=True)
        
        logger.info(f"🧠 {len(profiles)} profils comportementaux analysés")
        return profiles
    
    async def perform_apt_attribution(self, campaign_id: str) -> List[APTSignature]:
        """Effectuer attribution APT pour campagne"""
        
        if campaign_id not in self.active_campaigns:
            return []
        
        campaign = self.active_campaigns[campaign_id]
        
        # Charger findings de la campagne
        findings = []
        for finding_id in campaign.findings:
            finding = await self._load_finding(finding_id)
            if finding:
                findings.append(finding)
        
        # Charger profils comportementaux récents
        behavior_profiles = await self._load_recent_behavior_profiles()
        
        # Effectuer attribution
        signatures = self.attribution_engine.analyze_attribution(findings, behavior_profiles)
        
        # Mettre à jour findings avec attribution
        for signature in signatures:
            if signature.confidence > 0.5:
                for finding in findings:
                    if not finding.apt_attribution:
                        finding.apt_attribution = signature
                        await self._save_finding(finding)
        
        logger.info(f"🎯 Attribution APT: {len(signatures)} candidats identifiés")
        return signatures
    
    async def _save_hypothesis(self, hypothesis: ThreatHypothesis):
        """Sauvegarder hypothèse en DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO hunt_hypotheses
            (id, title, description, mitre_tactics, threat_actors, confidence_score,
             priority, hunt_queries, expected_indicators, created_by, created_at,
             last_tested, success_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            hypothesis.id, hypothesis.title, hypothesis.description,
            json.dumps(hypothesis.mitre_tactics), json.dumps(hypothesis.threat_actors),
            hypothesis.confidence_score, hypothesis.priority.value,
            json.dumps(hypothesis.hunt_queries), json.dumps(hypothesis.expected_indicators),
            hypothesis.created_by, hypothesis.created_at, hypothesis.last_tested,
            hypothesis.success_rate
        ))
        
        conn.commit()
        conn.close()
    
    async def _save_campaign(self, campaign: HuntCampaign):
        """Sauvegarder campagne en DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO hunt_campaigns
            (id, name, description, hypotheses, status, start_date, end_date,
             lead_hunter, team_members, scope, findings, metrics, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            campaign.id, campaign.name, campaign.description,
            json.dumps(campaign.hypotheses), campaign.status.value,
            campaign.start_date, campaign.end_date, campaign.lead_hunter,
            json.dumps(campaign.team_members), json.dumps(campaign.scope),
            json.dumps(campaign.findings), json.dumps(campaign.metrics),
            campaign.created_at
        ))
        
        conn.commit()
        conn.close()
    
    async def _save_finding(self, finding: HuntFindings):
        """Sauvegarder finding en DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        apt_attribution_json = None
        if finding.apt_attribution:
            # Convertir datetime en string pour sérialisation JSON
            apt_dict = asdict(finding.apt_attribution)
            if 'last_seen' in apt_dict and apt_dict['last_seen']:
                apt_dict['last_seen'] = apt_dict['last_seen'].isoformat()
            apt_attribution_json = json.dumps(apt_dict)
        
        cursor.execute('''
            INSERT OR REPLACE INTO hunt_findings
            (finding_id, hunt_campaign_id, hypothesis_id, threat_level, title,
             description, affected_entities, iocs_discovered, ttps_observed,
             timeline, evidence_artifacts, confidence_score, apt_attribution,
             recommendations, discovered_at, analyst)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            finding.finding_id, finding.hunt_campaign_id, finding.hypothesis_id,
            finding.threat_level.value, finding.title, finding.description,
            json.dumps(finding.affected_entities), json.dumps(finding.iocs_discovered),
            json.dumps(finding.ttps_observed), json.dumps(finding.timeline),
            json.dumps(finding.evidence_artifacts), finding.confidence_score,
            apt_attribution_json, json.dumps(finding.recommendations),
            finding.discovered_at, finding.analyst
        ))
        
        conn.commit()
        conn.close()
    
    async def _save_behavior_profile(self, profile: BehaviorProfile):
        """Sauvegarder profil comportemental"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO behavior_profiles
            (entity_id, entity_type, baseline_metrics, current_metrics,
             anomaly_score, behavioral_patterns, risk_indicators,
             last_updated, observation_period)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile.entity_id, profile.entity_type,
            json.dumps(profile.baseline_metrics), json.dumps(profile.current_metrics),
            profile.anomaly_score, json.dumps(profile.behavioral_patterns),
            json.dumps(profile.risk_indicators), profile.last_updated,
            str(profile.observation_period)
        ))
        
        conn.commit()
        conn.close()
    
    async def _load_hypothesis(self, hypothesis_id: str) -> Optional[ThreatHypothesis]:
        """Charger hypothèse depuis DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM hunt_hypotheses WHERE id = ?', (hypothesis_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return ThreatHypothesis(
            id=row[0], title=row[1], description=row[2],
            mitre_tactics=json.loads(row[3]), threat_actors=json.loads(row[4]),
            confidence_score=row[5], priority=ThreatLevel(row[6]),
            hunt_queries=json.loads(row[7]), expected_indicators=json.loads(row[8]),
            created_by=row[9], created_at=datetime.fromisoformat(row[10]),
            last_tested=datetime.fromisoformat(row[11]) if row[11] else None,
            success_rate=row[12]
        )
    
    async def _load_finding(self, finding_id: str) -> Optional[HuntFindings]:
        """Charger finding depuis DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM hunt_findings WHERE finding_id = ?', (finding_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        apt_attribution = None
        if row[12]:  # apt_attribution column
            apt_data = json.loads(row[12])
            apt_attribution = APTSignature(**apt_data)
        
        return HuntFindings(
            finding_id=row[0], hunt_campaign_id=row[1], hypothesis_id=row[2],
            threat_level=ThreatLevel(row[3]), title=row[4], description=row[5],
            affected_entities=json.loads(row[6]), iocs_discovered=json.loads(row[7]),
            ttps_observed=json.loads(row[8]), timeline=json.loads(row[9]),
            evidence_artifacts=json.loads(row[10]), confidence_score=row[11],
            apt_attribution=apt_attribution, recommendations=json.loads(row[13]),
            discovered_at=datetime.fromisoformat(row[14]), analyst=row[15]
        )
    
    async def _load_recent_behavior_profiles(self) -> List[BehaviorProfile]:
        """Charger profils comportementaux récents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM behavior_profiles 
            WHERE last_updated >= datetime('now', '-7 days')
            ORDER BY anomaly_score DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        profiles = []
        for row in rows:
            profile = BehaviorProfile(
                entity_id=row[0], entity_type=row[1],
                baseline_metrics=json.loads(row[2]), current_metrics=json.loads(row[3]),
                anomaly_score=row[4], behavioral_patterns=json.loads(row[5]),
                risk_indicators=json.loads(row[6]),
                last_updated=datetime.fromisoformat(row[7]),
                observation_period=timedelta(seconds=float(row[8].split(':')[0]) * 86400)  # Conversion simplifiée
            )
            profiles.append(profile)
        
        return profiles
    
    def get_hunt_metrics(self) -> Dict[str, Any]:
        """Métriques de threat hunting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Métriques générales
        cursor.execute('SELECT COUNT(*) FROM hunt_campaigns WHERE status = "active"')
        active_campaigns = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM hunt_findings WHERE discovered_at >= datetime("now", "-24 hours")')
        findings_24h = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(confidence_score) FROM hunt_findings')
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        cursor.execute('SELECT COUNT(*) FROM behavior_profiles WHERE anomaly_score > 0.5')
        high_risk_entities = cursor.fetchone()[0]
        
        # Top techniques MITRE
        cursor.execute('''
            SELECT ttps_observed, COUNT(*) as count
            FROM hunt_findings 
            WHERE ttps_observed != "[]"
            GROUP BY ttps_observed 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        top_ttps = cursor.fetchall()
        
        conn.close()
        
        return {
            'active_campaigns': active_campaigns,
            'findings_last_24h': findings_24h,
            'average_confidence': avg_confidence,
            'high_risk_entities': high_risk_entities,
            'top_mitre_techniques': dict(top_ttps),
            'hunter_status': 'operational'
        }

# Démonstration complète
async def demo_advanced_threat_hunter():
    """Démonstration du système de threat hunting avancé"""
    hunter = ThreatHuntingEngine("data/threat_hunting_demo.db")
    
    print("🕵️ DEMO ADVANCED THREAT HUNTER - Station Traffeyère")
    print("=" * 65)
    
    # 1. Créer hypothèses de menace
    print("\n🎯 CRÉATION D'HYPOTHÈSES DE MENACE")
    
    hypo1 = await hunter.create_threat_hypothesis(
        title="APT29 Living off the Land Attack",
        description="Detect potential APT29 activities using legitimate tools for malicious purposes",
        mitre_tactics=["T1078", "T1021", "T1055"],
        threat_actors=["APT29", "Cozy Bear"],
        priority=ThreatLevel.HIGH,
        created_by="Senior Threat Hunter"
    )
    
    hypo2 = await hunter.create_threat_hypothesis(
        title="Lateral Movement via Remote Services",
        description="Detect lateral movement using RDP, SSH, or SMB services",
        mitre_tactics=["T1021", "T1059"],
        threat_actors=["APT28", "FIN7"],
        priority=ThreatLevel.MEDIUM,
        created_by="Threat Hunter Jr"
    )
    
    print(f"   ✅ Hypothèse 1: {hypo1.title} ({len(hypo1.hunt_queries)} requêtes)")
    print(f"   ✅ Hypothèse 2: {hypo2.title} ({len(hypo2.hunt_queries)} requêtes)")
    
    # 2. Lancer campagne de chasse
    print("\n🚀 LANCEMENT DE CAMPAGNE DE CHASSE")
    
    campaign = await hunter.launch_hunt_campaign(
        name="Q1 APT Hunting Campaign",
        description="Proactive hunt for APT activities in Q1 2025",
        hypothesis_ids=[hypo1.id, hypo2.id],
        lead_hunter="Alice Cooper",
        team_members=["Bob Wilson", "Carol Smith"],
        scope={
            "time_range": "last_30_days",
            "networks": ["10.0.0.0/8", "192.168.0.0/16"],
            "priority_assets": ["domain_controllers", "file_servers"]
        }
    )
    
    print(f"   🎯 Campagne: {campaign.name}")
    print(f"   📊 Scope: {campaign.scope['networks']}")
    print(f"   👥 Équipe: {len(campaign.team_members)} hunters")
    
    # 3. Simuler données pour hunting
    print("\n📊 SIMULATION DE DONNÉES POUR HUNTING")
    
    data_sources = {
        "windows_logs": [
            {
                "timestamp": "2025-08-18T02:30:00",
                "event_type": "authentication",
                "user": "admin",
                "hostname": "dc01.traffeyere.local",
                "src_ip": "192.168.1.100",
                "auth_result": "success",
                "process_name": "winlogon.exe"
            },
            {
                "timestamp": "2025-08-18T02:31:00",
                "event_type": "process_creation",
                "user": "admin",
                "hostname": "dc01.traffeyere.local",
                "process_name": "powershell.exe",
                "command_line": "powershell -enc JABlAHgAZQBjAC4A..."
            },
            {
                "timestamp": "2025-08-18T02:32:00",
                "event_type": "network_connection",
                "user": "system",
                "hostname": "dc01.traffeyere.local",
                "src_ip": "192.168.1.10",
                "dst_ip": "192.168.1.100",
                "protocol": "RDP",
                "dst_port": 3389
            }
        ],
        "network_logs": [
            {
                "timestamp": "2025-08-18T02:33:00",
                "event_type": "network_connection",
                "src_ip": "192.168.1.100",
                "dst_ip": "malicious.domain.com",
                "dst_port": 443,
                "bytes": 1024,
                "protocol": "HTTPS"
            },
            {
                "timestamp": "2025-08-18T02:34:00", 
                "event_type": "dns_query",
                "src_ip": "192.168.1.100",
                "query": "cozy-bear-c2.com",
                "response": "5.6.7.8"
            }
        ]
    }
    
    print(f"   📝 Sources: {list(data_sources.keys())}")
    print(f"   📊 Events: {sum(len(events) for events in data_sources.values())}")
    
    # 4. Exécuter requêtes de chasse
    print("\n🔍 EXÉCUTION DES REQUÊTES DE CHASSE")
    
    findings = await hunter.execute_hunt_queries(campaign.id, data_sources)
    
    print(f"   🎯 Findings découverts: {len(findings)}")
    for finding in findings:
        print(f"      • {finding.title} (confiance: {finding.confidence_score:.2f})")
        print(f"        Entités affectées: {len(finding.affected_entities)}")
        print(f"        TTPs observés: {finding.ttps_observed}")
    
    # 5. Analyse comportementale
    print("\n🧠 ANALYSE COMPORTEMENTALE")
    
    behavior_profiles = await hunter.analyze_behavioral_anomalies(data_sources)
    
    print(f"   📊 Profils analysés: {len(behavior_profiles)}")
    for profile in behavior_profiles[:3]:  # Top 3
        print(f"      • {profile.entity_id}: anomalie {profile.anomaly_score:.2f}")
        print(f"        Patterns: {profile.behavioral_patterns}")
        print(f"        Risques: {len(profile.risk_indicators)}")
    
    # 6. Attribution APT
    print("\n🎯 ATTRIBUTION APT")
    
    apt_signatures = await hunter.perform_apt_attribution(campaign.id)
    
    print(f"   🕵️ Candidats APT: {len(apt_signatures)}")
    for signature in apt_signatures:
        print(f"      • {signature.apt_group}: confiance {signature.confidence:.2f}")
        print(f"        TTPs matchés: {len(signature.ttps_matched)}")
        print(f"        IOCs matchés: {len(signature.iocs_matched)}")
        print(f"        Comportements: {len(signature.behavioral_matches)}")
    
    # 7. Métriques finales
    print("\n📈 MÉTRIQUES DE THREAT HUNTING")
    
    metrics = hunter.get_hunt_metrics()
    print(f"   🚀 Campagnes actives: {metrics['active_campaigns']}")
    print(f"   🎯 Findings 24h: {metrics['findings_last_24h']}")
    print(f"   🎨 Confiance moyenne: {metrics['average_confidence']:.2f}")
    print(f"   ⚠️ Entités à risque: {metrics['high_risk_entities']}")
    print(f"   🔧 Statut hunter: {metrics['hunter_status']}")
    
    return {
        "campaign": campaign,
        "findings": findings,
        "behavior_profiles": behavior_profiles,
        "apt_signatures": apt_signatures,
        "metrics": metrics
    }

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_advanced_threat_hunter())
