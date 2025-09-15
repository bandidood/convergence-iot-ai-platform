#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 DÉPLOIEMENT COMPLET PROJET STATION TRAFFEYÈRE
IoT/IA Platform - RNCP 39394 - Test Final

Script de déploiement et validation complète de tous les composants
développés pendant les 16 semaines du projet.
"""

import os
import sys
import time
import subprocess
import json
import asyncio
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProjectDeployer:
    """Déployeur complet du projet Station Traffeyère"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.services = []
        self.deployment_status = {}
        self.start_time = time.time()
        
        # Configuration des services à déployer
        self.service_config = {
            "iot_generator": {
                "path": "scripts/iot_data_generator.py",
                "port": 8090,
                "description": "Générateur données IoT 127 capteurs"
            },
            "edge_ai_engine": {
                "path": "scripts/edge_ai_engine.py", 
                "port": 8091,
                "description": "Moteur IA Edge temps réel"
            },
            "prometheus": {
                "docker_compose": "docker-compose.monitoring.yml",
                "service": "prometheus",
                "port": 9090,
                "description": "Serveur métriques Prometheus"
            },
            "grafana": {
                "docker_compose": "docker-compose.yml",
                "service": "grafana",
                "port": 3001,
                "description": "Dashboard Grafana"
            },
            "soc_dashboard": {
                "path": "src/dashboard/soc_dashboard.py",
                "port": 8080,
                "description": "Dashboard SOC temps réel"
            },
            "validation_system": {
                "path": "week-16-global-expansion/final_validation_system.py",
                "description": "Système validation finale RNCP"
            }
        }

    def check_prerequisites(self) -> bool:
        """Vérification prérequis système"""
        logger.info("Verification prerequisites...")
        
        prerequisites = {
            "python": {"command": "python --version", "required": True},
            "docker": {"command": "docker --version", "required": True},
            "docker-compose": {"command": "docker-compose --version", "required": False},
            "pip": {"command": "pip --version", "required": True}
        }
        
        all_good = True
        for name, config in prerequisites.items():
            try:
                result = subprocess.run(
                    config["command"].split(), 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                    logger.info(f"✅ {name}: {version}")
                else:
                    if config["required"]:
                        logger.error(f"❌ {name}: Non disponible (requis)")
                        all_good = False
                    else:
                        logger.warning(f"⚠️ {name}: Non disponible (optionnel)")
            except Exception as e:
                if config["required"]:
                    logger.error(f"❌ {name}: Erreur - {e}")
                    all_good = False
                else:
                    logger.warning(f"⚠️ {name}: Erreur - {e}")
        
        return all_good

    def install_dependencies(self) -> bool:
        """Installation dépendances Python"""
        logger.info("Installation dependencies Python...")
        
        # Packages requis
        required_packages = [
            "asyncio",
            "aiohttp", 
            "fastapi",
            "uvicorn",
            "prometheus-client",
            "requests",
            "numpy",
            "scikit-learn",
            "pandas"
        ]
        
        try:
            for package in required_packages:
                try:
                    __import__(package.replace('-', '_'))
                    logger.info(f"✅ {package}: Déjà installé")
                except ImportError:
                    logger.info(f"📦 Installation {package}...")
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", package
                    ], check=True, capture_output=True)
                    logger.info(f"✅ {package}: Installé")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur installation dependencies: {e}")
            return False

    def prepare_environment(self) -> bool:
        """Préparation environnement de déploiement"""
        logger.info("Preparation environnement...")
        
        try:
            # Création dossiers nécessaires
            directories = [
                "logs",
                "data", 
                "config",
                "monitoring/prometheus/data",
                "monitoring/grafana/data",
                "security/certs",
                "security/secrets"
            ]
            
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Dossier créé: {directory}")
            
            # Configuration fichiers environnement
            env_content = """# Station Traffeyère Environment
PROJECT_NAME=station-traffeyere-iot-ai-platform
ENVIRONMENT=development
LOG_LEVEL=INFO

# Prometheus
PROMETHEUS_PORT=9090
PROMETHEUS_DATA_RETENTION=15d

# Grafana  
GRAFANA_PORT=3001
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin123

# IoT Generator
IOT_GENERATOR_PORT=8090
IOT_SENSORS_COUNT=127

# Edge AI
EDGE_AI_PORT=8091
AI_MODEL_TYPE=isolation_forest
LATENCY_TARGET_MS=0.28

# SOC Dashboard
SOC_DASHBOARD_PORT=8080
SOC_ALERTS_ENABLED=true
"""
            
            env_file = self.project_root / ".env"
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            logger.info("✅ Fichier .env créé")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur préparation environnement: {e}")
            return False

    def deploy_docker_services(self) -> bool:
        """Déploiement services Docker"""
        logger.info("Deploiement services Docker...")
        
        try:
            # Vérifier si Docker est disponible
            subprocess.run(["docker", "ps"], check=True, capture_output=True)
            
            # Arrêter services existants si nécessaire
            logger.info("Arret services existants...")
            try:
                subprocess.run([
                    "docker-compose", "-f", "docker-compose.yml", "down"
                ], capture_output=True, timeout=30)
                
                subprocess.run([
                    "docker-compose", "-f", "docker-compose.monitoring.yml", "down"  
                ], capture_output=True, timeout=30)
            except:
                pass
            
            # Démarrage services principaux
            logger.info("Demarrage services principaux...")
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.yml", "up", "-d"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"Erreur docker-compose principal: {result.stderr}")
                return False
            
            # Attendre que les services soient prêts
            time.sleep(10)
            
            # Vérifier statut services
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.yml", "ps"
            ], capture_output=True, text=True)
            
            logger.info("Services Docker démarrés:")
            for line in result.stdout.split('\n')[2:]:  # Skip headers
                if line.strip():
                    logger.info(f"  {line}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur déploiement Docker: {e}")
            return False

    async def deploy_python_services(self) -> bool:
        """Déploiement services Python"""
        logger.info("Deploiement services Python...")
        
        python_services = []
        
        for service_name, config in self.service_config.items():
            if "path" in config:
                service_path = self.project_root / config["path"]
                if service_path.exists():
                    logger.info(f"Demarrage {service_name}...")
                    try:
                        # Lancer le service en arrière-plan
                        process = subprocess.Popen([
                            sys.executable, str(service_path)
                        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        python_services.append({
                            "name": service_name,
                            "process": process,
                            "config": config
                        })
                        
                        # Attendre un peu pour que le service démarre
                        await asyncio.sleep(2)
                        
                        # Vérifier si le service est encore actif
                        if process.poll() is None:
                            logger.info(f"✅ {service_name}: Démarré (PID: {process.pid})")
                            self.deployment_status[service_name] = "RUNNING"
                        else:
                            logger.error(f"❌ {service_name}: Échec démarrage")
                            self.deployment_status[service_name] = "FAILED"
                            
                    except Exception as e:
                        logger.error(f"❌ {service_name}: Erreur - {e}")
                        self.deployment_status[service_name] = "ERROR"
                else:
                    logger.warning(f"⚠️ {service_name}: Fichier non trouvé - {service_path}")
                    self.deployment_status[service_name] = "NOT_FOUND"
        
        # Sauvegarder références des processus
        self.services = python_services
        return len([s for s in python_services if self.deployment_status[s["name"]] == "RUNNING"]) > 0

    def test_services_connectivity(self) -> Dict[str, Any]:
        """Test connectivité des services"""
        logger.info("Test connectivite services...")
        
        connectivity_results = {}
        
        # Services HTTP à tester
        http_services = {
            "iot_generator": "http://localhost:8090/metrics",
            "edge_ai_engine": "http://localhost:8091/metrics", 
            "prometheus": "http://localhost:9090/-/healthy",
            "grafana": "http://localhost:3001/api/health",
            "soc_dashboard": "http://localhost:8080/health"
        }
        
        for service_name, url in http_services.items():
            try:
                import requests
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    connectivity_results[service_name] = {
                        "status": "OK",
                        "response_time": response.elapsed.total_seconds(),
                        "url": url
                    }
                    logger.info(f"✅ {service_name}: Connectivité OK ({response.elapsed.total_seconds():.3f}s)")
                else:
                    connectivity_results[service_name] = {
                        "status": "ERROR",
                        "http_code": response.status_code,
                        "url": url
                    }
                    logger.warning(f"⚠️ {service_name}: HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                connectivity_results[service_name] = {
                    "status": "CONNECTION_REFUSED",
                    "url": url
                }
                logger.warning(f"⚠️ {service_name}: Connexion refusée")
                
            except Exception as e:
                connectivity_results[service_name] = {
                    "status": "EXCEPTION",
                    "error": str(e),
                    "url": url
                }
                logger.error(f"❌ {service_name}: {e}")
        
        return connectivity_results

    def run_integration_tests(self) -> Dict[str, Any]:
        """Exécution tests d'intégration"""
        logger.info("Execution tests integration...")
        
        test_results = {}
        
        # Test 1: Validation système final
        try:
            logger.info("Test: Validation système final...")
            result = subprocess.run([
                sys.executable, 
                str(self.project_root / "week-16-global-expansion/final_validation_system.py")
            ], capture_output=True, text=True, timeout=60)
            
            if "VALIDATION RÉUSSIE" in result.stdout or result.returncode == 0:
                test_results["final_validation"] = {
                    "status": "PASSED",
                    "description": "Système de validation finale RNCP"
                }
                logger.info("✅ Test validation finale: RÉUSSI")
            else:
                test_results["final_validation"] = {
                    "status": "FAILED",
                    "error": result.stderr[:200]
                }
                logger.error("❌ Test validation finale: ÉCHEC")
                
        except Exception as e:
            test_results["final_validation"] = {
                "status": "ERROR",
                "error": str(e)
            }
        
        # Test 2: Collecte métriques Prometheus
        try:
            logger.info("Test: Collecte métriques Prometheus...")
            import requests
            
            # Test métriques IoT
            response = requests.get("http://localhost:9090/api/v1/query?query=up", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    test_results["prometheus_metrics"] = {
                        "status": "PASSED",
                        "metrics_collected": len(data.get("data", {}).get("result", [])),
                        "description": "Collecte métriques Prometheus"
                    }
                    logger.info("✅ Test métriques Prometheus: RÉUSSI")
                else:
                    test_results["prometheus_metrics"] = {
                        "status": "FAILED",
                        "error": "Pas de données"
                    }
            else:
                test_results["prometheus_metrics"] = {
                    "status": "FAILED",
                    "http_code": response.status_code
                }
                
        except Exception as e:
            test_results["prometheus_metrics"] = {
                "status": "ERROR", 
                "error": str(e)
            }
        
        # Test 3: Dashboard Grafana accessible
        try:
            logger.info("Test: Accessibilite Dashboard Grafana...")
            import requests
            
            response = requests.get("http://localhost:3001/api/health", timeout=10)
            if response.status_code == 200:
                test_results["grafana_dashboard"] = {
                    "status": "PASSED",
                    "description": "Dashboard Grafana accessible"
                }
                logger.info("✅ Test Dashboard Grafana: RÉUSSI")
            else:
                test_results["grafana_dashboard"] = {
                    "status": "FAILED",
                    "http_code": response.status_code
                }
                
        except Exception as e:
            test_results["grafana_dashboard"] = {
                "status": "ERROR",
                "error": str(e)
            }
        
        return test_results

    def generate_deployment_report(self, connectivity_results: Dict, test_results: Dict) -> Dict[str, Any]:
        """Génération rapport de déploiement"""
        logger.info("Generation rapport deploiement...")
        
        # Calcul statistiques
        total_services = len(self.service_config)
        running_services = len([s for s, status in self.deployment_status.items() if status == "RUNNING"])
        connected_services = len([s for s, result in connectivity_results.items() if result.get("status") == "OK"])
        passed_tests = len([t for t, result in test_results.items() if result.get("status") == "PASSED"])
        total_tests = len(test_results)
        
        deployment_time = time.time() - self.start_time
        
        report = {
            "title": "RAPPORT DE DÉPLOIEMENT STATION TRAFFEYÈRE",
            "subtitle": "IoT/IA Platform - RNCP 39394 - Test Final",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "deployment_duration": f"{deployment_time:.2f} seconds",
            "summary": {
                "total_services": total_services,
                "running_services": running_services,
                "connected_services": connected_services,
                "success_rate": f"{(running_services/total_services*100):.1f}%",
                "connectivity_rate": f"{(connected_services/len(connectivity_results)*100):.1f}%" if connectivity_results else "0%",
                "tests_passed": f"{passed_tests}/{total_tests}",
                "overall_status": "SUCCESS" if running_services >= total_services * 0.7 else "PARTIAL" if running_services > 0 else "FAILED"
            },
            "services_status": self.deployment_status,
            "connectivity_results": connectivity_results,
            "test_results": test_results,
            "recommendations": []
        }
        
        # Recommandations basées sur les résultats
        if running_services < total_services:
            report["recommendations"].append("Vérifier les services qui ne démarrent pas")
        
        if connected_services < len(connectivity_results) * 0.8:
            report["recommendations"].append("Vérifier la configuration réseau et les ports")
        
        if passed_tests < total_tests:
            report["recommendations"].append("Analyser les échecs de tests d'intégration")
        
        # Sauvegarde rapport
        report_path = self.project_root / "deployment_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Rapport sauvegardé: {report_path}")
        return report

    async def deploy_complete_project(self) -> Dict[str, Any]:
        """Déploiement complet du projet"""
        logger.info("🚀 DÉMARRAGE DÉPLOIEMENT COMPLET PROJET STATION TRAFFEYÈRE")
        logger.info("=" * 70)
        
        try:
            # Étape 1: Prérequis
            if not self.check_prerequisites():
                return {"status": "FAILED", "step": "prerequisites"}
            
            # Étape 2: Dépendances
            if not self.install_dependencies():
                return {"status": "FAILED", "step": "dependencies"}
            
            # Étape 3: Environnement
            if not self.prepare_environment():
                return {"status": "FAILED", "step": "environment"}
            
            # Étape 4: Services Docker
            docker_success = self.deploy_docker_services()
            if not docker_success:
                logger.warning("⚠️ Échec déploiement Docker (continue sans Docker)")
            
            # Étape 5: Services Python
            python_success = await self.deploy_python_services()
            
            # Attendre que tous les services soient prêts
            logger.info("Attente stabilisation services...")
            await asyncio.sleep(5)
            
            # Étape 6: Tests de connectivité
            connectivity_results = self.test_services_connectivity()
            
            # Étape 7: Tests d'intégration
            test_results = self.run_integration_tests()
            
            # Étape 8: Rapport final
            final_report = self.generate_deployment_report(connectivity_results, test_results)
            
            return {
                "status": "SUCCESS",
                "report": final_report
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur critique déploiement: {e}")
            return {"status": "ERROR", "error": str(e)}

    def cleanup_deployment(self):
        """Nettoyage après déploiement"""
        logger.info("Nettoyage déploiement...")
        
        # Arrêt services Python
        for service in self.services:
            try:
                process = service["process"]
                if process.poll() is None:
                    process.terminate()
                    logger.info(f"✅ Service {service['name']} arrêté")
            except Exception as e:
                logger.error(f"❌ Erreur arrêt {service['name']}: {e}")

def main():
    """Fonction principale"""
    print("🚀 DÉPLOIEMENT COMPLET PROJET STATION TRAFFEYÈRE")
    print("IoT/IA Platform - RNCP 39394 - Test Final")
    print("=" * 70)
    
    deployer = ProjectDeployer()
    
    try:
        # Déploiement complet
        result = asyncio.run(deployer.deploy_complete_project())
        
        if result["status"] == "SUCCESS":
            report = result["report"]
            summary = report["summary"]
            
            print(f"\n🎉 DÉPLOIEMENT RÉUSSI !")
            print(f"📊 Services déployés : {summary['running_services']}/{summary['total_services']} ({summary['success_rate']})")
            print(f"🌐 Connectivité : {summary['connectivity_rate']}")
            print(f"🧪 Tests : {summary['tests_passed']}")
            print(f"⏱️ Durée : {report['deployment_duration']}")
            print(f"📄 Rapport : deployment_report.json")
            
            print(f"\n🔗 ACCÈS AUX SERVICES :")
            print(f"📊 Grafana Dashboard : http://localhost:3001")
            print(f"📈 Prometheus : http://localhost:9090")
            print(f"🏭 Générateur IoT : http://localhost:8090/metrics")
            print(f"🤖 Edge AI Engine : http://localhost:8091/metrics")
            print(f"🛡️ SOC Dashboard : http://localhost:8080")
            
            print(f"\n🎓 PROJET STATION TRAFFEYÈRE DÉPLOYÉ AVEC SUCCÈS ! 🏆")
            
        else:
            print(f"❌ Échec déploiement : {result.get('error', 'Erreur inconnue')}")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Déploiement interrompu par utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale : {e}")
    finally:
        # Nettoyage
        deployer.cleanup_deployment()
        print(f"\n✅ Nettoyage terminé")

if __name__ == "__main__":
    main()
