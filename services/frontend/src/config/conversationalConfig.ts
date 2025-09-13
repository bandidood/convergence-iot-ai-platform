export interface AIProviderConfig {
  name: string;
  displayName: string;
  baseURL: string;
  model: string;
  maxTokens: number;
  temperature: number;
  supportedFeatures: string[];
  pricing: {
    inputTokens: number; // Prix par 1K tokens
    outputTokens: number;
  };
}

export interface VoiceConfig {
  enabled: boolean;
  defaultLanguage: string;
  recognition: {
    continuous: boolean;
    interimResults: boolean;
    maxAlternatives: number;
    grammars: string[];
  };
  synthesis: {
    rate: number;
    pitch: number;
    volume: number;
  };
}

export interface ConversationalConfig {
  aiProviders: Record<string, AIProviderConfig>;
  voice: VoiceConfig;
  ui: {
    theme: 'light' | 'dark' | 'auto';
    animations: boolean;
    compactMode: boolean;
    maxHistoryItems: number;
    autoSaveHistory: boolean;
  };
  websocket: {
    enabled: boolean;
    url: string;
    heartbeatInterval: number;
    reconnectInterval: number;
    maxReconnectAttempts: number;
  };
  iot: {
    contextualResponses: boolean;
    sensorDataIntegration: boolean;
    alertNotifications: boolean;
    realTimeUpdates: boolean;
  };
}

// Configuration par défaut
export const defaultConversationalConfig: ConversationalConfig = {
  aiProviders: {
    gemini: {
      name: 'gemini',
      displayName: 'Google Gemini Pro',
      baseURL: 'https://generativelanguage.googleapis.com/v1beta',
      model: 'gemini-1.5-pro-latest',
      maxTokens: 8192,
      temperature: 0.7,
      supportedFeatures: ['text', 'multimodal', 'code', 'reasoning'],
      pricing: {
        inputTokens: 0.0025,
        outputTokens: 0.0075,
      },
    },
    claude: {
      name: 'claude',
      displayName: 'Anthropic Claude 4 Sonnet',
      baseURL: 'https://api.anthropic.com/v1',
      model: 'claude-3-5-sonnet-20241022',
      maxTokens: 8192,
      temperature: 0.7,
      supportedFeatures: ['text', 'analysis', 'code', 'reasoning', 'safety'],
      pricing: {
        inputTokens: 0.003,
        outputTokens: 0.015,
      },
    },
    gpt4: {
      name: 'gpt4',
      displayName: 'OpenAI GPT-4 Turbo',
      baseURL: 'https://api.openai.com/v1',
      model: 'gpt-4-turbo-preview',
      maxTokens: 4096,
      temperature: 0.7,
      supportedFeatures: ['text', 'code', 'reasoning', 'plugins'],
      pricing: {
        inputTokens: 0.01,
        outputTokens: 0.03,
      },
    },
    perplexity: {
      name: 'perplexity',
      displayName: 'Perplexity Sonar Large',
      baseURL: 'https://api.perplexity.ai',
      model: 'llama-3.1-sonar-large-128k-online',
      maxTokens: 4096,
      temperature: 0.7,
      supportedFeatures: ['text', 'web-search', 'real-time', 'citations'],
      pricing: {
        inputTokens: 0.001,
        outputTokens: 0.001,
      },
    },
  },

  voice: {
    enabled: true,
    defaultLanguage: 'fr-FR',
    recognition: {
      continuous: true,
      interimResults: true,
      maxAlternatives: 3,
      grammars: [
        'arrête', 'stop', 'pause', 'reprend', 'continue',
        'capteurs', 'température', 'pression', 'humidité',
        'alerte', 'alarme', 'anomalie', 'problème',
        'dashboard', 'graphique', 'données', 'historique',
        'aide', 'assistant', 'XIA', 'IA explicable'
      ],
    },
    synthesis: {
      rate: 1.0,
      pitch: 1.0,
      volume: 0.8,
    },
  },

  ui: {
    theme: 'auto',
    animations: true,
    compactMode: false,
    maxHistoryItems: 50,
    autoSaveHistory: true,
  },

  websocket: {
    enabled: true,
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:8080/ws',
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
};

// Messages système contextuels pour chaque provider
export const systemPrompts = {
  base: `Tu es XIA (eXplainable Intelligent Assistant), l'assistant IA de la Station Traffeyère IoT/IA Platform.

**Contexte :**
- Station de surveillance environnementale avec 127 capteurs IoT
- Systèmes d'IA explicable (XAI) avec SHAP/LIME
- Digital Twin en temps réel avec Unity WebGL
- Plateforme de monitoring avancé avec alertes intelligentes

**Ton rôle :**
- Assistant conversationnel expert en IoT, IA explicable et monitoring
- Analyser les données de capteurs et alertes en temps réel
- Expliquer les décisions IA de manière claire et accessible
- Guider l'utilisateur dans l'interface et l'analyse des données

**Capacités spécifiques :**
- Synthèse vocale pour les alertes critiques
- Intégration avec les données capteurs en temps réel
- Explications SHAP/LIME des anomalies détectées
- Navigation contextuelle du Digital Twin
- Recommandations d'actions préventives

**Style de communication :**
- Professionnel mais accessible
- Réponses concises et orientées action
- Utilise des emojis IoT pertinents (🌡️ 💧 ⚡ 📊 🔄)
- Priorise la sécurité et la fiabilité`,

  gemini: `En plus des instructions de base, utilise tes capacités multimodales pour :
- Analyser les graphiques et visualisations de données
- Interpréter les schémas du Digital Twin
- Détecter les patterns visuels dans les dashboards`,

  claude: `En plus des instructions de base, privilégie :
- Analyses de sécurité et conformité (ISA/IEC 62443)
- Raisonnement éthique pour les décisions automatisées
- Explications détaillées des algorithmes XAI`,

  gpt4: `En plus des instructions de base, utilise :
- Intégration avec plugins pour données externes
- Génération de code pour automations personnalisées
- Analyses prédictives avancées`,

  perplexity: `En plus des instructions de base, fournis :
- Informations temps réel sur les conditions météo locales
- Recherches contextuelles sur les standards IoT
- Citations de sources pour les recommandations techniques`,
};

// Commandes vocales prédéfinies
export const voiceCommands = {
  navigation: {
    'va au dashboard': () => ({ action: 'navigate', path: '/dashboard' }),
    'ouvre les capteurs': () => ({ action: 'navigate', path: '/sensors' }),
    'montre les alertes': () => ({ action: 'navigate', path: '/alerts' }),
    'ouvre digital twin': () => ({ action: 'navigate', path: '/digital-twin' }),
    'va à XAI': () => ({ action: 'navigate', path: '/xai' }),
  },
  
  controls: {
    'arrête la synthèse': () => ({ action: 'stop-speech' }),
    'active le micro': () => ({ action: 'start-listening' }),
    'ferme le micro': () => ({ action: 'stop-listening' }),
    'change la langue': () => ({ action: 'toggle-language' }),
    'efface l\'historique': () => ({ action: 'clear-history' }),
  },

  data: {
    'état des capteurs': () => ({ action: 'sensor-status' }),
    'température actuelle': () => ({ action: 'get-temperature' }),
    'dernières alertes': () => ({ action: 'recent-alerts' }),
    'résumé de la station': () => ({ action: 'station-summary' }),
    'anomalies détectées': () => ({ action: 'detected-anomalies' }),
  },
};

// Réponses automatiques basées sur les données IoT
export const automaticResponses = {
  highTemperature: (temp: number) => 
    `🌡️ Température élevée détectée: ${temp}°C. Recommandation: vérifier la ventilation et surveiller l'évolution.`,
  
  sensorOffline: (sensorId: string, name: string) => 
    `⚠️ Capteur ${sensorId} (${name}) hors ligne. Vérification de connectivité recommandée.`,
  
  anomalyDetected: (sensor: string, confidence: number) => 
    `🚨 Anomalie détectée sur ${sensor} avec ${(confidence * 100).toFixed(1)}% de certitude. Analyse XAI disponible.`,
  
  systemHealthy: (activeSensors: number, total: number) => 
    `✅ Station fonctionnelle: ${activeSensors}/${total} capteurs actifs. Tous les systèmes opérationnels.`,
  
  batteryLow: (sensorId: string, level: number) => 
    `🔋 Batterie faible sur capteur ${sensorId}: ${level}%. Maintenance préventive recommandée.`,
};

// Thèmes visuels pour l'interface conversationnelle
export const conversationalThemes = {
  light: {
    background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
    messageUser: '#2196f3',
    messageAI: '#4caf50',
    accent: '#ff9800',
    text: '#333333',
    border: '#e0e0e0',
  },
  
  dark: {
    background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
    messageUser: '#64b5f6',
    messageAI: '#81c784',
    accent: '#ffb74d',
    text: '#ffffff',
    border: '#424242',
  },
  
  iot: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    messageUser: '#00bcd4',
    messageAI: '#4caf50',
    accent: '#ff5722',
    text: '#ffffff',
    border: '#37474f',
  },
};

// Configuration des animations
export const animationConfig = {
  messageEntry: {
    initial: { opacity: 0, y: 20, scale: 0.95 },
    animate: { opacity: 1, y: 0, scale: 1 },
    transition: { type: 'spring', stiffness: 100, damping: 20 },
  },
  
  voiceIndicator: {
    listening: {
      scale: [1, 1.2, 1],
      opacity: [0.7, 1, 0.7],
    },
    speaking: {
      rotate: [0, 360],
      scale: [1, 1.1, 1],
    },
  },
  
  typing: {
    dots: {
      y: [0, -10, 0],
      transition: {
        repeat: Infinity,
        duration: 1.2,
        ease: 'easeInOut',
      },
    },
  },
};

// Validation de la configuration
export const validateConfig = (config: Partial<ConversationalConfig>): boolean => {
  const required = ['aiProviders', 'voice', 'ui', 'websocket', 'iot'];
  return required.every(key => key in config);
};

// Fusion avec configuration personnalisée
export const mergeConfig = (
  base: ConversationalConfig, 
  custom: Partial<ConversationalConfig>
): ConversationalConfig => {
  return {
    ...base,
    ...custom,
    aiProviders: { ...base.aiProviders, ...custom.aiProviders },
    voice: { ...base.voice, ...custom.voice },
    ui: { ...base.ui, ...custom.ui },
    websocket: { ...base.websocket, ...custom.websocket },
    iot: { ...base.iot, ...custom.iot },
  };
};