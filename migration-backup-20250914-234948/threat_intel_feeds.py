#!/usr/bin/env python3
"""
📡 THREAT INTELLIGENCE FEEDS
Station Traffeyère IoT AI Platform - RNCP 39394 Semaine 6

Intégration ANSSI, MISP, VirusTotal et feeds de renseignement
Enrichissement automatique des incidents
"""

import asyncio
import aiohttp
import json
import sqlite3
from datetime import datetime, timedelta
import hashlib
import logging
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger('ThreatIntelFeeds')

class ThreatIntelligenceManager:
    """Gestionnaire des flux de Threat Intelligence"""
    
    def __init__(self, db_path: str = "threat_intelligence.db"):
        self.db_path = db_path
        self.feeds_config = self._setup_feeds_configuration()
        self.indicators_cache = {}
        self._setup_database()
        
    def _setup_feeds_configuration(self) -> Dict[str, Dict[str, Any]]:
        """Configuration des flux de renseignement"""
        return {
            'anssi_cert_fr': {
                'name': 'ANSSI CERT-FR',
                'url': 'https://www.cert.ssi.gouv.fr/feeds/',
                'format': 'json',
                'update_interval': 3600,  # 1 heure
                'classification': 'TLP:WHITE',
                'categories': ['malware', 'vulnerability', 'phishing', 'apt']
            },
            'misp_local': {
                'name': 'MISP Local Instance',
                'url': 'http://localhost:8080/events/restSearch',
                'format': 'json',
                'update_interval': 1800,  # 30 minutes
                'classification': 'TLP:AMBER',
                'api_key': 'demo-api-key-misp-2024'
            },
            'virustotal': {
                'name': 'VirusTotal Intelligence',
                'url': 'https://www.virustotal.com/vtapi/v2/',
                'format': 'json',
                'update_interval': 7200,  # 2 heures
                'classification': 'TLP:GREEN',
                'api_key': 'demo-vt-api-key'
            },
            'otx_alienvault': {
                'name': 'AlienVault OTX',
                'url': 'https://otx.alienvault.com/api/v1/indicators/',
                'format': 'json',
                'update_interval': 3600,
                'classification': 'TLP:WHITE'
            },
            'cisa_known_exploited': {
                'name': 'CISA Known Exploited Vulnerabilities',
                'url': 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json',
                'format': 'json',
                'update_interval': 86400,  # 24 heures
                'classification': 'TLP:WHITE'
            }
        }
    
    def _setup_database(self):
        """Initialiser la base de données de Threat Intelligence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des indicateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threat_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator_type TEXT NOT NULL,
                indicator_value TEXT NOT NULL UNIQUE,
                threat_type TEXT,
                severity TEXT,
                confidence INTEGER,
                source TEXT,
                classification TEXT,
                description TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                tags TEXT,
                metadata TEXT
            )
        ''')
        
        # Table des campagnes d'attaque
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attack_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_name TEXT UNIQUE,
                apt_group TEXT,
                first_observed TIMESTAMP,
                last_activity TIMESTAMP,
                targets TEXT,
                ttps TEXT,
                indicators TEXT,
                description TEXT
            )
        ''')
        
        # Table des mises à jour des feeds
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feed_updates (
                feed_name TEXT PRIMARY KEY,
                last_update TIMESTAMP,
                indicators_count INTEGER,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def update_all_feeds(self):
        """Mettre à jour tous les flux de renseignement"""
        logger.info("🔄 Mise à jour des flux Threat Intelligence")
        
        update_tasks = []
        for feed_name, config in self.feeds_config.items():
            task = asyncio.create_task(self._update_feed(feed_name, config))
            update_tasks.append(task)
        
        results = await asyncio.gather(*update_tasks, return_exceptions=True)
        
        successful_updates = 0
        for i, result in enumerate(results):
            feed_name = list(self.feeds_config.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"❌ Échec mise à jour {feed_name}: {result}")
            else:
                successful_updates += 1
                logger.info(f"✅ Feed {feed_name} mis à jour: {result} indicateurs")
        
        logger.info(f"📊 Mise à jour terminée: {successful_updates}/{len(self.feeds_config)} feeds")
        return successful_updates
    
    async def _update_feed(self, feed_name: str, config: Dict[str, Any]) -> int:
        """Mettre à jour un flux spécifique"""
        
        # Simuler la récupération de données (en production, requête HTTP réelle)
        indicators = await self._fetch_feed_data(feed_name, config)
        
        # Stocker les indicateurs
        stored_count = self._store_indicators(feed_name, indicators)
        
        # Mettre à jour le statut du feed
        self._update_feed_status(feed_name, stored_count)
        
        return stored_count
    
    async def _fetch_feed_data(self, feed_name: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Récupérer les données d'un flux (simulation)"""
        
        # Données simulées basées sur les feeds réels
        simulated_data = {
            'anssi_cert_fr': [
                {
                    'type': 'domain',
                    'value': 'malicious-station-attack.com',
                    'threat_type': 'malware_c2',
                    'severity': 'high',
                    'confidence': 90,
                    'description': 'Domaine C&C utilisé pour attaques ciblées stations de traitement'
                },
                {
                    'type': 'ip',
                    'value': '185.220.101.45',
                    'threat_type': 'exploitation',
                    'severity': 'critical',
                    'confidence': 95,
                    'description': 'IP source attaques sur infrastructure critique française'
                },
                {
                    'type': 'hash',
                    'value': 'a1b2c3d4e5f6789012345678901234567890abcd',
                    'threat_type': 'malware',
                    'severity': 'high',
                    'confidence': 85,
                    'description': 'Malware ciblant systèmes SCADA stations eau'
                }
            ],
            'misp_local': [
                {
                    'type': 'email',
                    'value': 'admin@traffeyere-fake.com',
                    'threat_type': 'phishing',
                    'severity': 'medium',
                    'confidence': 75,
                    'description': 'Email phishing imitant domaine station Traffeyère',
                    'tags': ['spearphishing', 'social_engineering']
                },
                {
                    'type': 'url',
                    'value': 'http://traffeyere-admin-portal.tk/login',
                    'threat_type': 'credential_harvesting',
                    'severity': 'high',
                    'confidence': 80,
                    'description': 'Site frauduleux collecte identifiants station'
                }
            ],
            'virustotal': [
                {
                    'type': 'hash',
                    'value': 'def456789abc012345678901234567890abcdef12',
                    'threat_type': 'trojan',
                    'severity': 'high',
                    'confidence': 90,
                    'description': 'Trojan détecté ciblant systèmes de contrôle industriel'
                }
            ],
            'otx_alienvault': [
                {
                    'type': 'ip',
                    'value': '192.168.100.200',
                    'threat_type': 'scanning',
                    'severity': 'medium',
                    'confidence': 70,
                    'description': 'IP effectuant scan réseau infrastructure eau'
                }
            ],
            'cisa_known_exploited': [
                {
                    'type': 'cve',
                    'value': 'CVE-2024-8888',
                    'threat_type': 'vulnerability',
                    'severity': 'critical',
                    'confidence': 100,
                    'description': 'Vulnérabilité critique SCADA exploitée activement'
                }
            ]
        }
        
        # Simuler délai réseau
        await asyncio.sleep(0.5)
        
        return simulated_data.get(feed_name, [])
    
    def _store_indicators(self, source: str, indicators: List[Dict[str, Any]]) -> int:
        """Stocker les indicateurs dans la base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stored_count = 0
        
        for indicator in indicators:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO threat_indicators 
                    (indicator_type, indicator_value, threat_type, severity, confidence, 
                     source, classification, description, first_seen, last_seen, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    indicator['type'],
                    indicator['value'],
                    indicator.get('threat_type', 'unknown'),
                    indicator.get('severity', 'medium'),
                    indicator.get('confidence', 50),
                    source,
                    self.feeds_config[source].get('classification', 'TLP:WHITE'),
                    indicator.get('description', ''),
                    datetime.now(),
                    datetime.now(),
                    json.dumps(indicator.get('tags', [])),
                    json.dumps(indicator.get('metadata', {}))
                ))
                stored_count += 1
                
            except sqlite3.Error as e:
                logger.warning(f"⚠️  Erreur stockage indicateur {indicator['value']}: {e}")
        
        conn.commit()
        conn.close()
        
        return stored_count
    
    def _update_feed_status(self, feed_name: str, indicators_count: int):
        """Mettre à jour le statut d'un feed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO feed_updates 
            (feed_name, last_update, indicators_count, status)
            VALUES (?, ?, ?, ?)
        ''', (feed_name, datetime.now(), indicators_count, 'success'))
        
        conn.commit()
        conn.close()
    
    async def enrich_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichir un incident avec Threat Intelligence"""
        enriched = incident_data.copy()
        
        # Extraire les indicateurs de l'incident
        indicators_to_check = self._extract_indicators(incident_data)
        
        threat_matches = []
        for indicator in indicators_to_check:
            matches = self._query_indicator(indicator['type'], indicator['value'])
            if matches:
                threat_matches.extend(matches)
        
        # Enrichir avec les correspondances
        if threat_matches:
            enriched['threat_intelligence'] = {
                'matches_found': len(threat_matches),
                'max_severity': max(match.get('severity', 'low') for match in threat_matches),
                'threat_types': list(set(match.get('threat_type') for match in threat_matches)),
                'sources': list(set(match.get('source') for match in threat_matches)),
                'indicators': threat_matches[:5]  # Limiter à 5 pour lisibilité
            }
            
            # Calculer score de risque
            severity_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            avg_confidence = sum(match.get('confidence', 50) for match in threat_matches) / len(threat_matches)
            max_severity_score = max(severity_scores.get(match.get('severity', 'low'), 1) for match in threat_matches)
            
            enriched['risk_score'] = min(100, (max_severity_score * 20) + (avg_confidence * 0.3))
            
            logger.info(f"📊 Incident enrichi: {len(threat_matches)} correspondances, score risque: {enriched['risk_score']:.1f}")
        
        return enriched
    
    def _extract_indicators(self, incident_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extraire les indicateurs d'un incident"""
        indicators = []
        
        # IP sources/destinations
        for ip_field in ['source_ip', 'destination_ip', 'remote_ip']:
            if ip_field in incident_data:
                indicators.append({'type': 'ip', 'value': incident_data[ip_field]})
        
        # Domaines/URLs
        for url_field in ['url', 'domain', 'hostname']:
            if url_field in incident_data:
                indicators.append({'type': 'domain', 'value': incident_data[url_field]})
        
        # Hashes de fichiers
        for hash_field in ['file_hash', 'md5', 'sha1', 'sha256']:
            if hash_field in incident_data:
                indicators.append({'type': 'hash', 'value': incident_data[hash_field]})
        
        # Emails
        for email_field in ['sender_email', 'recipient_email', 'email']:
            if email_field in incident_data:
                indicators.append({'type': 'email', 'value': incident_data[email_field]})
        
        return indicators
    
    def _query_indicator(self, indicator_type: str, indicator_value: str) -> List[Dict[str, Any]]:
        """Rechercher un indicateur dans la base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM threat_indicators 
            WHERE indicator_type = ? AND indicator_value = ?
        ''', (indicator_type, indicator_value))
        
        rows = cursor.fetchall()
        conn.close()
        
        matches = []
        for row in rows:
            matches.append({
                'indicator_type': row[1],
                'indicator_value': row[2],
                'threat_type': row[3],
                'severity': row[4],
                'confidence': row[5],
                'source': row[6],
                'description': row[8]
            })
        
        return matches
    
    def get_statistics(self) -> Dict[str, Any]:
        """Statistiques Threat Intelligence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Compter indicateurs par type
        cursor.execute('''
            SELECT indicator_type, COUNT(*) 
            FROM threat_indicators 
            GROUP BY indicator_type
        ''')
        indicators_by_type = dict(cursor.fetchall())
        
        # Compter indicateurs par source
        cursor.execute('''
            SELECT source, COUNT(*) 
            FROM threat_indicators 
            GROUP BY source
        ''')
        indicators_by_source = dict(cursor.fetchall())
        
        # Compter indicateurs par sévérité
        cursor.execute('''
            SELECT severity, COUNT(*) 
            FROM threat_indicators 
            GROUP BY severity
        ''')
        indicators_by_severity = dict(cursor.fetchall())
        
        # Total indicateurs
        cursor.execute('SELECT COUNT(*) FROM threat_indicators')
        total_indicators = cursor.fetchone()[0]
        
        # Statut des feeds
        cursor.execute('SELECT * FROM feed_updates')
        feed_status = []
        for row in cursor.fetchall():
            feed_status.append({
                'name': row[0],
                'last_update': row[1],
                'indicators_count': row[2],
                'status': row[3]
            })
        
        conn.close()
        
        return {
            'total_indicators': total_indicators,
            'indicators_by_type': indicators_by_type,
            'indicators_by_source': indicators_by_source,
            'indicators_by_severity': indicators_by_severity,
            'feeds_status': feed_status,
            'active_feeds': len(self.feeds_config)
        }

# Test et démonstration
async def test_threat_intelligence():
    """Test complet du système Threat Intelligence"""
    ti_manager = ThreatIntelligenceManager()
    
    print("📡 TEST THREAT INTELLIGENCE - Station Traffeyère")
    print("=" * 55)
    
    # Mise à jour des feeds
    print("\n🔄 Mise à jour des flux...")
    updated_feeds = await ti_manager.update_all_feeds()
    print(f"✅ {updated_feeds} feeds mis à jour")
    
    # Test enrichissement incidents
    test_incidents = [
        {
            'incident_id': 'INC-001',
            'type': 'suspicious_connection',
            'source_ip': '185.220.101.45',  # IP malicieuse des feeds
            'destination_ip': '10.1.0.100'
        },
        {
            'incident_id': 'INC-002', 
            'type': 'malware_detection',
            'file_hash': 'a1b2c3d4e5f6789012345678901234567890abcd'  # Hash malicieux
        },
        {
            'incident_id': 'INC-003',
            'type': 'phishing_attempt',
            'sender_email': 'admin@traffeyere-fake.com',  # Email malicieux
            'url': 'http://traffeyere-admin-portal.tk/login'
        }
    ]
    
    print("\n🔍 Test enrichissement incidents...")
    enriched_incidents = []
    
    for incident in test_incidents:
        enriched = await ti_manager.enrich_incident(incident)
        enriched_incidents.append(enriched)
        
        print(f"\n📋 Incident {incident['incident_id']}:")
        if 'threat_intelligence' in enriched:
            ti = enriched['threat_intelligence']
            print(f"   🎯 Correspondances: {ti['matches_found']}")
            print(f"   🚨 Sévérité max: {ti['max_severity']}")
            print(f"   📊 Score risque: {enriched.get('risk_score', 0):.1f}/100")
            print(f"   📡 Sources: {', '.join(ti['sources'])}")
        else:
            print("   ℹ️  Aucune correspondance threat intelligence")
    
    # Statistiques
    print("\n📈 STATISTIQUES THREAT INTELLIGENCE:")
    stats = ti_manager.get_statistics()
    print(f"   Total indicateurs: {stats['total_indicators']}")
    print(f"   Feeds actifs: {stats['active_feeds']}")
    print(f"   Types d'indicateurs: {stats['indicators_by_type']}")
    print(f"   Répartition sévérité: {stats['indicators_by_severity']}")
    
    return enriched_incidents, stats

if __name__ == "__main__":
    asyncio.run(test_threat_intelligence())
