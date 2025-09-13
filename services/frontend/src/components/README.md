# 🎯 Frontend React - Station Traffeyère IoT/AI Platform

## 📁 Structure des composants

```
src/
├── components/
│   ├── Dashboard/              # Dashboards principaux
│   │   ├── MainDashboard.tsx   # Vue d'ensemble 127 capteurs
│   │   ├── IoTSensorGrid.tsx   # Grille capteurs temps réel
│   │   ├── AlertsPanel.tsx     # Panneau alertes/anomalies
│   │   └── MetricsOverview.tsx # KPIs et métriques clés
│   │
│   ├── XAI/                    # IA Explicable (SHAP/LIME)
│   │   ├── ExplanationDashboard.tsx  # Dashboard explicabilité
│   │   ├── SHAPVisualizer.tsx         # Visualisations SHAP
│   │   ├── ConversationalAI.tsx       # Chatbot explicable
│   │   ├── UncertaintyQuantification.tsx # Quantification incertitude
│   │   └── ExplanationHistory.tsx     # Historique explications
│   │
│   ├── DigitalTwin/            # Jumeau Numérique Unity
│   │   ├── UnityWebGLViewer.tsx       # Viewer Unity WebGL
│   │   ├── TwinControlPanel.tsx       # Contrôles Digital Twin
│   │   ├── ARVRInterface.tsx          # Interface AR/VR
│   │   └── SimulationControls.tsx     # Contrôles simulation
│   │
│   ├── VoiceAssistant/         # Assistant Vocal XIA
│   │   ├── VoiceInterface.tsx         # Interface reconnaissance vocale
│   │   ├── SpeechSynthesis.tsx        # Synthèse vocale
│   │   ├── ConversationHistory.tsx    # Historique conversations
│   │   └── VoiceCommands.tsx          # Commandes vocales
│   │
│   ├── Monitoring/             # Monitoring & Observabilité
│   │   ├── SystemHealth.tsx           # Santé système
│   │   ├── PerformanceMetrics.tsx     # Métriques performance
│   │   ├── AlertsManager.tsx          # Gestionnaire alertes
│   │   └── LogsViewer.tsx             # Visualiseur logs
│   │
│   ├── Common/                 # Composants communs
│   │   ├── Layout.tsx                 # Layout principal
│   │   ├── Navigation.tsx             # Navigation responsive
│   │   ├── LoadingSpinner.tsx         # Indicateurs chargement
│   │   └── ErrorBoundary.tsx          # Gestion erreurs
│   │
│   └── Charts/                 # Graphiques & Visualisations
│       ├── RealTimeChart.tsx          # Graphiques temps réel
│       ├── SHAPChart.tsx              # Graphiques SHAP
│       ├── AnomalyVisualization.tsx   # Visualisation anomalies
│       └── PerformanceChart.tsx       # Graphiques performance
│
├── services/                   # Services API & WebSocket
│   ├── api.ts                         # Client API REST
│   ├── websocket.ts                   # WebSocket temps réel
│   ├── xaiService.ts                  # Service XAI
│   └── twinService.ts                 # Service Digital Twin
│
├── hooks/                      # Hooks React personnalisés
│   ├── useWebSocket.ts                # Hook WebSocket
│   ├── useXAIExplanations.ts          # Hook explications XAI
│   ├── useIoTData.ts                  # Hook données IoT
│   └── useVoiceRecognition.ts         # Hook reconnaissance vocale
│
├── store/                      # State Management (Zustand)
│   ├── iotStore.ts                    # Store données IoT
│   ├── xaiStore.ts                    # Store XAI
│   ├── twinStore.ts                   # Store Digital Twin
│   └── uiStore.ts                     # Store UI/UX
│
└── types/                      # Types TypeScript
    ├── iot.types.ts                   # Types IoT
    ├── xai.types.ts                   # Types XAI
    ├── twin.types.ts                  # Types Digital Twin
    └── api.types.ts                   # Types API
```

## 🚀 Fonctionnalités implémentées

### ✨ Dashboard IoT Temps Réel
- **127 capteurs IoT** visualisés en grille interactive
- **WebSocket** pour mise à jour temps réel (5s)
- **Alertes anomalies** avec notifications push
- **Graphiques Chart.js/D3.js** haute performance

### 🧠 Interface XAI Explicable
- **SHAP/LIME visualizations** interactives
- **Chatbot conversationnel** avec explications contextuelles
- **Quantification incertitude** avec métriques de confiance
- **Historique explications** avec recherche/filtrage

### 🏗️ Digital Twin Unity
- **Unity WebGL** intégré dans React
- **Contrôles 3D** pour navigation immersive
- **Synchronisation temps réel** avec données IoT
- **Interface AR/VR** pour HoloLens/Quest

### 🗣️ Assistant Vocal XIA
- **Reconnaissance vocale** Web Speech API
- **Synthèse vocale** multilingue (FR/EN)
- **Commandes vocales** contextuelles métier
- **Interface conversationnelle** adaptive

### 📊 Monitoring & Observabilité
- **Métriques système** temps réel
- **Alertes intelligentes** avec escalade
- **Logs centralisés** avec recherche
- **Performance Edge AI** < 0.28ms

## 🎨 UI/UX Design System

- **Material-UI v5** comme base design
- **Thèmes sombre/clair** adaptatifs
- **Responsive design** mobile-first
- **Accessibilité WCAG 2.1 AA**
- **Animations Framer Motion** fluides

## 🔧 Technologies Frontend

- **React 18** avec TypeScript strict
- **Vite** pour bundling optimisé
- **Zustand** pour state management
- **React Query** pour cache API
- **Socket.io** pour WebSocket
- **Chart.js + D3.js** pour visualisations
- **Three.js** pour intégrations 3D