#!/usr/bin/env python3
"""
📊 SOC DASHBOARD TEMPS RÉEL
Station Traffeyère IoT AI Platform - RNCP 39394 Semaine 6

Dashboard 24/7 pour analystes SOC avec alertes intelligentes
Interface web temps réel pour monitoring des menaces
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import asyncio
import uvicorn
from typing import List
import sqlite3
from datetime import datetime, timedelta
import logging
from pathlib import Path
# Import optionnel - SOC peut fonctionner de manière autonome
try:
    from intelligent_soc import IntelligentSOC, threat_hunting_automated
    SOC_AVAILABLE = True
except ImportError:
    SOC_AVAILABLE = False
    print("⚠️  Module SOC non disponible - Dashboard en mode autonome")

import threading
import time

# Configuration
logger = logging.getLogger('SOCDashboard')

class ConnectionManager:
    """Gestionnaire de connexions WebSocket"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Nouvelle connexion WebSocket: {len(self.active_connections)} total")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Connexion fermée: {len(self.active_connections)} restantes")
    
    async def broadcast(self, data: dict):
        """Diffuser des données à tous les clients connectés"""
        if self.active_connections:
            message = json.dumps(data)
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            # Nettoyer les connexions fermées
            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)

class SOCDashboardAPI:
    """API Dashboard SOC"""
    
    def __init__(self):
        self.app = FastAPI(title="SOC Dashboard - Station Traffeyère", version="1.0.0")
        self.connection_manager = ConnectionManager()
        self.soc = None
        self.soc_thread = None
        self._setup_routes()
        self._setup_static_files()
        
        # Données simulées pour démo
        self.threat_levels = {
            'LOW': 15,
            'MEDIUM': 8, 
            'HIGH': 3,
            'CRITICAL': 1
        }
        
        self.attack_types = {
            'malware': 12,
            'network_intrusion': 8,
            'data_exfiltration': 4,
            'ddos': 3
        }
        
    def _setup_static_files(self):
        """Configuration des fichiers statiques"""
        # Créer le répertoire static s'il n'existe pas
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        
        # Créer le fichier HTML du dashboard s'il n'existe pas
        if not (static_dir / "dashboard.html").exists():
            self._create_dashboard_html()
        
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    def _create_dashboard_html(self):
        """Créer le fichier HTML du dashboard"""
        html_content = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOC Dashboard - Station Traffeyère</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            overflow-x: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
            padding: 1rem 2rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .header .subtitle {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .dashboard-container {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 2rem;
            padding: 2rem;
            max-width: 1800px;
            margin: 0 auto;
        }
        
        .widget {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #333;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        
        .widget h3 {
            color: #60a5fa;
            margin-bottom: 1rem;
            font-size: 1.3rem;
            border-bottom: 2px solid #374151;
            padding-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            margin: 1rem 0;
        }
        
        .metric-value.success { color: #10b981; }
        .metric-value.warning { color: #f59e0b; }
        .metric-value.danger { color: #ef4444; }
        .metric-value.info { color: #3b82f6; }
        
        .metric-label {
            text-align: center;
            opacity: 0.8;
            font-size: 0.9rem;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online { background: #10b981; }
        .status-warning { background: #f59e0b; }
        .status-offline { background: #ef4444; }
        
        .incident-item {
            background: #252525;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-left: 4px solid;
        }
        
        .incident-high { border-left-color: #ef4444; }
        .incident-medium { border-left-color: #f59e0b; }
        .incident-low { border-left-color: #10b981; }
        
        .incident-time {
            font-size: 0.8rem;
            opacity: 0.7;
            float: right;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 1rem;
        }
        
        .full-width {
            grid-column: 1 / -1;
        }
        
        .connection-status {
            position: fixed;
            top: 1rem;
            right: 1rem;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.8rem;
            z-index: 1000;
        }
        
        .connected {
            background: #10b981;
            color: white;
        }
        
        .disconnected {
            background: #ef4444;
            color: white;
        }
        
        @media (max-width: 1200px) {
            .dashboard-container {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        @media (max-width: 768px) {
            .dashboard-container {
                grid-template-columns: 1fr;
                padding: 1rem;
            }
        }
        
        .blink {
            animation: blink 2s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">🔴 Connexion...</div>
    
    <div class="header">
        <h1>🔐 SOC INTELLIGENT - Station Traffeyère</h1>
        <div class="subtitle">Monitoring 24/7 • IA-Powered Threat Detection • RNCP 39394</div>
    </div>
    
    <div class="dashboard-container">
        <!-- Statut Global -->
        <div class="widget">
            <h3>🎯 Statut Global</h3>
            <div class="metric-value success" id="globalStatus">OPÉRATIONNEL</div>
            <div class="metric-label">
                <span class="status-indicator status-online"></span>
                Tous systèmes fonctionnels
            </div>
        </div>
        
        <!-- MTTR -->
        <div class="widget">
            <h3>⚡ MTTR Moyen</h3>
            <div class="metric-value info" id="mttr">0.24s</div>
            <div class="metric-label">Objectif < 11.3 minutes</div>
        </div>
        
        <!-- Menaces Détectées -->
        <div class="widget">
            <h3>🚨 Menaces Détectées</h3>
            <div class="metric-value warning" id="threatCount">0</div>
            <div class="metric-label">Dernières 24h</div>
        </div>
        
        <!-- Événements Traités -->
        <div class="widget">
            <h3>📊 Événements Traités</h3>
            <div class="metric-value info" id="eventsProcessed">0</div>
            <div class="metric-label">Total aujourd'hui</div>
        </div>
        
        <!-- Taux de Détection -->
        <div class="widget">
            <h3>🎯 Taux de Détection IA</h3>
            <div class="metric-value success" id="detectionRate">97.6%</div>
            <div class="metric-label">Précision du modèle ML</div>
        </div>
        
        <!-- Réponses Automatisées -->
        <div class="widget">
            <h3>🤖 Réponses Automatisées</h3>
            <div class="metric-value success" id="automatedResponses">0</div>
            <div class="metric-label">Incidents résolus automatiquement</div>
        </div>
        
        <!-- Incidents Récents -->
        <div class="widget full-width">
            <h3>🚨 Incidents Récents</h3>
            <div id="recentIncidents">
                <div class="incident-item incident-medium">
                    <div class="incident-time">Il y a 2 min</div>
                    <strong>Network Intrusion</strong><br>
                    IP suspecte détectée: 192.168.1.100 → Isolation automatique
                </div>
                <div class="incident-item incident-low">
                    <div class="incident-time">Il y a 15 min</div>
                    <strong>Anomalie ML</strong><br>
                    Pattern inhabituel détecté dans la zone IoT → Analyse en cours
                </div>
            </div>
        </div>
        
        <!-- Graphique des Menaces -->
        <div class="widget full-width">
            <h3>📈 Évolution des Menaces (24h)</h3>
            <div class="chart-container">
                <canvas id="threatChart"></canvas>
            </div>
        </div>
        
        <!-- Répartition par Type -->
        <div class="widget">
            <h3>🔍 Types de Menaces</h3>
            <div class="chart-container">
                <canvas id="threatTypeChart"></canvas>
            </div>
        </div>
        
        <!-- Threat Hunting -->
        <div class="widget">
            <h3>🎯 Threat Hunting</h3>
            <div class="metric-value warning" id="huntingPatterns">3</div>
            <div class="metric-label">Patterns suspects détectés</div>
        </div>
    </div>
    
    <script>
        // Configuration WebSocket
        let ws = null;
        let reconnectInterval = null;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                console.log('✅ WebSocket connecté');
                document.getElementById('connectionStatus').innerHTML = '🟢 Connecté';
                document.getElementById('connectionStatus').className = 'connection-status connected';
                
                if (reconnectInterval) {
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = function() {
                console.log('❌ WebSocket déconnecté');
                document.getElementById('connectionStatus').innerHTML = '🔴 Déconnecté';
                document.getElementById('connectionStatus').className = 'connection-status disconnected';
                
                // Reconnexion automatique
                if (!reconnectInterval) {
                    reconnectInterval = setInterval(connectWebSocket, 5000);
                }
            };
            
            ws.onerror = function(error) {
                console.error('Erreur WebSocket:', error);
            };
        }
        
        function updateDashboard(data) {
            // Mettre à jour les métriques
            if (data.metrics) {
                document.getElementById('mttr').textContent = 
                    (data.metrics.average_mttr_minutes * 60).toFixed(2) + 's';
                document.getElementById('threatCount').textContent = 
                    data.metrics.threats_detected || 0;
                document.getElementById('eventsProcessed').textContent = 
                    data.metrics.total_events_processed || 0;
                document.getElementById('automatedResponses').textContent = 
                    data.metrics.automated_responses || 0;
            }
            
            // Mettre à jour les incidents
            if (data.incidents) {
                updateIncidents(data.incidents);
            }
            
            // Mettre à jour threat hunting
            if (data.threat_hunting) {
                document.getElementById('huntingPatterns').textContent = 
                    data.threat_hunting.patterns_found || 0;
            }
        }
        
        function updateIncidents(incidents) {
            const container = document.getElementById('recentIncidents');
            container.innerHTML = '';
            
            incidents.forEach(incident => {
                const div = document.createElement('div');
                const severity = getSeverity(incident.threat_event?.severity || 'LOW');
                div.className = `incident-item incident-${severity}`;
                
                const timeAgo = getTimeAgo(incident.timestamp);
                div.innerHTML = `
                    <div class="incident-time">${timeAgo}</div>
                    <strong>${incident.playbook || 'Incident'}</strong><br>
                    ${incident.threat_event?.description || 'Incident détecté'} → 
                    ${incident.status === 'resolved' ? 'Résolu automatiquement' : 'En cours'}
                `;
                
                container.appendChild(div);
            });
        }
        
        function getSeverity(severity) {
            switch(severity.toUpperCase()) {
                case 'HIGH': 
                case 'CRITICAL': return 'high';
                case 'MEDIUM': return 'medium';
                default: return 'low';
            }
        }
        
        function getTimeAgo(timestamp) {
            const now = new Date();
            const time = new Date(timestamp);
            const diff = now - time;
            const minutes = Math.floor(diff / 60000);
            
            if (minutes < 1) return 'À l\\'instant';
            if (minutes < 60) return `Il y a ${minutes} min`;
            const hours = Math.floor(minutes / 60);
            if (hours < 24) return `Il y a ${hours}h`;
            return `Il y a ${Math.floor(hours / 24)} jour(s)`;
        }
        
        // Graphiques
        function initCharts() {
            // Graphique temporel des menaces
            const threatCtx = document.getElementById('threatChart').getContext('2d');
            window.threatChart = new Chart(threatCtx, {
                type: 'line',
                data: {
                    labels: Array.from({length: 24}, (_, i) => `${23-i}h`),
                    datasets: [{
                        label: 'Menaces Détectées',
                        data: [2,1,0,3,1,0,0,5,2,1,0,0,1,3,2,4,1,0,2,1,0,1,2,3],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#ffffff' }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#ffffff' },
                            grid: { color: '#374151' }
                        },
                        y: {
                            ticks: { color: '#ffffff' },
                            grid: { color: '#374151' }
                        }
                    }
                }
            });
            
            // Graphique en secteurs des types de menaces  
            const typeCtx = document.getElementById('threatTypeChart').getContext('2d');
            window.threatTypeChart = new Chart(typeCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Malware', 'Intrusion', 'Exfiltration', 'DDoS'],
                    datasets: [{
                        data: [40, 30, 20, 10],
                        backgroundColor: [
                            '#ef4444',
                            '#f59e0b', 
                            '#3b82f6',
                            '#10b981'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { 
                                color: '#ffffff',
                                padding: 15
                            }
                        }
                    }
                }
            });
        }
        
        // Initialisation
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            initCharts();
            
            // Simulation de données en temps réel
            setInterval(() => {
                // Clignotement aléatoire des nouvelles alertes
                if (Math.random() > 0.7) {
                    document.getElementById('threatCount').classList.add('blink');
                    setTimeout(() => {
                        document.getElementById('threatCount').classList.remove('blink');
                    }, 3000);
                }
            }, 10000);
        });
    </script>
</body>
</html>
        """
        
        with open("static/dashboard.html", "w", encoding="utf-8") as f:
            f.write(html_content)
    
    def _setup_routes(self):
        """Configuration des routes API"""
        
        @self.app.get("/")
        async def dashboard():
            """Page d'accueil du dashboard"""
            with open("static/dashboard.html", "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Endpoint WebSocket pour données temps réel"""
            await self.connection_manager.connect(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """API pour récupérer les métriques SOC"""
            if self.soc:
                metrics = self.soc.get_metrics()
                incidents = self.soc.get_recent_incidents(5)
                hunting_results = threat_hunting_automated(self.soc)
                
                return {
                    "metrics": metrics,
                    "incidents": incidents,
                    "threat_hunting": hunting_results,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "metrics": {
                        "total_events_processed": 0,
                        "threats_detected": 0,
                        "average_mttr_minutes": 0.0,
                        "automated_responses": 0
                    },
                    "incidents": [],
                    "threat_hunting": {"patterns_found": 0},
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.get("/api/health")
        async def health_check():
            """Check de santé du service"""
            return {
                "status": "healthy",
                "soc_running": self.soc is not None and self.soc.is_running,
                "connections": len(self.connection_manager.active_connections),
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_background_tasks(self):
        """Démarrer les tâches en arrière-plan"""
        
        # Démarrer le SOC dans un thread séparé (si disponible)
        def run_soc():
            if SOC_AVAILABLE:
                self.soc = IntelligentSOC()
            else:
                self.soc = None
                logger.info("SOC non disponible - dashboard en mode démo")
                return
            
            # Simuler quelques événements de test
            test_events = [
                {
                    'source_ip': '192.168.1.100',
                    'destination_ip': '10.3.0.10', 
                    'event_type': 'network_connection',
                    'description': 'Suspicious outbound connection from known malicious IP'
                },
                {
                    'source_ip': '10.2.0.25',
                    'destination_ip': '8.8.8.8',
                    'event_type': 'dns_query',
                    'description': 'Unusual DNS query pattern detected'
                }
            ]
            
            async def soc_main():
                # Démarrer le SOC
                soc_task = asyncio.create_task(self.soc.start())
                
                # Attendre l'initialisation
                await asyncio.sleep(3)
                
                # Ingérer des événements périodiquement
                while self.soc.is_running:
                    for event in test_events:
                        self.soc.ingest_event(event)
                        await asyncio.sleep(30)  # Nouvel événement toutes les 30s
            
            try:
                asyncio.run(soc_main())
            except Exception as e:
                logger.error(f"Erreur dans le SOC: {e}")
        
        # Lancer le SOC dans un thread
        self.soc_thread = threading.Thread(target=run_soc, daemon=True)
        self.soc_thread.start()
        
        # Attendre que le SOC soit prêt
        await asyncio.sleep(5)
        
        # Tâche de diffusion des données
        asyncio.create_task(self._broadcast_data())
    
    async def _broadcast_data(self):
        """Diffuser les données en temps réel aux clients WebSocket"""
        while True:
            try:
                if self.soc and len(self.connection_manager.active_connections) > 0:
                    # Récupérer les données du SOC
                    metrics = self.soc.get_metrics()
                    incidents = self.soc.get_recent_incidents(10)
                    hunting_results = threat_hunting_automated(self.soc)
                    
                    data = {
                        "type": "update",
                        "metrics": metrics,
                        "incidents": incidents,
                        "threat_hunting": hunting_results,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await self.connection_manager.broadcast(data)
                
                await asyncio.sleep(5)  # Mise à jour toutes les 5 secondes
                
            except Exception as e:
                logger.error(f"Erreur diffusion données: {e}")
                await asyncio.sleep(10)

async def main():
    """Fonction principale pour lancer le dashboard"""
    
    # Créer le répertoire static
    Path("static").mkdir(exist_ok=True)
    
    # Initialiser le dashboard
    dashboard = SOCDashboardAPI()
    
    # Démarrer les tâches en arrière-plan
    await dashboard.start_background_tasks()
    
    # Lancer le serveur
    print("🚀 Démarrage SOC Dashboard...")
    print("📊 Interface web: http://localhost:8094")
    print("🔗 API Health: http://localhost:8094/api/health") 
    print("📡 API Metrics: http://localhost:8094/api/metrics")
    print("⏹️  Ctrl+C pour arrêter")
    
    config = uvicorn.Config(
        dashboard.app,
        host="0.0.0.0",
        port=8094,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
