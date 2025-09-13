# Interface Conversationnelle XIA - Station Traffeyère

L'interface conversationnelle XIA (eXplainable Intelligent Assistant) est intégrée au dashboard principal de la Station Traffeyère pour offrir une expérience utilisateur conversationnelle complète avec les données IoT en temps réel.

## 🎯 Fonctionnalités Principales

### 🤖 **IA Conversationnelle Multi-Providers**
- **Google Gemini Pro**: Capacités multimodales et analyse avancée
- **Anthropic Claude 4 Sonnet**: Sécurité et raisonnement éthique
- **OpenAI GPT-4 Turbo**: Intégration plugins et génération de code
- **Perplexity AI**: Recherche temps réel avec citations

### 🎤 **Interface Vocale Complète**
- **Reconnaissance vocale** : Web Speech API avec support multi-langue
- **Synthèse vocale** : Text-to-Speech avec voix personnalisables
- **Commandes vocales** : Navigation et contrôle par commandes prédéfinies
- **Alertes automatiques** : Annonces vocales des anomalies critiques

### 🔗 **Intégration Temps Réel**
- **WebSocket**: Connexion temps réel avec reconnexion automatique
- **Données IoT**: Contexte enrichi avec 127 capteurs
- **Alertes contextuelles**: Réponses automatiques aux anomalies
- **Dashboard sync**: Synchronisation avec les données du dashboard

### 🎨 **Interface Adaptative**
- **États multiples**: Minimisé, normal, plein écran
- **Responsive design**: Adaptation mobile et desktop
- **Thèmes visuels**: Light, dark, et thème IoT personnalisé
- **Animations fluides**: Framer Motion pour les transitions

## 🏗️ Architecture

```
ConversationalInterface/
├── ConversationalInterfaceContainer.tsx    # Conteneur principal
├── ConversationalInterface.tsx             # Interface de chat
├── ConversationalSettings.tsx              # Panneau de paramètres
├── VoiceIndicator.tsx                      # Indicateurs vocaux animés
└── index.ts                               # Exports centralisés

hooks/
├── useConversationalAI.ts                 # Hook IA multi-providers
├── useVoiceRecognition.ts                 # Hook reconnaissance vocale
├── useSpeechSynthesis.ts                  # Hook synthèse vocale
└── useWebSocket.ts                        # Hook WebSocket temps réel

config/
└── conversationalConfig.ts               # Configuration centralisée

types/
└── conversation.types.ts                  # Types TypeScript
```

## 🚀 Integration dans le Dashboard

L'interface est intégrée dans le `MainDashboard` avec:

```typescript
<ConversationalInterfaceContainer
  sensorData={sensors || []}
  alerts={sensors?.filter(s => s.alertLevel !== 'normal') || []}
  anomalies={sensorStats?.anomalies || 0}
  isMinimized={conversationalMinimized}
  onMinimizedChange={setConversationalMinimized}
  position={conversationalPosition}
  onAction={handleConversationalAction}
  config={{
    websocket: {
      enabled: true,
      url: 'ws://backend:8000/ws/conversational',
      heartbeatInterval: 30000,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
    },
    iot: {
      contextualResponses: true,
      sensorDataIntegration: true,
      alertNotifications: true,
      realTimeUpdates: true,
    },
    ui: {
      theme: 'auto',
      animations: true,
      compactMode: false,
      maxHistoryItems: 50,
      autoSaveHistory: true,
    },
  }}
/>
```

## 🎮 Utilisation

### Interface Minimisée
- **Icône flottante** avec indicateur d'alertes
- **Clic** pour agrandir l'interface
- **Animations** d'état vocal en temps réel

### Interface Complète
- **Chat conversationnel** avec historique
- **Reconnaissance vocale** par bouton micro
- **Commandes texte et voix** intégrées
- **Paramètres** accessibles via l'icône engrenage

### Commandes Vocales Prédéfinies

#### Navigation
- "va au dashboard"
- "ouvre les capteurs"
- "montre les alertes"
- "ouvre digital twin"
- "va à XAI"

#### Contrôles
- "arrête la synthèse"
- "active le micro"
- "ferme le micro"
- "efface l'historique"

#### Données IoT
- "état des capteurs"
- "température actuelle"
- "dernières alertes"
- "résumé de la station"
- "anomalies détectées"

## 🔧 Configuration

### Providers IA
```typescript
const config = {
  aiProviders: {
    claude: {
      name: 'claude',
      displayName: 'Anthropic Claude 4 Sonnet',
      baseURL: 'https://api.anthropic.com/v1',
      model: 'claude-3-5-sonnet-20241022',
      maxTokens: 8192,
      temperature: 0.7,
    },
    // ... autres providers
  }
}
```

### Paramètres Vocaux
```typescript
const voiceConfig = {
  enabled: true,
  defaultLanguage: 'fr-FR',
  recognition: {
    continuous: true,
    interimResults: true,
    maxAlternatives: 3,
  },
  synthesis: {
    rate: 1.0,
    pitch: 1.0,
    volume: 0.8,
  },
}
```

## 🎨 Thèmes Visuels

### Thème IoT (par défaut)
```typescript
const iotTheme = {
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  messageUser: '#00bcd4',
  messageAI: '#4caf50',
  accent: '#ff5722',
  text: '#ffffff',
  border: '#37474f',
}
```

## 📊 Réponses Automatiques

L'assistant génère automatiquement des réponses contextuelles :

- **Température élevée** : Alerte et recommandations
- **Capteur hors ligne** : Notification de déconnexion
- **Anomalie détectée** : Analyse XAI disponible
- **Système sain** : Confirmation état normal
- **Batterie faible** : Recommandation maintenance

## 🔒 Sécurité et Conformité

- **Gestion des secrets** : Clés API protégées
- **Validation des entrées** : Sanitisation des données
- **Rate limiting** : Limitation des requêtes IA
- **Audit trail** : Logs des conversations
- **Conformité ISA/IEC 62443** : Standards industriels

## 🚀 Déploiement

L'interface est automatiquement disponible avec le dashboard principal. La configuration WebSocket doit pointer vers l'endpoint backend approprié :

```bash
# Production
REACT_APP_WS_URL=wss://traffeyere.station.ai/ws/conversational

# Développement
REACT_APP_WS_URL=ws://localhost:8080/ws/conversational
```

## 🎯 Performance

- **Latence IA** : < 2s (objectif < 500ms)
- **Reconnaissance vocale** : Temps réel
- **Synthèse vocale** : < 100ms délai
- **WebSocket** : < 50ms round-trip
- **Animations** : 60fps avec Framer Motion

## 🛠️ Développement

### Tests locaux
```bash
cd services/frontend
npm run dev
```

### Build production
```bash
npm run build
npm run preview
```

---

🎉 **L'interface conversationnelle XIA est maintenant intégrée au dashboard principal de la Station Traffeyère !**