#!/usr/bin/env python3
"""
Station Traffeyère Digital Twin - Health Check
RNCP 39394 - Script de vérification santé conteneur
Conformité Docker best practices et ISA/IEC 62443
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import socket
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class HealthChecker:
    """Vérificateur de santé pour Digital Twin Unity"""
    
    def __init__(self):
        self.api_port = int(os.getenv('API_PORT', 8080))
        self.web_port = int(os.getenv('WEB_PORT', 8081))
        self.mqtt_host = os.getenv('MQTT_BROKER_HOST', 'mqtt-broker')
        self.mqtt_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        self.redis_host = os.getenv('REDIS_HOST', 'redis')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        
        self.checks = []
        self.critical_failures = []
        self.warnings = []
    
    def log(self, level: str, message: str):
        """Logging formaté"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{level}] {timestamp} - {message}")
    
    def check_port(self, host: str, port: int, service_name: str, critical: bool = True) -> bool:
        """Vérification connectivité port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                self.log("INFO", f"✓ {service_name} ({host}:{port}) disponible")
                return True
            else:
                message = f"❌ {service_name} ({host}:{port}) inaccessible"
                self.log("ERROR" if critical else "WARN", message)
                if critical:
                    self.critical_failures.append(message)
                else:
                    self.warnings.append(message)
                return False
                
        except Exception as e:
            message = f"❌ Erreur test {service_name}: {e}"
            self.log("ERROR" if critical else "WARN", message)
            if critical:
                self.critical_failures.append(message)
            else:
                self.warnings.append(message)
            return False
    
    def check_http_endpoint(self, url: str, service_name: str, timeout: int = 10) -> bool:
        """Vérification endpoint HTTP"""
        try:
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'HealthCheck/2.1.0')
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.getcode() == 200:
                    self.log("INFO", f"✓ {service_name} API disponible ({url})")
                    return True
                else:
                    message = f"❌ {service_name} retourne code {response.getcode()}"
                    self.log("ERROR", message)
                    self.critical_failures.append(message)
                    return False
                    
        except urllib.error.HTTPError as e:
            if e.code == 401:
                # 401 est acceptable pour endpoints protégés
                self.log("INFO", f"✓ {service_name} API protégée disponible ({url})")
                return True
            else:
                message = f"❌ {service_name} HTTP error {e.code}: {e.reason}"
                self.log("ERROR", message)
                self.critical_failures.append(message)
                return False
                
        except Exception as e:
            message = f"❌ Erreur connexion {service_name}: {e}"
            self.log("ERROR", message)
            self.critical_failures.append(message)
            return False
    
    def check_api_health(self) -> bool:
        """Vérification santé API FastAPI"""
        try:
            url = f"http://localhost:{self.api_port}/health"
            request = urllib.request.Request(url)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode())
                    status = data.get('status', 'unknown')
                    
                    if status == 'healthy':
                        self.log("INFO", "✓ API Digital Twin en bonne santé")
                        
                        # Vérification composants détaillés
                        components = data.get('components', {})
                        for comp_name, comp_status in components.items():
                            if comp_status == 'ok':
                                self.log("INFO", f"  ✓ {comp_name}: OK")
                            else:
                                self.log("WARN", f"  ⚠️ {comp_name}: {comp_status}")
                                self.warnings.append(f"Composant {comp_name} dégradé")
                        
                        return True
                    elif status == 'degraded':
                        self.log("WARN", "⚠️ API Digital Twin en mode dégradé")
                        self.warnings.append("API en mode dégradé")
                        return True  # Acceptable
                    else:
                        message = f"❌ API Digital Twin unhealthy: {status}"
                        self.log("ERROR", message)
                        self.critical_failures.append(message)
                        return False
                else:
                    message = f"❌ Health check API retourne {response.getcode()}"
                    self.log("ERROR", message)
                    self.critical_failures.append(message)
                    return False
                    
        except Exception as e:
            message = f"❌ Erreur health check API: {e}"
            self.log("ERROR", message)
            self.critical_failures.append(message)
            return False
    
    def check_file_system(self) -> bool:
        """Vérification système de fichiers"""
        checks_passed = True
        
        # Répertoires critiques
        critical_dirs = [
            '/app',
            '/app/logs',
            '/app/api'
        ]
        
        for directory in critical_dirs:
            if os.path.exists(directory) and os.access(directory, os.R_OK):
                self.log("INFO", f"✓ Répertoire {directory} accessible")
            else:
                message = f"❌ Répertoire {directory} inaccessible"
                self.log("ERROR", message)
                self.critical_failures.append(message)
                checks_passed = False
        
        # Vérification espace disque (simple)
        try:
            stat = os.statvfs('/app')
            free_space = stat.f_bavail * stat.f_frsize
            total_space = stat.f_blocks * stat.f_frsize
            used_percent = ((total_space - free_space) / total_space) * 100
            
            if used_percent > 90:
                message = f"⚠️ Espace disque critique: {used_percent:.1f}% utilisé"
                self.log("WARN", message)
                self.warnings.append(message)
            else:
                self.log("INFO", f"✓ Espace disque OK: {used_percent:.1f}% utilisé")
                
        except Exception as e:
            self.log("WARN", f"⚠️ Impossible de vérifier l'espace disque: {e}")
            self.warnings.append("Vérification espace disque impossible")
        
        return checks_passed
    
    def check_processes(self) -> bool:
        """Vérification processus critiques"""
        try:
            # Vérification via ps
            import subprocess
            
            # Processus attendus
            expected_processes = [
                'supervisord',
                'python3',  # API
                'Xvfb'      # Serveur X virtuel
            ]
            
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes_output = result.stdout
            
            for process_name in expected_processes:
                if process_name in processes_output:
                    self.log("INFO", f"✓ Processus {process_name} actif")
                else:
                    message = f"⚠️ Processus {process_name} introuvable"
                    self.log("WARN", message)
                    self.warnings.append(message)
            
            return True
            
        except Exception as e:
            self.log("WARN", f"⚠️ Impossible de vérifier les processus: {e}")
            self.warnings.append("Vérification processus impossible")
            return True  # Non critique
    
    def run_health_check(self) -> Tuple[bool, Dict]:
        """Exécution complète du health check"""
        self.log("INFO", "🔍 Démarrage health check Station Traffeyère Digital Twin")
        self.log("INFO", f"📋 RNCP 39394 - Version 2.1.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        
        # 1. Vérification système de fichiers
        self.log("INFO", "📁 Vérification système de fichiers...")
        fs_ok = self.check_file_system()
        
        # 2. Vérification processus
        self.log("INFO", "⚙️ Vérification processus...")
        processes_ok = self.check_processes()
        
        # 3. Vérification API principale
        self.log("INFO", "🌐 Vérification API Digital Twin...")
        api_ok = self.check_api_health()
        
        # 4. Vérification endpoints HTTP
        self.log("INFO", "📡 Vérification endpoints HTTP...")
        api_endpoint_ok = self.check_http_endpoint(
            f"http://localhost:{self.api_port}/docs",
            "API Documentation"
        )
        
        # 5. Vérification serveur web
        self.log("INFO", "🌍 Vérification serveur web...")
        web_ok = self.check_port('localhost', self.web_port, "Serveur Web", critical=False)
        
        # 6. Vérification services externes (non critique)
        self.log("INFO", "🔗 Vérification services externes...")
        mqtt_ok = self.check_port(self.mqtt_host, self.mqtt_port, "MQTT Broker", critical=False)
        redis_ok = self.check_port(self.redis_host, self.redis_port, "Redis Cache", critical=False)
        
        # Calcul résultat global
        critical_checks = [fs_ok, api_ok, api_endpoint_ok]
        all_critical_ok = all(critical_checks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Rapport final
        report = {
            'status': 'healthy' if all_critical_ok and not self.critical_failures else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'duration_ms': round(duration * 1000, 2),
            'version': '2.1.0',
            'rncp': '39394',
            'checks': {
                'filesystem': fs_ok,
                'processes': processes_ok,
                'api_health': api_ok,
                'api_endpoint': api_endpoint_ok,
                'web_server': web_ok,
                'mqtt_broker': mqtt_ok,
                'redis_cache': redis_ok
            },
            'critical_failures': self.critical_failures,
            'warnings': self.warnings
        }
        
        # Logging final
        if all_critical_ok and not self.critical_failures:
            self.log("INFO", f"✅ Health check PASSED - Durée: {duration:.2f}s")
        else:
            self.log("ERROR", f"❌ Health check FAILED - Durée: {duration:.2f}s")
            for failure in self.critical_failures:
                self.log("ERROR", f"  - {failure}")
        
        if self.warnings:
            self.log("WARN", f"⚠️ {len(self.warnings)} avertissements:")
            for warning in self.warnings:
                self.log("WARN", f"  - {warning}")
        
        return all_critical_ok and not self.critical_failures, report


def main():
    """Point d'entrée principal"""
    try:
        checker = HealthChecker()
        is_healthy, report = checker.run_health_check()
        
        # Sortie JSON pour monitoring externe (optionnel)
        if '--json' in sys.argv:
            print(json.dumps(report, indent=2))
        
        # Code de sortie pour Docker health check
        sys.exit(0 if is_healthy else 1)
        
    except Exception as e:
        print(f"❌ Erreur critique health check: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
