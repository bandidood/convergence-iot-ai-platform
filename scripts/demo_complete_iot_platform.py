"""
🎯 DÉMONSTRATION COMPLÈTE PLATEFORME IoT
Démarrage automatique: Générateur 127 capteurs + Edge AI + Tests Grafana
Compatible RNCP 39394 - Expert en Systèmes d'Information et Sécurité

Auteur: Expert DevSecOps & IA Explicable
Version: 1.0.0
"""

import asyncio
import time
import subprocess
import sys
import os
import signal
import logging
from datetime import datetime
from typing import List, Dict, Optional
import psutil
import requests
import threading

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IoTPlatformDemo:
    """
    Démonstration complète plateforme IoT Station Traffeyère
    Orchestration automatique de tous les composants
    """
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
        # Configuration services
        self.services = {
            'iot_generator': {
                'script': 'scripts/iot_data_generator.py',
                'port': 8090,
                'name': 'Générateur IoT 127 capteurs',
                'process': None,
                'ready': False
            },
            'edge_ai': {
                'script': 'scripts/edge_ai_engine.py', 
                'port': 8091,
                'name': 'Edge AI Engine',
                'process': None,
                'ready': False
            }
        }
        
        logger.info("🎯 Démonstration plateforme IoT initialisée")

    def install_dependencies(self):
        """Installation dépendances Python requises"""
        logger.info("📦 Vérification dépendances Python...")
        
        required_packages = [
            'numpy', 'pandas', 'scikit-learn', 'prometheus-client',
            'asyncio', 'aiohttp', 'requests', 'psutil', 'shap', 'joblib'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"✅ {package} - Installé")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"❌ {package} - Manquant")
        
        if missing_packages:
            logger.info(f"🔧 Installation packages manquants: {', '.join(missing_packages)}")
            try:
                cmd = [sys.executable, '-m', 'pip', 'install'] + missing_packages
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ Toutes les dépendances installées avec succès")
                else:
                    logger.error(f"❌ Erreur installation: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"❌ Impossible d'installer dépendances: {e}")
                return False
        
        return True

    async def check_service_ready(self, service_name: str, max_attempts: int = 30) -> bool:
        """Vérification service prêt"""
        service = self.services[service_name]
        url = f"http://localhost:{service['port']}/metrics"
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    service['ready'] = True
                    logger.info(f"✅ {service['name']} - Prêt (port {service['port']})")
                    return True
            except requests.RequestException:
                pass
            
            await asyncio.sleep(2)
            logger.info(f"⏳ {service['name']} - Démarrage... ({attempt + 1}/{max_attempts})")
        
        logger.error(f"❌ {service['name']} - Timeout après {max_attempts * 2}s")
        return False

    def start_service(self, service_name: str) -> bool:
        """Démarrage service en arrière-plan"""
        service = self.services[service_name]
        script_path = service['script']
        
        if not os.path.exists(script_path):
            logger.error(f"❌ Script non trouvé: {script_path}")
            return False
        
        logger.info(f"🚀 Démarrage {service['name']}...")
        
        try:
            # Démarrage processus Python
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            service['process'] = process
            self.processes.append(process)
            
            logger.info(f"🎯 {service['name']} démarré (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage {service['name']}: {e}")
            return False

    async def start_all_services(self) -> bool:
        """Démarrage séquentiel tous services"""
        logger.info("🚀 Démarrage plateforme IoT complète...")
        
        # 1. Démarrage générateur IoT
        if not self.start_service('iot_generator'):
            return False
            
        if not await self.check_service_ready('iot_generator'):
            return False
        
        # 2. Démarrage Edge AI Engine  
        if not self.start_service('edge_ai'):
            return False
            
        if not await self.check_service_ready('edge_ai'):
            return False
        
        logger.info("🎉 Tous les services sont opérationnels !")
        return True

    def display_service_status(self):
        """Affichage status services"""
        print("\n" + "="*60)
        print("📊 STATUS SERVICES PLATEFORME IoT")
        print("="*60)
        
        for name, service in self.services.items():
            status = "🟢 ACTIF" if service['ready'] else "🔴 ARRÊTÉ"
            port_info = f"Port {service['port']}" if service['ready'] else "N/A"
            pid_info = f"PID {service['process'].pid}" if service['process'] else "N/A"
            
            print(f"{status} {service['name']}")
            print(f"   URL: http://localhost:{service['port']}")
            print(f"   {port_info} | {pid_info}")
            print()

    def display_dashboard_info(self):
        """Information accès dashboards"""
        print("="*60)
        print("🎯 ACCÈS DASHBOARDS & MÉTRIQUES")
        print("="*60)
        print("📊 Générateur IoT (127 capteurs):")
        print("   • Métriques: http://localhost:8090/metrics")
        print("   • 20+ types de capteurs différents")
        print("   • Données temps réel toutes les 5 secondes")
        print()
        print("🤖 Edge AI Engine:")
        print("   • Métriques: http://localhost:8091/metrics")
        print("   • Latence P95 < 0.28ms (objectif RNCP)")
        print("   • Détection anomalies + explicabilité SHAP")
        print()
        print("📈 Intégration Prometheus/Grafana:")
        print("   • Prometheus: http://localhost:9090")
        print("   • Grafana: http://localhost:3000")
        print("   • Dashboard principal: 11 panneaux configurés")
        print()

    def display_demo_commands(self):
        """Commandes démonstration disponibles"""
        print("="*60)
        print("🎮 COMMANDES DÉMONSTRATION")
        print("="*60)
        print("📊 Tests & Validation:")
        print("   python scripts/test_full_integration_grafana.py")
        print("   • Validation complète pipeline IoT → Prometheus → Grafana")
        print("   • 8 tests automatisés incluant métriques RNCP 39394")
        print()
        print("🧪 Scripts supplémentaires:")
        print("   python scripts/validate_performance_thresholds.py")
        print("   python scripts/validate_security_thresholds.py") 
        print("   python scripts/test_monitoring_stack.py")
        print()
        print("⏹️ Arrêt plateforme: Ctrl+C dans ce terminal")
        print("="*60)

    async def monitor_services(self):
        """Monitoring continu services"""
        logger.info("👁️ Démarrage monitoring services...")
        
        while self.running:
            try:
                # Vérification santé services
                for name, service in self.services.items():
                    if service['process'] and service['process'].poll() is None:
                        # Service en cours
                        try:
                            response = requests.get(f"http://localhost:{service['port']}/metrics", timeout=2)
                            if response.status_code != 200:
                                logger.warning(f"⚠️ {service['name']} - Réponse anormale")
                        except requests.RequestException:
                            logger.warning(f"⚠️ {service['name']} - Pas de réponse")
                    else:
                        if service['ready']:  # Était actif avant
                            logger.error(f"❌ {service['name']} - Processus terminé")
                            service['ready'] = False
                
                await asyncio.sleep(30)  # Check toutes les 30s
                
            except Exception as e:
                logger.error(f"❌ Erreur monitoring: {e}")
                await asyncio.sleep(10)

    def cleanup_services(self):
        """Nettoyage processes à l'arrêt"""
        logger.info("🧹 Arrêt services en cours...")
        
        self.running = False
        
        for name, service in self.services.items():
            if service['process']:
                try:
                    logger.info(f"🛑 Arrêt {service['name']} (PID: {service['process'].pid})")
                    service['process'].terminate()
                    
                    # Attente arrêt gracieux
                    try:
                        service['process'].wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"⚡ Forçage arrêt {service['name']}")
                        service['process'].kill()
                        service['process'].wait()
                        
                    logger.info(f"✅ {service['name']} arrêté")
                except Exception as e:
                    logger.error(f"❌ Erreur arrêt {service['name']}: {e}")

    def signal_handler(self, signum, frame):
        """Gestionnaire signal arrêt"""
        logger.info("🛑 Signal arrêt reçu")
        self.cleanup_services()
        sys.exit(0)

async def main():
    """Fonction principale démonstration"""
    print("🎯 DÉMONSTRATION PLATEFORME IoT - STATION TRAFFEYÈRE")
    print("=" * 70)
    print("🏭 127 capteurs IoT avec données temps réel")
    print("🤖 Edge AI Engine - Latence P95 < 0.28ms")  
    print("📊 Intégration Prometheus + Grafana")
    print("🔐 Détection anomalies + explicabilité SHAP")
    print("✅ Conformité RNCP 39394")
    print("=" * 70)
    
    # Initialisation démo
    demo = IoTPlatformDemo()
    
    # Gestion signaux arrêt
    signal.signal(signal.SIGINT, demo.signal_handler)
    signal.signal(signal.SIGTERM, demo.signal_handler)
    
    try:
        # 1. Installation dépendances
        print("\n🔧 Phase 1: Vérification environnement...")
        if not demo.install_dependencies():
            logger.error("❌ Impossible d'installer dépendances")
            return
        
        # 2. Démarrage services
        print("\n🚀 Phase 2: Démarrage services...")
        if not await demo.start_all_services():
            logger.error("❌ Échec démarrage services")
            demo.cleanup_services()
            return
        
        # 3. Affichage informations
        demo.display_service_status()
        demo.display_dashboard_info()
        demo.display_demo_commands()
        
        print("\n🎉 PLATEFORME IoT OPÉRATIONNELLE !")
        print("📊 Génération données en cours...")
        print("🤖 Edge AI Engine actif")
        print("📈 Métriques disponibles sur Prometheus/Grafana")
        print("\n⏳ Laissez tourner quelques minutes pour accumulation données...")
        print("🧪 Puis lancez les tests d'intégration !")
        
        # 4. Monitoring continu
        await demo.monitor_services()
        
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}")
    finally:
        demo.cleanup_services()
        logger.info("📊 Démonstration terminée")

if __name__ == "__main__":
    asyncio.run(main())
